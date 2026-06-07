import joblib
import os

def save_model(model, file_path: str) -> None:
    if model is None:
        raise ValueError("Model cannot be None.")
    
    try:
        joblib.dump(model.model, file_path)
    except Exception as e:
        raise Exception(f"Error saving model to {file_path}: {e}")

def load_model(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")
    
    try:
        return joblib.load(file_path)
    except Exception as e:
        raise Exception(f"Error loading model from {file_path}: {e}")