import pandas as pd
import os
from datetime import datetime

def _clean_numeric_column(series):
    """Clean string columns into numbers, handling errors."""
    series_str = series.astype(str)
    return pd.to_numeric(series_str.str.replace(r'[^0-9.]', '', regex=True), errors='coerce')

def _calculate_age(dob_str, fight_date_str):
    """Calculate age in years from date of birth and fight date strings."""
    if pd.isna(dob_str) or not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, '%b %d, %Y')
        fight_date = datetime.strptime(fight_date_str, '%B %d, %Y')
        return (fight_date - dob).days / 365.25
    except (ValueError, TypeError):
        return None

def _get_days_since_last_fight(current_date, past_fights):
    """Calculate days since a fighter's last fight."""
    if not past_fights:
        return None
    last_fight_date = past_fights[-1]['date_obj']
    return (current_date - last_fight_date).days

def _get_win_streak(fighter_name, current_date, past_fights):
    """Calculate current win streak before a given date."""
    streak = 0
    for fight in reversed(past_fights):
        if fight['date_obj'] >= current_date:
            continue
        if fight['winner'] == fighter_name:
            streak += 1
        else:
            break
    return streak

def _to_int_safe(value):
    """Safely convert a value to integer, returning 0 for invalid values."""
    try:
        return int(float(value)) if value and not pd.isna(value) else 0
    except (ValueError, TypeError):
        return 0

def _get_fighter_history_stats(fighter_name, current_fight_date, past_fights, fighters_df, n_fights=5):
    """Calculate historical performance statistics for a fighter."""
    # Sort fights by date and get last N fights before current fight
    past_fights = [f for f in past_fights if f['date_obj'] < current_fight_date]
    past_fights = sorted(past_fights, key=lambda x: x['date_obj'])
    last_n_fights = past_fights[-n_fights:] if past_fights else []
    
    stats = {
        'wins_last_n': 0,
        'ko_wins': 0,
        'total_finishes': 0,
        'first_round_finishes': 0,
        'knockdowns_scored': 0,
        'knockdowns_absorbed': 0,
        'sig_str_landed': 0,
        'sig_str_attempted': 0,
        'takedowns_landed': 0,
        'takedowns_attempted': 0,
        'sub_attempts': 0,
        'ctrl_time_sec': 0,
        'total_fight_time_sec': 0,
        'fights_in_last_year': 0,
        'avg_opp_elo_last_n': 0
    }
    
    # Calculate fights in last year
    one_year_ago = current_fight_date - pd.Timedelta(days=365)
    stats['fights_in_last_year'] = len([f for f in past_fights if f['date_obj'] >= one_year_ago])
    
    # Process each fight
    total_opp_elo = 0
    for fight in last_n_fights:
        is_fighter_1 = (fight['fighter_1'] == fighter_name)
        f_prefix = 'f1' if is_fighter_1 else 'f2'
        opp_prefix = 'f2' if is_fighter_1 else 'f1'
        opponent_name = fight['fighter_2'] if is_fighter_1 else fight['fighter_1']
        
        # Win/Loss and Finishes
        if fight['winner'] == fighter_name:
            stats['wins_last_n'] += 1
            if fight['method'] != 'Decision':
                stats['total_finishes'] += 1
                if fight['round'] == '1':
                    stats['first_round_finishes'] += 1
            if 'KO' in fight['method']:
                stats['ko_wins'] += 1
        
        # Striking and Grappling Stats
        stats['knockdowns_scored'] += _to_int_safe(fight.get(f'{f_prefix}_kd'))
        stats['knockdowns_absorbed'] += _to_int_safe(fight.get(f'{opp_prefix}_kd'))
        stats['sig_str_landed'] += _to_int_safe(fight.get(f'{f_prefix}_sig_str_landed'))
        stats['sig_str_attempted'] += _to_int_safe(fight.get(f'{f_prefix}_sig_str_attempted'))
        stats['takedowns_landed'] += _to_int_safe(fight.get(f'{f_prefix}_td_landed'))
        stats['takedowns_attempted'] += _to_int_safe(fight.get(f'{f_prefix}_td_attempted'))
        stats['sub_attempts'] += _to_int_safe(fight.get(f'{f_prefix}_sub_attempts'))
        
        # Control Time
        ctrl_time = fight.get(f'{f_prefix}_ctrl_time', '0:00')
        if isinstance(ctrl_time, str) and ':' in ctrl_time:
            mins, secs = map(int, ctrl_time.split(':'))
            stats['ctrl_time_sec'] += mins * 60 + secs
        
        # Fight Duration
        round_num = _to_int_safe(fight['round'])
        round_time = fight.get('round_time', '0:00')
        if isinstance(round_time, str) and ':' in round_time:
            mins, secs = map(int, round_time.split(':'))
            stats['total_fight_time_sec'] += (round_num - 1) * 300 + mins * 60 + secs
        
        # Opponent ELO
        if opponent_name in fighters_df.index:
            opp_elo = fighters_df.loc[opponent_name, 'elo']
            if not pd.isna(opp_elo):
                total_opp_elo += opp_elo
    
    # Calculate averages and rates
    n_actual_fights = len(last_n_fights)
    
    # Always provide all required keys with default values
    stats['finish_rate_last_n'] = stats['total_finishes'] / n_actual_fights if n_actual_fights > 0 else 0.0
    stats['first_round_finish_rate_last_n'] = stats['first_round_finishes'] / n_actual_fights if n_actual_fights > 0 else 0.0
    stats['ko_percent_last_n'] = stats['ko_wins'] / n_actual_fights if n_actual_fights > 0 else 0.0
    stats['avg_knockdowns_per_fight_last_n'] = stats['knockdowns_scored'] / n_actual_fights if n_actual_fights > 0 else 0.0
    stats['knockdowns_absorbed_per_fight_last_n'] = stats['knockdowns_absorbed'] / n_actual_fights if n_actual_fights > 0 else 0.0
    stats['avg_opp_elo_last_n'] = total_opp_elo / n_actual_fights if n_actual_fights > 0 else 1500.0
    
    # Per-minute stats
    total_mins = stats['total_fight_time_sec'] / 60
    stats['sig_str_landed_per_min_last_n'] = stats['sig_str_landed'] / total_mins if total_mins > 0 else 0.0
    stats['sig_str_absorbed_per_min_last_n'] = stats['sig_str_attempted'] / total_mins if total_mins > 0 else 0.0
    stats['sub_attempts_per_min_last_n'] = stats['sub_attempts'] / total_mins if total_mins > 0 else 0.0
    stats['avg_ctrl_time_sec_per_min_last_n'] = stats['ctrl_time_sec'] / total_mins if total_mins > 0 else 0.0
    
    # Accuracy stats
    stats['sig_str_defense_last_n'] = stats['sig_str_landed'] / stats['sig_str_attempted'] if stats['sig_str_attempted'] > 0 else 0.5
    stats['takedown_accuracy_last_n'] = stats['takedowns_landed'] / stats['takedowns_attempted'] if stats['takedowns_attempted'] > 0 else 0.5
    stats['takedown_defense_last_n'] = 1 - (stats['takedowns_landed'] / stats['takedowns_attempted']) if stats['takedowns_attempted'] > 0 else 0.5
    
    return stats

