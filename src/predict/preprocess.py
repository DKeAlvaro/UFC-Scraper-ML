import pandas as pd
import os
import sys
from datetime import datetime
from ..config import FIGHTERS_CSV_PATH

def _clean_numeric_column(series):
    """A helper to clean string columns into numbers, handling errors."""
    series_str = series.astype(str)
    return pd.to_numeric(series_str.str.replace(r'[^0-9.]', '', regex=True), errors='coerce')

def _calculate_age(dob_str, fight_date_str):
    """Calculates age in years from a date of birth string and fight date string."""
    if pd.isna(dob_str) or not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, '%b %d, %Y')
        fight_date = datetime.strptime(fight_date_str, '%B %d, %Y')
        return (fight_date - dob).days / 365.25
    except (ValueError, TypeError):
        return None

def _parse_round_time_to_seconds(round_str, time_str):
    """Converts fight duration from round and time to total seconds."""
    try:
        rounds = int(round_str)
        minutes, seconds = map(int, time_str.split(':'))
        # Assuming 5-minute rounds for calculation simplicity
        return ((rounds - 1) * 5 * 60) + (minutes * 60) + seconds
    except (ValueError, TypeError, AttributeError):
        return 0

def _parse_striking_stats(stat_str):
    """Parses striking stats string like '10 of 20' into (landed, attempted)."""
    try:
        landed, attempted = map(int, stat_str.split(' of '))
        return landed, attempted
    except (ValueError, TypeError, AttributeError):
        return 0, 0

def _get_fighter_history_stats(fighter_name, current_fight_date, fighter_history, fighters_df, n=5):
    """
    Calculates performance statistics for a fighter based on their last n fights.
    """
    past_fights = [f for f in fighter_history if f['date_obj'] < current_fight_date]
    last_n_fights = past_fights[-n:]

    if not last_n_fights:
        # Return a default dictionary with the correct keys for a fighter with no history
        return {
            'wins_last_n': 0,
            'avg_opp_elo_last_n': 1500, # Assume average ELO for first opponent
            'ko_percent_last_n': 0,
            'sig_str_landed_per_min_last_n': 0,
        }

    stats = {
        'wins': 0, 'ko_wins': 0, 'total_time_secs': 0,
        'sig_str_landed': 0, 'opponent_elos': []
    }

    for fight in last_n_fights:
        is_fighter_1 = (fight['fighter_1'] == fighter_name)
        opponent_name = fight['fighter_2'] if is_fighter_1 else fight['fighter_1']

        if fight['winner'] == fighter_name:
            stats['wins'] += 1
            if 'KO' in fight['method']:
                stats['ko_wins'] += 1

        if opponent_name in fighters_df.index:
            opp_elo = fighters_df.loc[opponent_name, 'elo']
            stats['opponent_elos'].append(opp_elo if pd.notna(opp_elo) else 1500)
        
        stats['total_time_secs'] += _parse_round_time_to_seconds(fight['round'], fight['time'])
        
        sig_str_stat = fight.get(f'f1_sig_str' if is_fighter_1 else 'f2_sig_str', '0 of 0')
        landed, _ = _parse_striking_stats(sig_str_stat)
        stats['sig_str_landed'] += landed

    # Final calculations
    avg_opp_elo = sum(stats['opponent_elos']) / len(stats['opponent_elos']) if stats['opponent_elos'] else 1500
    
    return {
        'wins_last_n': stats['wins'],
        'avg_opp_elo_last_n': avg_opp_elo,
        'ko_percent_last_n': (stats['ko_wins'] / stats['wins']) if stats['wins'] > 0 else 0,
        'sig_str_landed_per_min_last_n': (stats['sig_str_landed'] * 60 / stats['total_time_secs']) if stats['total_time_secs'] > 0 else 0,
    }

