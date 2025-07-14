import argparse

# Use absolute imports to avoid relative import issues
from src.predict.pipeline import PredictionPipeline
from src.predict.models import (
    EloBaselineModel, 
    LogisticRegressionModel, 
    XGBoostModel,
    SVCModel,
    RandomForestModel,
    BernoulliNBModel,
    LGBMModel
)

def main():
    """
    Main entry point to run the prediction pipeline.
    You can specify which models to run and the reporting format.
    """
    parser = argparse.ArgumentParser(description="UFC Fight Prediction Pipeline")
    parser.add_argument(
        '--report', 
        type=str, 
        default='detailed', 
        choices=['detailed', 'summary'],
        help="Type of report to generate: 'detailed' (file) or 'summary' (console)."
    )
    parser.add_argument(
        '--use-existing-models',
        action='store_true',
        default=True,
        help="Use existing saved models if available and no new data (default: True)."
    )
    parser.add_argument(
        '--no-use-existing-models',
        action='store_true',
        default=False,
        help="Force retrain all models from scratch, ignoring existing saved models."
    )
    parser.add_argument(
        '--force-retrain',
        action='store_true',
        default=False,
        help="Force retrain all models even if no new data is available."
    )
    args = parser.parse_args()

    # Handle conflicting arguments
    use_existing_models = not args.no_use_existing_models and args.use_existing_models
    force_retrain = args.force_retrain

    if args.no_use_existing_models:
        print("No-use-existing-models flag set: All models will be retrained from scratch.")
    elif force_retrain:
        print("Force-retrain flag set: All models will be retrained regardless of new data.")
    elif use_existing_models:
        print("Using existing models if available and no new data detected.")

    # --- Define Models to Run ---
    # Instantiate all the models you want to evaluate here.
    models_to_run = [
        EloBaselineModel(),
        LogisticRegressionModel(),
        XGBoostModel(),
        SVCModel(),
        RandomForestModel(),
        BernoulliNBModel(),
        LGBMModel(),
    ]
    # --- End of Model Definition ---

    pipeline = PredictionPipeline(
        models=models_to_run, 
        use_existing_models=use_existing_models,
        force_retrain=force_retrain
    )
    
    try:
        pipeline.run(detailed_report=(args.report == 'detailed'))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the required data files exist. You may need to run the scraping and ELO analysis first.")

if __name__ == '__main__':
    main() 