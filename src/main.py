import sys
import os
from .args import get_pipeline_args

def run_scraping_pipeline(args):
    """Execute the scraping pipeline with given arguments."""
    print("=== Running Scraping Pipeline ===")
    from .scrape.main import main as scrape_main
    
    # Pass arguments to scrape.main
    original_argv = sys.argv
    sys.argv = ['scrape_main', '--mode', args.scrape_mode, '--num-events', str(args.num_events)]
    try:
        scrape_main()
    finally:
        sys.argv = original_argv

def run_analysis_pipeline():
    """Execute the ELO analysis pipeline."""
    print("\n=== Running ELO Analysis ===")
    from .analysis.elo import main as elo_main
    elo_main()

def run_prediction_pipeline(args):
    """Execute the prediction pipeline with given arguments."""
    print("\n=== Running Prediction Pipeline ===")
    from .predict.main import main as predict_main
    
    # Pass model management arguments to predict.main
    original_argv = sys.argv
    predict_args = ['predict_main']
    
    if args.no_use_existing_models:
        predict_args.append('--no-use-existing-models')
    elif args.use_existing_models:
        predict_args.append('--use-existing-models')
        
    if args.force_retrain:
        predict_args.append('--force-retrain')
        
    sys.argv = predict_args
    try:
        predict_main()
    finally:
        sys.argv = original_argv

def run_model_update(args):
    """Execute the model update pipeline."""
    print("\n=== Running Model Update Pipeline ===")
    try:
        from .predict.main import MODELS_TO_RUN
        from .predict.pipeline import PredictionPipeline
    except ImportError:
        print("Fatal: Could not import prediction modules.")
        print("Please ensure your project structure and python path are correct.")
        return

    pipeline = PredictionPipeline(models=MODELS_TO_RUN)
    pipeline.update_models_if_new_data()

def main():
    """Main entry point for the UFC data pipeline."""
    args = get_pipeline_args()
    
    # Execute requested pipeline(s)
    if args.pipeline in ['scrape', 'all']:
        run_scraping_pipeline(args)
    
    if args.pipeline in ['analysis', 'all']:
        run_analysis_pipeline()
    
    if args.pipeline == 'update':
        run_model_update(args)
    
    if args.pipeline in ['predict', 'all']:
        run_prediction_pipeline(args)

if __name__ == '__main__':
    main()
