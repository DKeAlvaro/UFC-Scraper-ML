from abc import ABC, abstractmethod
import sys
import os
from ..analysis.elo import process_fights_for_elo, INITIAL_ELO

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
    def predict(self, fighter1_name, fighter2_name):
        """
        Predicts the winner of a single fight.

        :param fighter1_name: The name of the first fighter.
        :param fighter2_name: The name of the second fighter.
        :return: The name of the predicted winning fighter.
        """
        pass

class EloBaselineModel(BaseModel):
    """
    A baseline prediction model that predicts the winner based on the higher ELO rating.
    """
    def __init__(self):
        self.historical_elos = {}

    def train(self, train_fights):
        """
        Calculates the ELO ratings for all fighters based on historical data.
        These ratings are then stored to be used for predictions.
        """
        print("Training ELO Baseline Model...")
        self.historical_elos = process_fights_for_elo(train_fights)
        print("ELO Model training complete.")

    def predict(self, fighter1_name, fighter2_name):
        """
        Predicts the winner based on which fighter has the higher historical ELO.
        If a fighter has no ELO rating, the default initial ELO is used.
        """
        elo1 = self.historical_elos.get(fighter1_name, INITIAL_ELO)
        elo2 = self.historical_elos.get(fighter2_name, INITIAL_ELO)
        
        # Return the name of the fighter with the higher ELO
        return fighter1_name if elo1 > elo2 else fighter2_name 