def preprocess_for_ml(fights_to_process, fighters_csv_path):
    """
    Transforms raw fight and fighter data into a feature matrix (X) and target vector (y)
    suitable for a binary classification machine learning model.

    Args:
        fights_to_process (list of dict): The list of fights to process.
        fighters_csv_path (str): Path to the CSV file with all fighter stats.

    Returns:
        pd.DataFrame: Feature matrix X.
        pd.Series: Target vector y.
        pd.DataFrame: Metadata DataFrame.
    """
    if not os.path.exists(fighters_csv_path):
        raise FileNotFoundError(f"Fighters data not found at '{fighters_csv_path}'.")

    fighters_df = pd.read_csv(fighters_csv_path)
    
    # 1. Prepare fighters data for merging
    fighters_prepared = fighters_df.copy()
    fighters_prepared['full_name'] = fighters_prepared['first_name'] + ' ' + fighters_prepared['last_name']
    
    # Handle duplicate fighter names by keeping the first entry
    fighters_prepared = fighters_prepared.drop_duplicates(subset=['full_name'], keep='first')
    fighters_prepared = fighters_prepared.set_index('full_name')

    for col in ['height_cm', 'reach_in', 'elo']:
        if col in fighters_prepared.columns:
            fighters_prepared[col] = _clean_numeric_column(fighters_prepared[col])

    # 2. Pre-calculate fighter histories to speed up lookups
    # And convert date strings to datetime objects once
    for fight in fights_to_process:
        try:
            # This will work if event_date is a string
            fight['date_obj'] = datetime.strptime(fight['event_date'], '%B %d, %Y')
        except TypeError:
            # This will be triggered if it's already a date-like object (e.g., Timestamp)
            fight['date_obj'] = fight['event_date']
    
    fighter_histories = {}
    for fighter_name in fighters_prepared.index:
        history = [f for f in fights_to_process if fighter_name in (f['fighter_1'], f['fighter_2'])]
        fighter_histories[fighter_name] = sorted(history, key=lambda x: x['date_obj'])

    # 3. Process fights to create features and targets
    feature_list = []
    target_list = []
    metadata_list = []

    for fight in fights_to_process:
        # Per the dataset's design, fighter_1 is always the winner.
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']

        if f1_name not in fighters_prepared.index or f2_name not in fighters_prepared.index:
            continue

        f1_stats, f2_stats = fighters_prepared.loc[f1_name], fighters_prepared.loc[f2_name]
        
        if isinstance(f1_stats, pd.DataFrame): f1_stats = f1_stats.iloc[0]
        if isinstance(f2_stats, pd.DataFrame): f2_stats = f2_stats.iloc[0]

        # Calculate ages for both fighters
        f1_age = _calculate_age(f1_stats.get('dob'), fight['event_date'])
        f2_age = _calculate_age(f2_stats.get('dob'), fight['event_date'])

        # Get historical stats for both fighters
        f1_hist_stats = _get_fighter_history_stats(f1_name, fight['date_obj'], fighter_histories.get(f1_name, []), fighters_prepared)
        f2_hist_stats = _get_fighter_history_stats(f2_name, fight['date_obj'], fighter_histories.get(f2_name, []), fighters_prepared)
        
        # --- Create two training examples from each fight for a balanced dataset ---

        # 1. The "Win" case: (fighter_1 - fighter_2)
        features_win = {
            # Original diffs
            'elo_diff': f1_stats.get('elo', 1500) - f2_stats.get('elo', 1500),
            'height_diff_cm': f1_stats.get('height_cm', 0) - f2_stats.get('height_cm', 0),
            'reach_diff_in': f1_stats.get('reach_in', 0) - f2_stats.get('reach_in', 0),
            'age_diff_years': (f1_age - f2_age) if f1_age and f2_age else 0,
            'stance_is_different': 1 if f1_stats.get('stance') != f2_stats.get('stance') else 0,
            # New historical diffs
            'wins_last_5_diff': f1_hist_stats['wins_last_n'] - f2_hist_stats['wins_last_n'],
            'avg_opp_elo_last_5_diff': f1_hist_stats['avg_opp_elo_last_n'] - f2_hist_stats['avg_opp_elo_last_n'],
            'ko_percent_last_5_diff': f1_hist_stats['ko_percent_last_n'] - f2_hist_stats['ko_percent_last_n'],
            'sig_str_landed_per_min_last_5_diff': f1_hist_stats['sig_str_landed_per_min_last_n'] - f2_hist_stats['sig_str_landed_per_min_last_n'],
        }
        feature_list.append(features_win)
        target_list.append(1)  # 1 represents a win

        # 2. The "Loss" case: (fighter_2 - fighter_1)
        # We invert the differences for the losing case.
        features_loss = {key: -value for key, value in features_win.items()}
        # Stance difference is symmetric; it doesn't get inverted.
        features_loss['stance_is_different'] = features_win['stance_is_different']
        
        feature_list.append(features_loss)
        target_list.append(0)  # 0 represents a loss

        # Add metadata for both generated samples
        # The 'winner' and 'loser' are consistent with the original data structure
        metadata_list.append({
            'winner': f1_name, 'loser': f2_name, 'event_date': fight['event_date']
        })
        metadata_list.append({
            'winner': f1_name, 'loser': f2_name, 'event_date': fight['event_date']
        })

    X = pd.DataFrame(feature_list).fillna(0)
    y = pd.Series(target_list, name='winner')
    metadata = pd.DataFrame(metadata_list)

    print(f"Preprocessing complete. Generated {X.shape[0]} samples with {X.shape[1]} features.")
    return X, y, metadata

if __name__ == '__main__':
    from .pipeline import PredictionPipeline
    
    print("--- Running Preprocessing Example ---")
    
    pipeline = PredictionPipeline(models=[])
    try:
        pipeline._load_and_split_data()
        if pipeline.train_fights:
            X_train, y_train, metadata_train = preprocess_for_ml(pipeline.train_fights, FIGHTERS_CSV_PATH)
            print("\nTraining Data Shape:")
            print("X_train:", X_train.shape)
            print("y_train:", y_train.shape)
            print("metadata_train:", metadata_train.shape)

            print("\nLast 5 rows of X_train (showing populated historical features):")
            print(X_train.tail())
            
            print("\nTarget distribution (0=Loss, 1=Win):")
            print(y_train.value_counts())
            
            print("\nMetadata for last 5 rows:")
            print(metadata_train.tail())

    except FileNotFoundError as e:
        print(e)
        print("Please run the scraping pipeline first ('python -m src.scrape.main').")
