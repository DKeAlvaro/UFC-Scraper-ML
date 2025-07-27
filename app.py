import gradio as gr
import joblib
from datetime import datetime
import os

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
from src.config import MODELS_DIR

# --- Model Cache ---
# This global dictionary will store loaded models to avoid reloading them from disk.
MODEL_CACHE = {}

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
        return "Please select a model and enter both fighter names.", ""

    try:
        # Load model from cache or from disk if it's the first time
        if model_name not in MODEL_CACHE:
            print(f"Loading and caching model: {model_name}...")
            model_path = os.path.join(MODELS_DIR, model_name)
            MODEL_CACHE[model_name] = joblib.load(model_path)
            print("...model cached.")

        model = MODEL_CACHE[model_name]

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