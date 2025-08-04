import pandas as pd
from datetime import datetime
from typing import Optional, Any

from .config import DEFAULT_ROUNDS_DURATION

def clean_numeric_column(series: pd.Series) -> pd.Series:
    """A helper to clean string columns into numbers, handling errors."""
    series_str = series.astype(str)
    return pd.to_numeric(series_str.str.replace(r'[^0-9.]', '', regex=True), errors='coerce')

def calculate_age(dob_str: str, fight_date_str: str) -> Optional[float]:
    """Calculates age in years from a date of birth string and fight date string."""
    if pd.isna(dob_str) or not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, '%b %d, %Y')
        fight_date = datetime.strptime(fight_date_str, '%B %d, %Y')
        return (fight_date - dob).days / 365.25
    except (ValueError, TypeError):
        return None

def parse_round_time_to_seconds(round_str: str, time_str: str) -> int:
    """Converts fight duration from round and time to total seconds."""
    try:
        rounds = int(round_str)
        minutes, seconds = map(int, time_str.split(':'))
        # Assuming 5-minute rounds for calculation simplicity
        return ((rounds - 1) * DEFAULT_ROUNDS_DURATION) + (minutes * 60) + seconds
    except (ValueError, TypeError, AttributeError):
        return 0

def parse_striking_stats(stat_str: str) -> tuple[int, int]:
    """Parses striking stats string like '10 of 20' into (landed, attempted)."""
    try:
        landed, attempted = map(int, stat_str.split(' of '))
        return landed, attempted
    except (ValueError, TypeError, AttributeError):
        return 0, 0

def to_int_safe(val: Any) -> int:
    """Safely converts a value to an integer, returning 0 if it's invalid or empty."""
    if pd.isna(val):
        return 0
    try:
        # handle strings with whitespace or empty strings
        return int(str(val).strip() or 0)
    except (ValueError, TypeError):
        return 0

def prepare_fighters_data(fighters_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares fighter data for analysis by cleaning and standardizing."""
    fighters_prepared = fighters_df.copy()
    fighters_prepared['full_name'] = fighters_prepared['first_name'] + ' ' + fighters_prepared['last_name']
    
    # Handle duplicate fighter names by keeping the first entry
    fighters_prepared = fighters_prepared.drop_duplicates(subset=['full_name'], keep='first')
    fighters_prepared = fighters_prepared.set_index('full_name')

    for col in ['height_cm', 'reach_in', 'elo']:
        if col in fighters_prepared.columns:
            fighters_prepared[col] = clean_numeric_column(fighters_prepared[col])
    
    return fighters_prepared