import joblib
from sklearn.ensemble import RandomForestClassifier
from typing import Optional
import os

class RandomForestTrainer:
    def __init__(self, hyperparameters: Optional[dict] = None):
        # Load default hyperparameters from config file if it exists
        try:
            import yaml
            with open('config/hyperparameters.yaml', 'r') as f:
                default_hyperparams = yaml.safe_load(f)
        except FileNotFoundError:
            default_hyperparams = {}
        
        # Update with provided hyperparameters if any
        self.hyperparameters = {**default_hyperparams, **(hyperparameters or {})}
        self.model = None

    def train(self, X_train, y_train):
        if X_train.empty or y_train.empty:
            raise ValueError("Training data cannot be empty.")
        
        # Initialize and train the model
        self.model = RandomForestClassifier(**self.hyperparameters)
        self.model.fit(X_train, y_train)

    def save_model(self, model_path: str):
        try:
            joblib.dump(self.model, model_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Directory {os.path.dirname(model_path)} does not exist.")

    def load_model(self, model_path: str):
        try:
            self.model = joblib.load(model_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Model file {model_path} does not exist.")