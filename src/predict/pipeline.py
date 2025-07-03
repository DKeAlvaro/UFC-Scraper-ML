import csv
import os
import sys
from datetime import datetime
from collections import OrderedDict
from ..scrape.config import FIGHTS_CSV_PATH
from .models import BaseModel

class PredictionPipeline:
    """
    Orchestrates the model training, evaluation, and reporting pipeline.
    """
    def __init__(self, models):
        if not all(isinstance(m, BaseModel) for m in models):
            raise TypeError("All models must be instances of BaseModel.")
        self.models = models
        self.train_fights = []
        self.test_fights = []
        self.results = {}

    def _load_and_split_data(self, num_test_events=10):
        """Loads and splits the data into chronological training and testing sets."""
        print("\n--- Loading and Splitting Data ---")
        if not os.path.exists(FIGHTS_CSV_PATH):
            raise FileNotFoundError(f"Fights data not found at '{FIGHTS_CSV_PATH}'.")

        with open(FIGHTS_CSV_PATH, 'r', encoding='utf-8') as f:
            fights = list(csv.DictReader(f))
        
        fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
        
        all_events = list(OrderedDict.fromkeys(f['event_name'] for f in fights))
        if len(all_events) < num_test_events:
            print(f"Warning: Fewer than {num_test_events} events found. Adjusting test set size.")
            num_test_events = len(all_events)
            
        test_event_names = all_events[-num_test_events:]
        self.train_fights = [f for f in fights if f['event_name'] not in test_event_names]
        self.test_fights = [f for f in fights if f['event_name'] in test_event_names]
        print(f"Data loaded. {len(self.train_fights)} training fights, {len(self.test_fights)} testing fights.")
        print(f"Testing on the last {num_test_events} events.")

    def run(self, detailed_report=True):
        """Executes the full pipeline: load, train, evaluate, and report."""
        self._load_and_split_data()
        
        eval_fights = [f for f in self.test_fights if f['winner'] not in ["Draw", "NC", ""]]
        if not eval_fights:
            print("No fights with definitive outcomes in the test set. Aborting.")
            return

        for model in self.models:
            model_name = model.__class__.__name__
            print(f"\n--- Evaluating Model: {model_name} ---")
            
            model.train(self.train_fights)
            
            correct_predictions = 0
            predictions = []
            
            for fight in eval_fights:
                f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
                actual_winner = fight['winner']
                predicted_winner = model.predict(f1_name, f2_name)
                
                is_correct = (predicted_winner == actual_winner)
                if is_correct:
                    correct_predictions += 1
                
                predictions.append({
                    'fight': f"{f1_name} vs. {f2_name}",
                    'predicted_winner': predicted_winner,
                    'actual_winner': actual_winner,
                    'is_correct': is_correct
                })
                
            accuracy = (correct_predictions / len(eval_fights)) * 100
            self.results[model_name] = {
                'accuracy': accuracy, 
                'predictions': predictions,
                'total_fights': len(eval_fights)
            }

        if detailed_report:
            self._report_detailed_results()
        else:
            self._report_summary()

    def _report_summary(self):
        """Prints a concise summary of model performance."""
        print("\n\n--- Prediction Pipeline Summary ---")
        print(f"{'Model':<25} | {'Accuracy':<10} | {'Fights Evaluated':<20}")
        print("-" * 65)
        for model_name, result in self.results.items():
            print(f"{model_name:<25} | {result['accuracy']:<9.2f}% | {result['total_fights']:<20}")
        print("-" * 65)

    def _report_detailed_results(self):
        """Prints a summary and detailed report of the model evaluations."""
        print("\n\n--- Prediction Pipeline Finished: Detailed Report ---")
        for model_name, result in self.results.items():
            print(f"\n--- Model: {model_name} ---")
            print(f"  Overall Accuracy: {result['accuracy']:.2f}%")
            print("  Detailed Predictions:")
            for p in result['predictions']:
                status = "CORRECT" if p['is_correct'] else "INCORRECT"
                print(f"    - Fight: {p['fight']}")
                print(f"      -> Predicted: {p['predicted_winner']}")
                print(f"      -> Actual:    {p['actual_winner']}")
                print(f"      -> Result: {status}")
            print("------------------------" + "-" * len(model_name)) 