import argparse
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
    args = parser.parse_args()

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

    pipeline = PredictionPipeline(models=models_to_run)
    
    try:
        pipeline.run(detailed_report=(args.report == 'detailed'))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the required data files exist. You may need to run the scraping and ELO analysis first.")

if __name__ == '__main__':
    main() 