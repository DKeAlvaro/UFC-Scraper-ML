from abc import ABC, abstractmethod
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import BernoulliNB
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from ..analysis.elo import process_fights_for_elo, INITIAL_ELO
from ..config import FIGHTERS_CSV_PATH
from .preprocess import preprocess_for_ml

class BaseModel(ABC):
    """Abstract base class for all prediction models."""
    
    def __init__(self):
        self.model_name = self.__class__.__name__
        
    @abstractmethod
    def train(self, train_fights):
        """Train the model using historical fight data."""
        pass

    @abstractmethod
    def predict(self, fight):
        """Predict the winner of a single fight."""
        pass

    def _format_prediction(self, winner, probability):
        """Format prediction results consistently."""
        return {'winner': winner, 'probability': probability}

class EloBaselineModel(BaseModel):
    """Simple ELO-based prediction model."""
    
    def train(self, train_fights):
        """Process historical fights to calculate current ELO ratings."""
        print(f"--- Training {self.model_name} ---")
        
        # Load and prepare fighter data
        self.fighters_df = pd.read_csv(FIGHTERS_CSV_PATH)
        self.fighters_df['full_name'] = self.fighters_df['first_name'] + ' ' + self.fighters_df['last_name']
        self.fighters_df = self.fighters_df.drop_duplicates(subset=['full_name']).set_index('full_name')
        
        # Calculate ELO ratings
        elo_ratings = process_fights_for_elo(train_fights)
        self.fighters_df['elo'] = pd.Series(elo_ratings)
        self.fighters_df['elo'] = self.fighters_df['elo'].fillna(INITIAL_ELO)
        
        print("ELO ratings calculated for all fighters.")

    def predict(self, fight):
        """Predict winner based on current ELO ratings."""
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        
        try:
            f1_elo = self.fighters_df.loc[f1_name, 'elo']
            f2_elo = self.fighters_df.loc[f2_name, 'elo']
            
            # Calculate win probability using ELO formula
            prob_f1_wins = 1 / (1 + 10**((f2_elo - f1_elo) / 400))
            
            winner = f1_name if prob_f1_wins >= 0.5 else f2_name
            probability = prob_f1_wins if prob_f1_wins >= 0.5 else 1 - prob_f1_wins
            
            return self._format_prediction(winner, probability)
            
        except KeyError as e:
            print(f"Warning: Could not find ELO for fighter {e}. Skipping prediction.")
            return self._format_prediction(None, None)

class BaseMLModel(BaseModel):
    """Base class for all machine learning models."""
    
    def __init__(self, model):
        super().__init__()
        if model is None:
            raise ValueError("A model must be provided.")
        self.model = model

    def train(self, train_fights):
        """Train the ML model on preprocessed fight data."""
        print(f"--- Training {self.model_name} ---")
        
        # Preprocess data and fit model
        X_train, y_train, _ = preprocess_for_ml(train_fights, FIGHTERS_CSV_PATH)
        print(f"Fitting model on {X_train.shape[0]} samples...")
        self.model.fit(X_train, y_train)
        print("Model training complete.")

    def predict(self, fight):
        """Predict fight outcome using the trained ML model."""
        # Preprocess single fight for prediction
        X_pred, _, metadata = preprocess_for_ml([fight], FIGHTERS_CSV_PATH)
        
        if X_pred.empty:
            print(f"Warning: Could not process fight data for {fight['fighter_1']} vs {fight['fighter_2']}")
            return self._format_prediction(None, None)
        
        # Make prediction
        try:
            prob_f1_wins = self.model.predict_proba(X_pred)[0][1]
            winner = fight['fighter_1'] if prob_f1_wins >= 0.5 else fight['fighter_2']
            probability = prob_f1_wins if prob_f1_wins >= 0.5 else 1 - prob_f1_wins
            
            return self._format_prediction(winner, probability)
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return self._format_prediction(None, None)

# Concrete ML model implementations
class LogisticRegressionModel(BaseMLModel):
    def __init__(self):
        super().__init__(LogisticRegression(random_state=42))

class SVCModel(BaseMLModel):
    def __init__(self):
        super().__init__(SVC(probability=True, random_state=42))

class RandomForestModel(BaseMLModel):
    def __init__(self):
        super().__init__(RandomForestClassifier(n_estimators=100, random_state=42))

class BernoulliNBModel(BaseMLModel):
    def __init__(self):
        super().__init__(BernoulliNB())

class XGBoostModel(BaseMLModel):
    def __init__(self):
        super().__init__(XGBClassifier(random_state=42))

class LGBMModel(BaseMLModel):
    def __init__(self):
        super().__init__(LGBMClassifier(random_state=42))