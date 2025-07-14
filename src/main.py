import argparse
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """
    Main entry point for the UFC data pipeline.
    Supports scraping, analysis, and prediction workflows.
    """
    parser = argparse.ArgumentParser(description="UFC Data Pipeline")
    parser.add_argument(
        '--pipeline', 
        type=str, 
        default='scrape', 
        choices=['scrape', 'analysis', 'predict', 'all'],
        help="Pipeline to run: 'scrape', 'analysis', 'predict', or 'all'"
    )
    parser.add_argument(
        '--scrape-mode', 
        type=str, 
        default='full', 
        choices=['full', 'update'],
        help="Scraping mode: 'full' (complete scraping) or 'update' (latest events only)"
    )
    parser.add_argument(
        '--num-events', 
        type=int, 
        default=5,
        help="Number of latest events to scrape in update mode (default: 5)"
    )
    # Model management arguments for prediction pipeline
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
    
    if args.pipeline in ['scrape', 'all']:
        print("=== Running Scraping Pipeline ===")
        from scrape.main import main as scrape_main
        
        # Override sys.argv to pass arguments to scrape.main
        original_argv = sys.argv
        sys.argv = ['scrape_main', '--mode', args.scrape_mode, '--num-events', str(args.num_events)]
        try:
            scrape_main()
        finally:
            sys.argv = original_argv
    
    if args.pipeline in ['analysis', 'all']:
        print("\n=== Running ELO Analysis ===")
        from analysis.elo import main as elo_main
        elo_main()
    
    if args.pipeline in ['predict', 'all']:
        print("\n=== Running Prediction Pipeline ===")
        from predict.main import main as predict_main
        
        # Override sys.argv to pass model management arguments to predict.main
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

if __name__ == '__main__':
    main()
