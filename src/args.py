import argparse

def get_pipeline_args():
    """
    Parse command line arguments for the main UFC data pipeline.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="UFC Data Pipeline")
    
    # Pipeline selection
    parser.add_argument(
        '--pipeline',
        type=str,
        default='scrape',
        choices=['scrape', 'analysis', 'predict', 'update', 'all'],
        help="Pipeline to run: 'scrape', 'analysis', 'predict', 'update', or 'all'"
    )
    
    # Scraping arguments
    scraping_group = parser.add_argument_group('Scraping options')
    scraping_group.add_argument(
        '--scrape-mode',
        type=str,
        default='full',
        choices=['full', 'update'],
        help="Scraping mode: 'full' (complete scraping) or 'update' (latest events only)"
    )
    scraping_group.add_argument(
        '--num-events',
        type=int,
        default=5,
        help="Number of latest events to scrape in update mode (default: 5)"
    )
    
    # Model management arguments
    model_group = parser.add_argument_group('Model management')
    model_group.add_argument(
        '--use-existing-models',
        action='store_true',
        default=True,
        help="Use existing saved models if available and no new data (default: True)"
    )
    model_group.add_argument(
        '--no-use-existing-models',
        action='store_true',
        default=False,
        help="Force retrain all models from scratch, ignoring existing saved models"
    )
    model_group.add_argument(
        '--force-retrain',
        action='store_true',
        default=False,
        help="Force retrain all models even if no new data is available"
    )
    
    return parser.parse_args()

def get_prediction_args():
    """
    Parse command line arguments specific to the prediction pipeline.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="UFC Fight Prediction Pipeline")
    
    parser.add_argument(
        '--report',
        type=str,
        default='detailed',
        choices=['detailed', 'summary'],
        help="Type of report to generate: 'detailed' (file) or 'summary' (console)"
    )
    
    model_group = parser.add_argument_group('Model management')
    model_group.add_argument(
        '--use-existing-models',
        action='store_true',
        default=True,
        help="Use existing saved models if available and no new data (default: True)"
    )
    model_group.add_argument(
        '--no-use-existing-models',
        action='store_true',
        default=False,
        help="Force retrain all models from scratch, ignoring existing saved models"
    )
    model_group.add_argument(
        '--force-retrain',
        action='store_true',
        default=False,
        help="Force retrain all models even if no new data is available"
    )
    
    return parser.parse_args()