def preprocess_for_ml(fights_to_process, fighters_csv_path):
    """Transform fight data into ML-ready features."""
    if not os.path.exists(fighters_csv_path):
        raise FileNotFoundError(f"Fighters data not found at '{fighters_csv_path}'.")

    # Load and prepare fighter data
    fighters_df = pd.read_csv(fighters_csv_path)
    fighters_df['full_name'] = fighters_df['first_name'] + ' ' + fighters_df['last_name']
    fighters_df = fighters_df.drop_duplicates(subset=['full_name']).set_index('full_name')
    
    for col in ['height_cm', 'reach_in', 'elo']:
        if col in fighters_df.columns:
            fighters_df[col] = _clean_numeric_column(fighters_df[col])
    
    # Process fights and calculate features
    processed_fights = []
    for fight in fights_to_process:
        f1_name, f2_name = fight['fighter_1'], fight['fighter_2']
        
        # Skip if either fighter is missing
        if f1_name not in fighters_df.index or f2_name not in fighters_df.index:
            continue
            
        # Get fighter stats
        f1_stats = fighters_df.loc[f1_name]
        f2_stats = fighters_df.loc[f2_name]
        
        # Calculate fight date and ensure date_obj is available
        fight_date = pd.to_datetime(fight['event_date'])
        fight['date_obj'] = fight_date
        
        # Get fighter histories and ensure date_obj is available for all fights
        f1_hist = [f for f in fights_to_process if f1_name in (f['fighter_1'], f['fighter_2'])]
        f2_hist = [f for f in fights_to_process if f2_name in (f['fighter_1'], f['fighter_2'])]
        
        # Ensure date_obj is available for all historical fights
        for hist_fight in f1_hist + f2_hist:
            if 'date_obj' not in hist_fight:
                hist_fight['date_obj'] = pd.to_datetime(hist_fight['event_date'])
        
        # Calculate historical stats
        f1_hist_stats = _get_fighter_history_stats(f1_name, fight_date, f1_hist, fighters_df)
        f2_hist_stats = _get_fighter_history_stats(f2_name, fight_date, f2_hist, fighters_df)
        
        # Calculate ages
        f1_age = _calculate_age(f1_stats.get('dob'), fight['event_date'])
        f2_age = _calculate_age(f2_stats.get('dob'), fight['event_date'])
        
        # Calculate days since last fight
        f1_days_since_last = _get_days_since_last_fight(fight_date, f1_hist) or 547  # ~1.5 years if no previous fights
        f2_days_since_last = _get_days_since_last_fight(fight_date, f2_hist) or 547
        
        # Calculate win streaks
        f1_win_streak = _get_win_streak(f1_name, fight_date, f1_hist)
        f2_win_streak = _get_win_streak(f2_name, fight_date, f2_hist)
        
        # Compile all features
        feature_dict = {
            'winner': 1 if fight.get('winner') == f1_name else 0,
            'date': fight['event_date'],
            'fighter_1': f1_name,
            'fighter_2': f2_name,
            
            # Physical differences
            'height_diff': f1_stats.get('height_cm', 0) - f2_stats.get('height_cm', 0),
            'reach_diff': f1_stats.get('reach_in', 0) - f2_stats.get('reach_in', 0),
            'age_diff': (f1_age or 0) - (f2_age or 0),
            'elo_diff': f1_stats.get('elo', 1500) - f2_stats.get('elo', 1500),
            
            # Career momentum
            'days_since_last_fight_diff': f1_days_since_last - f2_days_since_last,
            'win_streak_diff': f1_win_streak - f2_win_streak,
            'fights_last_year_diff': f1_hist_stats['fights_in_last_year'] - f2_hist_stats['fights_in_last_year'],
            
            # Performance differences
            'finish_rate_diff': f1_hist_stats['finish_rate_last_n'] - f2_hist_stats['finish_rate_last_n'],
            'ko_rate_diff': f1_hist_stats['ko_percent_last_n'] - f2_hist_stats['ko_percent_last_n'],
            'sig_str_per_min_diff': f1_hist_stats['sig_str_landed_per_min_last_n'] - f2_hist_stats['sig_str_landed_per_min_last_n'],
            'td_accuracy_diff': f1_hist_stats['takedown_accuracy_last_n'] - f2_hist_stats['takedown_accuracy_last_n'],
            'sub_attempts_per_min_diff': f1_hist_stats['sub_attempts_per_min_last_n'] - f2_hist_stats['sub_attempts_per_min_last_n'],
            'control_time_diff': f1_hist_stats['avg_ctrl_time_sec_per_min_last_n'] - f2_hist_stats['avg_ctrl_time_sec_per_min_last_n'],
            
            # Defense differences
            'sig_str_defense_diff': f1_hist_stats['sig_str_defense_last_n'] - f2_hist_stats['sig_str_defense_last_n'],
            'td_defense_diff': f1_hist_stats['takedown_defense_last_n'] - f2_hist_stats['takedown_defense_last_n'],
            'knockdowns_absorbed_diff': f1_hist_stats['knockdowns_absorbed_per_fight_last_n'] - f2_hist_stats['knockdowns_absorbed_per_fight_last_n']
        }
        
        processed_fights.append(feature_dict)
    
    if not processed_fights:
        return pd.DataFrame(), pd.Series(), pd.DataFrame()
    
    # Create final dataframes
    df = pd.DataFrame(processed_fights)
    metadata = df[['date', 'fighter_1', 'fighter_2', 'winner']]
    
    # Prepare X and y
    y = df['winner']
    X = df.drop(columns=['winner', 'date', 'fighter_1', 'fighter_2'])
    X = X.reindex(sorted(X.columns), axis=1)  # Ensure consistent column order
    
    # Handle missing values by filling NaNs with 0
    X = X.fillna(0)
    
    return X, y, metadata
