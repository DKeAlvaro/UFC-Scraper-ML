from abc import ABC, abstractmethod
import sys
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import BernoulliNB
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Use absolute imports to avoid relative import issues
try:
    from src.analysis.elo import process_fights_for_elo, INITIAL_ELO
    from src.config import FIGHTERS_CSV_PATH
    from src.predict.preprocess import preprocess_for_ml, _get_fighter_history_stats, _calculate_age
except ImportError:
    # Fallback for when running directly
    from ..analysis.elo import process_fights_for_elo, INITIAL_ELO
    from ..config import FIGHTERS_CSV_PATH
    from .preprocess import preprocess_for_ml, _get_fighter_history_stats, _calculate_age

class BaseModel(ABC):
    """
    Abstract base class for all prediction models.
    Ensures that every model has a standard interface for training and prediction.
    """
    @abstractmethod
    def train(self, train_fights):
        """
        Trains or prepares the model using historical fight data.

        :param train_fights: A list of historical fight data dictionaries.
        """
        pass

    @abstractmethod
    def predict(self, fight):
        """
        Predicts the winner of a single fight.

        :param fight: A dictionary representing a single fight.
        :return: The name of the predicted winning fighter.
        """
        pass

class EloBaselineModel(BaseModel):
    """
    A baseline prediction model that predicts the winner based on the higher ELO rating.
    """
    def __init__(self):
        self.fighters_df = None

    def train(self, train_fights):
        """
        For the ELO baseline, 'training' simply consists of loading the fighter data
        to access their ELO scores during prediction.
        """
        print("Training EloBaselineModel: Loading fighter ELO data...")
        self.fighters_df = pd.read_csv(FIGHTERS_CSV_PATH)
        self.fighters_df['full_name'] = self.fighters_df['first_name'] + ' ' + self.fighters_df['last_name']
        self.fighters_df = self.fighters_df.drop_duplicates(subset=['full_name']).set_index('full_name')

    def predict(self, fight):
        """Predicts the winner based on ELO and calculates win probability."""
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        
        try:
            f1_elo = self.fighters_df.loc[f1_name, 'elo']
            f2_elo = self.fighters_df.loc[f2_name, 'elo']
            
            # Calculate win probability for fighter 1 using the ELO formula
            prob_f1_wins = 1 / (1 + 10**((f2_elo - f1_elo) / 400))

            if prob_f1_wins >= 0.5:
                return {'winner': f1_name, 'probability': prob_f1_wins}
            else:
                return {'winner': f2_name, 'probability': 1 - prob_f1_wins}

        except KeyError as e:
            print(f"Warning: Could not find ELO for fighter {e}. Skipping prediction.")
            return {'winner': None, 'probability': None}

