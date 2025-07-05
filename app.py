import gradio as gr
import joblib
from datetime import datetime
import os
import sys

# --- Path and Module Setup ---
# Add the 'src' directory to the system path so we can import our custom modules.
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Although these models are not called directly, they MUST be imported here.
# joblib.load() needs these class definitions in scope to deserialize the model files correctly.
from src.predict.models import (
    BaseMLModel, 
    EloBaselineModel, 
    LogisticRegressionModel, 
    XGBoostModel,
    SVCModel,
    RandomForestModel,
    BernoulliNBModel,
    LGBMModel
)
# Import the configuration variable for the models directory for consistency.
from src.config import MODELS_DIR

# --- Gradio App Setup ---
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)
    print(f"Warning: Models directory not found. Created a dummy directory at '{MODELS_DIR}'.")

# Get a list of available models
available_models = [f for f in os.listdir(MODELS_DIR) if f.endswith(".joblib")]
if not available_models:
    print(f"Warning: No models found in '{MODELS_DIR}'. The dropdown will be empty.")
    available_models.append("No models found")

# --- Prediction Function ---
def predict_fight(model_name, fighter1_name, fighter2_name):
    """
    Loads the selected model and predicts the winner of a fight.
    """
    if model_name == "No models found" or not fighter1_name or not fighter2_name:
        return "Please select a model and enter both fighter names."

    model_path = os.path.join(MODELS_DIR, model_name)
    
    try:
        print(f"Loading model: {model_name}")
        model = joblib.load(model_path)
        
        fight = {
            'fighter_1': fighter1_name,
            'fighter_2': fighter2_name,
            'event_date': datetime.now().strftime('%B %d, %Y')
        }

        prediction_result = model.predict(fight)
        
        if prediction_result and prediction_result.get('winner'):
            winner = prediction_result['winner']
            prob = prediction_result['probability']
            return winner, f"{prob:.1%}"
        else:
            return "Could not make a prediction.", ""
            
    except FileNotFoundError:
        return f"Error: Model file '{model_name}' not found.", ""
    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return f"An error occurred: {e}", ""

# --- Gradio Interface ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🥋 UFC Fight Predictor 🥊")
    gr.Markdown("Select a prediction model and enter two fighter names to predict the outcome.")
    
    with gr.Column():
        model_dropdown = gr.Dropdown(
            label="Select Model", 
            choices=available_models,
            value=available_models[0] if available_models else None
        )
        with gr.Row():
            fighter1_input = gr.Textbox(label="Fighter 1", placeholder="e.g., Jon Jones")
            fighter2_input = gr.Textbox(label="Fighter 2", placeholder="e.g., Stipe Miocic")
    
    predict_button = gr.Button("Predict Winner")
    
    with gr.Column():
        winner_output = gr.Textbox(label="Predicted Winner", interactive=False)
        prob_output = gr.Textbox(label="Confidence", interactive=False)

    predict_button.click(
        fn=predict_fight,
        inputs=[model_dropdown, fighter1_input, fighter2_input],
        outputs=[winner_output, prob_output]
    )

# --- Launch the App ---
demo.launch() 