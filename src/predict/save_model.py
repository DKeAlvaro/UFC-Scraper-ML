import argparse
import os
import joblib
import pandas as pd

from ..config import FIGHTS_CSV_PATH, OUTPUT_DIR
import src.predict.models as models

def save_model(model_name):
    """
    Trains a specified model on the entire dataset and saves it to a file.

    :param model_name: The name of the model class to train (e.g., 'XGBoostModel').
    """
    print(f"--- Training and Saving Model: {model_name} ---")

    # 1. Get the model class from the models module
    try:
        ModelClass = getattr(models, model_name)
    except AttributeError:
        print(f"Error: Model '{model_name}' not found in src/predict/models.py")
        return

    model = ModelClass()

    # 2. Load all available fights for training
    if not os.path.exists(FIGHTS_CSV_PATH):
        raise FileNotFoundError(f"Fights data not found at '{FIGHTS_CSV_PATH}'.")
    
    all_fights = pd.read_csv(FIGHTS_CSV_PATH).to_dict('records')
    print(f"Training model on all {len(all_fights)} available fights...")

    # 3. Train the model
    model.train(all_fights)

    # 4. Save the entire trained model object
    save_path = os.path.join(OUTPUT_DIR, 'trained_model.joblib')
    joblib.dump(model, save_path)

    print(f"\nModel saved successfully to {save_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train and save a prediction model.")
    parser.add_argument(
        '--model', 
        type=str, 
        default='XGBoostModel',
        help="The name of the model class to train and save."
    )
    args = parser.parse_args()
    
    save_model(args.model) 