class BaseMLModel(BaseModel):
    """
    An abstract base class for machine learning models that handles all common
    data preparation, training, and prediction logic.
    """
    def __init__(self, model):
        if model is None:
            raise ValueError("A model must be provided.")
        self.model = model
        self.fighters_df = None
        self.fighter_histories = {}

    def train(self, train_fights):
        """
        Trains the machine learning model. This involves loading fighter data,
        pre-calculating histories, and fitting the model on the preprocessed data.
        """
        print(f"--- Training {self.model.__class__.__name__} ---")
        
        # 1. Prepare data for prediction-time feature generation
        self.fighters_df = pd.read_csv(FIGHTERS_CSV_PATH)
        self.fighters_df['full_name'] = self.fighters_df['first_name'] + ' ' + self.fighters_df['last_name']
        self.fighters_df = self.fighters_df.drop_duplicates(subset=['full_name']).set_index('full_name')
        for col in ['height_cm', 'reach_in', 'elo']:
            if col in self.fighters_df.columns:
                self.fighters_df[col] = pd.to_numeric(self.fighters_df[col], errors='coerce')

        # 2. Pre-calculate fighter histories
        train_fights_with_dates = []
        for fight in train_fights:
            fight['date_obj'] = pd.to_datetime(fight['event_date'])
            train_fights_with_dates.append(fight)
        for fighter_name in self.fighters_df.index:
            history = [f for f in train_fights_with_dates if fighter_name in (f['fighter_1'], f['fighter_2'])]
            self.fighter_histories[fighter_name] = sorted(history, key=lambda x: x['date_obj'])

        # 3. Preprocess and fit
        X_train, y_train, _ = preprocess_for_ml(train_fights, FIGHTERS_CSV_PATH)
        print(f"Fitting model on {X_train.shape[0]} samples...")
        self.model.fit(X_train, y_train)
        print("Model training complete.")

    def predict(self, fight):
        """
        Predicts the outcome of a single fight, returning the winner and probability.
        """
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        fight_date = pd.to_datetime(fight['event_date'])

        if f1_name not in self.fighters_df.index or f2_name not in self.fighters_df.index:
            print(f"Warning: Fighter not found. Skipping prediction for {f1_name} vs {f2_name}")
            return {'winner': None, 'probability': None}

        f1_stats = self.fighters_df.loc[f1_name]
        f2_stats = self.fighters_df.loc[f2_name]
        if isinstance(f1_stats, pd.DataFrame): f1_stats = f1_stats.iloc[0]
        if isinstance(f2_stats, pd.DataFrame): f2_stats = f2_stats.iloc[0]
        
        f1_hist = self.fighter_histories.get(f1_name, [])
        f2_hist = self.fighter_histories.get(f2_name, [])
        f1_hist_stats = _get_fighter_history_stats(f1_name, fight_date, f1_hist, self.fighters_df)
        f2_hist_stats = _get_fighter_history_stats(f2_name, fight_date, f2_hist, self.fighters_df)
        
        f1_age = _calculate_age(f1_stats.get('dob'), fight['event_date'])
        f2_age = _calculate_age(f2_stats.get('dob'), fight['event_date'])

        features = {
            'elo_diff': f1_stats.get('elo', 1500) - f2_stats.get('elo', 1500),
            'height_diff_cm': f1_stats.get('height_cm', 0) - f2_stats.get('height_cm', 0),
            'reach_diff_in': f1_stats.get('reach_in', 0) - f2_stats.get('reach_in', 0),
            'age_diff_years': (f1_age - f2_age) if f1_age and f2_age else 0,
            'stance_is_different': 1 if f1_stats.get('stance') != f2_stats.get('stance') else 0,
            'wins_last_5_diff': f1_hist_stats['wins_last_n'] - f2_hist_stats['wins_last_n'],
            'avg_opp_elo_last_5_diff': f1_hist_stats['avg_opp_elo_last_n'] - f2_hist_stats['avg_opp_elo_last_n'],
            'ko_percent_last_5_diff': f1_hist_stats['ko_percent_last_n'] - f2_hist_stats['ko_percent_last_n'],
            'sig_str_landed_per_min_last_5_diff': f1_hist_stats['sig_str_landed_per_min_last_n'] - f2_hist_stats['sig_str_landed_per_min_last_n'],
            'takedown_accuracy_last_5_diff': f1_hist_stats['takedown_accuracy_last_n'] - f2_hist_stats['takedown_accuracy_last_n'],
            'sub_attempts_per_min_last_5_diff': f1_hist_stats['sub_attempts_per_min_last_n'] - f2_hist_stats['sub_attempts_per_min_last_n'],
        }
        
        feature_vector = pd.DataFrame([features]).fillna(0)
        
        # Use predict_proba to get probabilities for each class
        probabilities = self.model.predict_proba(feature_vector)[0]
        prob_f1_wins = probabilities[1]  # Probability of class '1' (fighter 1 wins)

        if prob_f1_wins >= 0.5:
            return {'winner': f1_name, 'probability': prob_f1_wins}
        else:
            return {'winner': f2_name, 'probability': 1 - prob_f1_wins}

class LogisticRegressionModel(BaseMLModel):
    """A thin wrapper for scikit-learn's LogisticRegression."""
    def __init__(self):
        super().__init__(model=LogisticRegression())

class XGBoostModel(BaseMLModel):
    """A thin wrapper for XGBoost's XGBClassifier."""
    def __init__(self):
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
        super().__init__(model=model)

class SVCModel(BaseMLModel):
    """A thin wrapper for scikit-learn's Support Vector Classifier."""
    def __init__(self):
        # Probability=True is needed for some reports, though it slows down training
        super().__init__(model=SVC(probability=True, random_state=42))

class RandomForestModel(BaseMLModel):
    """A thin wrapper for scikit-learn's RandomForestClassifier."""
    def __init__(self):
        super().__init__(model=RandomForestClassifier(random_state=42))

class BernoulliNBModel(BaseMLModel):
    """A thin wrapper for scikit-learn's Bernoulli Naive Bayes classifier."""
    def __init__(self):
        super().__init__(model=BernoulliNB())

class LGBMModel(BaseMLModel):
    """A thin wrapper for LightGBM's LGBMClassifier."""
    def __init__(self):
        super().__init__(model=LGBMClassifier(random_state=42)) 