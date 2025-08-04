"""
UFC Fight Prediction Pipeline

Copyright (C) 2025 Alvaro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import csv
import os
from datetime import datetime
from collections import OrderedDict
import json
import joblib
from ..config import FIGHTS_CSV_PATH, MODEL_RESULTS_PATH, MODELS_DIR, LAST_EVENT_JSON_PATH
from .models import BaseModel
from sklearn.model_selection import KFold
import mlflow
import mlflow.sklearn

class PredictionPipeline:
    """
    Orchestrates the model training, evaluation, and reporting pipeline.
    """
    def __init__(self, models, use_existing_models=True, force_retrain=False):
        if not all(isinstance(m, BaseModel) for m in models):
            raise TypeError("All models must be instances of BaseModel.")
        self.models = models
        self.train_fights = []
        self.test_fights = []
        self.results = {}
        self.use_existing_models = use_existing_models
        self.force_retrain = force_retrain

    def _get_last_trained_event(self):
        """Get the last event that models were trained on."""
        if not os.path.exists(LAST_EVENT_JSON_PATH):
            return None
        try:
            with open(LAST_EVENT_JSON_PATH, 'r', encoding='utf-8') as f:
                last_event_data = json.load(f)
                if isinstance(last_event_data, list) and len(last_event_data) > 0:
                    return last_event_data[0].get('name'), last_event_data[0].get('date')
                return None, None
        except (json.JSONDecodeError, FileNotFoundError):
            return None, None

    def _save_last_trained_event(self, event_name, event_date):
        """Save the last event that models were trained on."""
        last_event_data = [{
            "name": event_name,
            "date": event_date,
            "training_timestamp": datetime.now().isoformat()
        }]
        try:
            with open(LAST_EVENT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(last_event_data, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save last trained event: {e}")

    def _has_new_data_since_last_training(self):
        """Check if there's new fight data since the last training."""
        last_event_name, last_event_date = self._get_last_trained_event()
        if not last_event_name or not last_event_date:
            return True  # No previous training record, consider as new data
        
        if not os.path.exists(FIGHTS_CSV_PATH):
            return False
        
        with open(FIGHTS_CSV_PATH, 'r', encoding='utf-8') as f:
            fights = list(csv.DictReader(f))
        
        if not fights:
            return False
        
        # Sort fights by date to get the latest event
        fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
        latest_fight = fights[-1]
        latest_event_name = latest_fight['event_name']
        latest_event_date = latest_fight['event_date']
        
        # Check if we have new events since last training
        if latest_event_name != last_event_name:
            print(f"New data detected: Latest event '{latest_event_name}' differs from last trained event '{last_event_name}'")
            return True
        
        return False

    def _model_exists(self, model):
        """Check if a saved model file exists and can be loaded successfully."""
        model_name = model.__class__.__name__
        file_name = f"{model_name}.joblib"
        save_path = os.path.join(MODELS_DIR, file_name)
        
        if not os.path.exists(save_path):
            return False
        
        # Verify the model can actually be loaded
        try:
            joblib.load(save_path)
            return True
        except Exception as e:
            print(f"Warning: Model file {file_name} exists but cannot be loaded ({e}). Will retrain.")
            return False

    def _load_existing_model(self, model_class):
        """Load an existing model from disk."""
        model_name = model_class.__name__
        file_name = f"{model_name}.joblib"
        load_path = os.path.join(MODELS_DIR, file_name)
        
        try:
            loaded_model = joblib.load(load_path)
            print(f"Loaded existing model: {model_name}")
            return loaded_model
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None

    def _should_retrain_models(self):
        """Determine if models should be retrained."""
        if self.force_retrain:
            print("Force retrain flag is set. Retraining all models.")
            return True
        
        if not self.use_existing_models:
            print("Use existing models flag is disabled. Retraining all models.")
            return True
        
        # Check if any model files are missing
        missing_models = [m for m in self.models if not self._model_exists(m)]
        if missing_models:
            missing_names = [m.__class__.__name__ for m in missing_models]
            print(f"Missing model files for: {missing_names}. Retraining all models.")
            return True
        
        # Check if there's new data since last training
        if self._has_new_data_since_last_training():
            return True
        
        print("No new data detected and all model files exist. Using existing models.")
        return False

    def _load_and_split_data(self, num_test_events: int = 1) -> None:
        """Loads and splits the data into chronological training and testing sets."""
        print("\n--- Loading and Splitting Data ---")
        if not os.path.exists(FIGHTS_CSV_PATH):
            raise FileNotFoundError(f"Fights data not found at '{FIGHTS_CSV_PATH}'.")

        fights = self._load_fights()
        
        all_events = list(OrderedDict.fromkeys(f['event_name'] for f in fights))
        if len(all_events) < num_test_events:
            print(f"Warning: Fewer than {num_test_events} events found. Adjusting test set size.")
            num_test_events = len(all_events)
            
        test_event_names = all_events[-num_test_events:]
        self.train_fights = [f for f in fights if f['event_name'] not in test_event_names]
        self.test_fights = [f for f in fights if f['event_name'] in test_event_names]
        print(f"Data loaded. {len(self.train_fights)} training fights, {len(self.test_fights)} testing fights.")
        print(f"Testing on the last {num_test_events} event(s): {', '.join(test_event_names)}")

    def _load_fights(self) -> list:
        """Helper method to load and sort fights from CSV."""
        with open(FIGHTS_CSV_PATH, 'r', encoding='utf-8') as f:
            fights = list(csv.DictReader(f))
        
        fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
        return fights

    def run(self, detailed_report: bool = True) -> None:
        """Executes the full pipeline: load, train, evaluate, report and save models."""
        self._load_and_split_data()
        
        eval_fights = [f for f in self.test_fights if f['winner'] not in ["Draw", "NC", ""]]
        if not eval_fights:
            print("No fights with definitive outcomes in the test set. Aborting.")
            return

        should_retrain = self._should_retrain_models()
        
        for i, model in enumerate(self.models):
            model_name = model.__class__.__name__
            print(f"\n--- Evaluating Model: {model_name} ---")
            
            if should_retrain:
                print(f"Training {model_name}...")
                model.train(self.train_fights)
            else:
                # Try to load existing model, fall back to training if loading fails
                loaded_model = self._load_existing_model(model.__class__)
                if loaded_model is not None:
                    # Replace the model instance with the loaded one
                    self.models[i] = loaded_model
                    model = loaded_model
                else:
                    print(f"Failed to load {model_name}, training new model...")
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
            model_status = "retrained" if should_retrain else "loaded from disk"
            self.results[model_name] = {
                'accuracy': accuracy, 
                'predictions': predictions,
                'total_fights': len(eval_fights),
                'model_status': model_status
            }

        if detailed_report:
            self._report_detailed_results()
        else:
            self._report_summary()

        # Only train and save models if retraining was performed
        if should_retrain:
            self._train_and_save_models()

    def run_kfold_cv(self, k: int = 3, holdout_events: int = 1):
        """Performs k-fold cross-validation where each fold is a set of events.
        Within each fold, we keep the last *holdout_events* for testing."""
        fights = self._load_fights()

        # Build an ordered list of unique events
        event_list = list(OrderedDict.fromkeys(f['event_name'] for f in fights))

        # Initialize KFold splitter on events
        kf = KFold(n_splits=k, shuffle=True, random_state=42)

        all_fold_metrics = []
        for fold_idx, (train_event_idx, test_event_idx) in enumerate(kf.split(event_list), start=1):
            train_events = [event_list[i] for i in train_event_idx]

            # Collect fights that belong to the training events
            fold_fights = [f for f in fights if f['event_name'] in train_events]

            # Inside this fold, reserve the last `holdout_events` events for testing
            fold_events_ordered = list(OrderedDict.fromkeys(f['event_name'] for f in fold_fights))
            test_events = fold_events_ordered[-holdout_events:]

            train_set = [f for f in fold_fights if f['event_name'] not in test_events]
            test_set  = [f for f in fold_fights if f['event_name'] in test_events]

            # Start an MLflow run for the current fold
            mlflow.set_experiment("UFC_KFold_CV")
            with mlflow.start_run(run_name=f"fold_{fold_idx}"):
                # Log meta information about the fold
                mlflow.log_param("fold", fold_idx)
                mlflow.log_param("train_events", len(train_events))
                mlflow.log_param("test_events", holdout_events)

                fold_results = {}
                for model in self.models:
                    model_name = model.__class__.__name__

                    # Train and evaluate
                    model.train(train_set)
                    correct = 0
                    total_fights = 0
                    for fight in test_set:
                        if fight['winner'] not in ["Draw", "NC", ""]:
                            prediction = model.predict(fight)
                            if prediction.get('winner') == fight['winner']:
                                correct += 1
                            total_fights += 1

                    acc = correct / total_fights if total_fights > 0 else 0.0
                    fold_results[model_name] = acc

                    # Log metrics and register model to appear in MLflow Models tab
                    mlflow.log_metric(f"accuracy_{model_name}", acc)
                    mlflow.log_metric(f"total_fights_{model_name}", total_fights)
                    
                    # Register the model with MLflow to appear in Models tab
                    mlflow.sklearn.log_model(
                        model, 
                        f"model_{model_name}",
                        registered_model_name=f"{model_name}_UFC_Model"
                    )

                all_fold_metrics.append(fold_results)

        return all_fold_metrics

    def update_models_if_new_data(self):
        """
        Checks for new data and retrains/saves all models on the full dataset if needed.
        This does not run any evaluation.
        """
        print("\n--- Checking for Model Updates ---")
        
        # Check if any model files are missing or invalid
        missing_models = [m for m in self.models if not self._model_exists(m)]
        has_new_data = self._has_new_data_since_last_training()

        if missing_models:
            missing_names = [m.__class__.__name__ for m in missing_models]
            print(f"Missing or invalid model files found for: {missing_names}.")
            self._train_and_save_models()
        elif has_new_data:
            print("New data detected, retraining all models...")
            self._train_and_save_models()
        else:
            print("No new data detected. Models are already up-to-date.")

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

        # Get the latest event info for tracking
        if all_fights:
            all_fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
            latest_fight = all_fights[-1]
            latest_event_name = latest_fight['event_name']
            latest_event_date = latest_fight['event_date']

        for model in self.models:
            model_name = model.__class__.__name__
            print(f"\n--- Training: {model_name} ---")
            model.train(all_fights)
            
            # Sanitize and save the model
            file_name = f"{model_name}.joblib"
            save_path = os.path.join(MODELS_DIR, file_name)
            joblib.dump(model, save_path)
            print(f"Model saved successfully to {save_path}")

        # Save the last trained event info
        if all_fights:
            self._save_last_trained_event(latest_event_name, latest_event_date)
            print(f"Updated last trained event: {latest_event_name} ({latest_event_date})")

    def _report_summary(self):
        """Prints a concise summary of model performance."""
        print("\n\n--- Prediction Pipeline Summary ---")
        print(f"{'Model':<25} | {'Accuracy':<10} | {'Fights Evaluated':<20} | {'Status':<15}")
        print("-" * 80)
        for model_name, result in self.results.items():
            status = result.get('model_status', 'unknown')
            print(f"{model_name:<25} | {result['accuracy']:<9.2f}% | {result['total_fights']:<20} | {status:<15}")
        print("-" * 80)

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
                    "model_status": result.get('model_status', 'unknown'),
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