import csv
import os
import sys
from datetime import datetime
from collections import OrderedDict
import json
import joblib

from ..config import FIGHTS_CSV_PATH, MODEL_RESULTS_PATH, MODELS_DIR
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
        """Executes the full pipeline: load, train, evaluate, report and save models."""
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
                event_name = fight.get('event_name', 'Unknown Event')
                
                prediction_result = model.predict(fight)
                predicted_winner = prediction_result.get('winner')
                probability = prediction_result.get('probability')

                is_correct = (predicted_winner == actual_winner)
                if is_correct:
                    correct_predictions += 1
                
                predictions.append({
                    'fight': f"{f1_name} vs. {f2_name}",
                    'event': event_name,
                    'predicted_winner': predicted_winner,
                    'probability': f"{probability:.1%}" if probability is not None else "N/A",
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

        self._train_and_save_models()

    def _train_and_save_models(self):
        """Trains all models on the full dataset and saves them."""
        print("\n\n--- Training and Saving All Models on Full Dataset ---")

        if not os.path.exists(FIGHTS_CSV_PATH):
            print(f"Error: Fights data not found at '{FIGHTS_CSV_PATH}'. Cannot save models.")
            return
            
        with open(FIGHTS_CSV_PATH, 'r', encoding='utf-8') as f:
            all_fights = list(csv.DictReader(f))
        
        print(f"Training models on all {len(all_fights)} available fights...")

        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)
            print(f"Created directory: {MODELS_DIR}")

        for model in self.models:
            model_name = model.__class__.__name__
            print(f"\n--- Training: {model_name} ---")
            model.train(all_fights)
            
            # Sanitize and save the model
            file_name = f"{model_name}.joblib"
            save_path = os.path.join(MODELS_DIR, file_name)
            joblib.dump(model, save_path)
            print(f"Model saved successfully to {save_path}")

    def _report_summary(self):
        """Prints a concise summary of model performance."""
        print("\n\n--- Prediction Pipeline Summary ---")
        print(f"{'Model':<25} | {'Accuracy':<10} | {'Fights Evaluated':<20}")
        print("-" * 65)
        for model_name, result in self.results.items():
            print(f"{model_name:<25} | {result['accuracy']:<9.2f}% | {result['total_fights']:<20}")
        print("-" * 65)

    def _save_report_to_json(self, file_path=MODEL_RESULTS_PATH):
        """Saves the detailed prediction results to a JSON file."""
        print(f"\nSaving detailed report to {file_path}...")
        try:
            # Create a report structure that is clean and JSON-friendly
            report = {}
            for model_name, result in self.results.items():
                
                # Group predictions by event for a more organized report
                predictions_by_event = {}
                for p in result['predictions']:
                    event_name = p.pop('event') # Extract event and remove it from the sub-dictionary
                    if event_name not in predictions_by_event:
                        predictions_by_event[event_name] = []
                    predictions_by_event[event_name].append(p)

                report[model_name] = {
                    "overall_accuracy": f"{result['accuracy']:.2f}%",
                    "total_fights_evaluated": result['total_fights'],
                    "predictions_by_event": predictions_by_event
                }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4)
            print("Report saved successfully.")
        except (IOError, TypeError) as e:
            print(f"Error saving report to JSON file: {e}")

    def _report_detailed_results(self):
        """Prints a summary and saves the detailed report to a file."""
        print("\n\n--- Prediction Pipeline Finished: Detailed Report ---")
        # A summary is printed to the console for convenience.
        self._report_summary()
        # The detailed report is now saved to a JSON file.
        self._save_report_to_json() 