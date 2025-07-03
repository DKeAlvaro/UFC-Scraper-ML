from abc import ABC, abstractmethod
import sys
import os
from ..analysis.elo import process_fights_for_elo, INITIAL_ELO
import pandas as pd
from sklearn.linear_model import LogisticRegression
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
        """Predicts the winner based on who has the higher ELO score."""
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        
        try:
            f1_elo = self.fighters_df.loc[f1_name, 'elo']
            f2_elo = self.fighters_df.loc[f2_name, 'elo']
            
            return f1_name if f1_elo > f2_elo else f2_name
        except KeyError as e:
            # If a fighter isn't found, we can't make a prediction.
            # Returning None or a default is a design choice.
            print(f"Warning: Could not find ELO for fighter {e}. Skipping prediction.")
            return None

class LogisticRegressionModel(BaseModel):
    """
    A model that uses logistic regression to predict fight outcomes based on differential features.
    """
    def __init__(self):
        self.model = LogisticRegression(solver='liblinear', random_state=42)
        self.fighters_df = None
        self.fighter_histories = {}

    def train(self, train_fights):
        """
        Trains the logistic regression model by preprocessing the training data
        and fitting the model.
        """
        print("Training LogisticRegressionModel...")
        
        # 1. Prepare data for prediction-time feature generation
        self.fighters_df = pd.read_csv(FIGHTERS_CSV_PATH)
        self.fighters_df['full_name'] = self.fighters_df['first_name'] + ' ' + self.fighters_df['last_name']
        self.fighters_df = self.fighters_df.drop_duplicates(subset=['full_name']).set_index('full_name')
        for col in ['height_cm', 'reach_in', 'elo']:
            if col in self.fighters_df.columns:
                self.fighters_df[col] = pd.to_numeric(self.fighters_df[col], errors='coerce')

        # 2. Pre-calculate fighter histories for efficient lookup during prediction
        train_fights_with_dates = []
        for fight in train_fights:
            fight['date_obj'] = pd.to_datetime(fight['event_date'])
            train_fights_with_dates.append(fight)
            
        for fighter_name in self.fighters_df.index:
            history = [f for f in train_fights_with_dates if fighter_name in (f['fighter_1'], f['fighter_2'])]
            self.fighter_histories[fighter_name] = sorted(history, key=lambda x: x['date_obj'])

        # 3. Preprocess training data and fit the model
        X_train, y_train, _ = preprocess_for_ml(train_fights, FIGHTERS_CSV_PATH)
        print(f"Fitting model on {X_train.shape[0]} samples...")
        self.model.fit(X_train, y_train)
        print("Model training complete.")

    def predict(self, fight):
        """
        Predicts the outcome of a single fight by generating its feature vector.
        """
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        fight_date = pd.to_datetime(fight['event_date'])

        if f1_name not in self.fighters_df.index or f2_name not in self.fighters_df.index:
            print(f"Warning: Fighter not found in data. Skipping prediction for {f1_name} vs {f2_name}")
            return None

        # 1. Get base stats
        f1_stats, f2_stats = self.fighters_df.loc[f1_name], self.fighters_df.loc[f2_name]
        if isinstance(f1_stats, pd.DataFrame): f1_stats = f1_stats.iloc[0]
        if isinstance(f2_stats, pd.DataFrame): f2_stats = f2_stats.iloc[0]
        
        # 2. Get historical stats
        f1_hist_stats = _get_fighter_history_stats(f1_name, fight_date, self.fighter_histories.get(f1_name, []), self.fighters_df)
        f2_hist_stats = _get_fighter_history_stats(f2_name, fight_date, self.fighter_histories.get(f2_name, []), self.fighters_df)
        
        # 3. Create differential features
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
        }
        
        feature_vector = pd.DataFrame([features]).fillna(0)
        
        # 4. Predict
        # The model predicts the probability of class '1' (a win for fighter_1)
        prediction = self.model.predict(feature_vector)[0]
        
        return f1_name if prediction == 1 else f2_name 