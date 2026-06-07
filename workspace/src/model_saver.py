import joblib
from typing import Any

def load_model(model_path: str) -> Any:
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Model file {model_path} does not exist.")
    
    return model