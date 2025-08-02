from ..args import get_prediction_args
from .pipeline import PredictionPipeline
from .models import (
    EloBaselineModel, 
    LogisticRegressionModel, 
    XGBoostModel,
    SVCModel,
    RandomForestModel,
    BernoulliNBModel,
    LGBMModel
)

def get_available_models():
    """Get a list of all available prediction models.
    
    Returns:
        list: List of instantiated model objects
    """
    return [
        EloBaselineModel(),
        LogisticRegressionModel(),
        # XGBoostModel(),
        # SVCModel(),
        # RandomForestModel(),
        # BernoulliNBModel(),
        LGBMModel(),
    ]

def main():
    """
    Main entry point to run the prediction pipeline.
    You can specify which models to run and the reporting format.
    """
    args = get_prediction_args()

    # Handle conflicting arguments
    use_existing_models = not args.no_use_existing_models and args.use_existing_models
    force_retrain = args.force_retrain

    # Log model management settings
    if args.no_use_existing_models:
        print("No-use-existing-models flag set: All models will be retrained from scratch.")
    elif force_retrain:
        print("Force-retrain flag set: All models will be retrained regardless of new data.")
    elif use_existing_models:
        print("Using existing models if available and no new data detected.")

    # Initialize and run prediction pipeline
    pipeline = PredictionPipeline(
        models=get_available_models(),
        use_existing_models=use_existing_models,
        force_retrain=force_retrain
    )
    
    try:
        pipeline.run(detailed_report=(args.report == 'detailed'))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the required data files exist. You may need to run the scraping and ELO analysis first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
