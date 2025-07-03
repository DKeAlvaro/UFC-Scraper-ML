from .models import EloBaselineModel
from .pipeline import PredictionPipeline

def main():
    """
    Sets up the models and runs the prediction pipeline.
    This is where you can add new models to compare them.
    """
    print("--- Initializing Machine Learning Prediction Pipeline ---")

    # 1. Initialize the models you want to test
    elo_model = EloBaselineModel()
    
    # Add other models here to compare them, e.g.:
    # logistic_model = LogisticRegressionModel()
    
    # 2. Create a list of the models to evaluate
    models_to_run = [
        elo_model,
        # logistic_model
    ]

    # 3. Initialize and run the pipeline
    pipeline = PredictionPipeline(models=models_to_run)
    
    # Set detailed_report=False for a summary, or True for a full detailed report
    pipeline.run(detailed_report=False)

if __name__ == '__main__':
    main() 