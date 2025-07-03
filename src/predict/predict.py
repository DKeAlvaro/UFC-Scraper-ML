import csv
import os
import sys
from datetime import datetime
from ..scrape.config import FIGHTS_CSV_PATH, FIGHTERS_CSV_PATH

def load_fighters_data():
    """Loads fighter data, including ELO scores, into a dictionary."""
    if not os.path.exists(FIGHTERS_CSV_PATH):
        print(f"Error: Fighter data not found at '{FIGHTERS_CSV_PATH}'.")
        print("Please run the ELO analysis first ('python -m src.analysis.elo').")
        return None
    
    fighters = {}
    with open(FIGHTERS_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_name = f"{row['first_name']} {row['last_name']}".strip()
            fighters[full_name] = {'elo': float(row.get('elo', 1500))} # Default ELO if missing
    return fighters

def load_fights_data():
    """Loads fight data and sorts it chronologically."""
    if not os.path.exists(FIGHTS_CSV_PATH):
        print(f"Error: Fights data not found at '{FIGHTS_CSV_PATH}'.")
        return None

    with open(FIGHTS_CSV_PATH, 'r', encoding='utf-8') as f:
        fights = list(csv.DictReader(f))
    
    # Sort fights chronologically to ensure a proper train/test split later
    fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
    return fights

def run_elo_baseline_model(fights, fighters):
    """
    Runs a simple baseline prediction model where the fighter with the higher ELO is predicted to win.
    """
    correct_predictions = 0
    total_predictions = 0
    
    for fight in fights:
        fighter1_name = fight['fighter_1']
        fighter2_name = fight['fighter_2']
        actual_winner = fight['winner']

        # Skip fights that are draws or no contests
        if actual_winner in ["Draw", "NC", ""]:
            continue
            
        fighter1 = fighters.get(fighter1_name)
        fighter2 = fighters.get(fighter2_name)

        if not fighter1 or not fighter2:
            continue # Skip if fighter data is missing

        elo1 = fighter1.get('elo', 1500)
        elo2 = fighter2.get('elo', 1500)
        
        # Predict winner based on higher ELO
        predicted_winner = fighter1_name if elo1 > elo2 else fighter2_name
        
        if predicted_winner == actual_winner:
            correct_predictions += 1
        
        total_predictions += 1
        
    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    return accuracy, total_predictions

def main():
    """
    Main function to run the prediction pipeline.
    """
    print("--- Starting ML Prediction Pipeline ---")

    # Load data
    fighters_data = load_fighters_data()
    fights_data = load_fights_data()
    
    if not fighters_data or not fights_data:
        print("Aborting pipeline due to missing data.")
        return

    # Run baseline model
    print("\nRunning Baseline Model (Predicting winner by highest ELO)...")
    accuracy, total_fights = run_elo_baseline_model(fights_data, fighters_data)
    
    print("\n--- Baseline Model Evaluation ---")
    print(f"Total Fights Evaluated: {total_fights}")
    print(f"Model Accuracy: {accuracy:.2f}%")
    print("---------------------------------")

if __name__ == '__main__':
    main() 