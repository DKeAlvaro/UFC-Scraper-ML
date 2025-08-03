"""Configuration module for UFC prediction models."""

# Model settings
DEFAULT_ELO = 1500
N_FIGHTS_HISTORY = 5
DEFAULT_ROUNDS_DURATION = 5 * 60  # 5 minutes per round

# Date formats
DATE_FORMAT_EVENT = '%B %d, %Y'
DATE_FORMAT_DOB = '%b %d, %Y'

# Feature settings
FEATURE_COLUMNS = [
    'height_cm', 
    'reach_in', 
    'elo', 
    'stance', 
    'dob'
]

# Model hyperparameters
MODEL_DEFAULTS = {
    'LogisticRegression': {},
    'XGBClassifier': {
        'use_label_encoder': False,
        'eval_metric': 'logloss',
        'random_state': 42
    },
    'SVC': {
        'probability': True,
        'random_state': 42
    },
    'RandomForestClassifier': {
        'random_state': 42
    },
    'BernoulliNB': {},
    'LGBMClassifier': {
        'random_state': 42
    }
}