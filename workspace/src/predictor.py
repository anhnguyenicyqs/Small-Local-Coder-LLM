import numpy as np

class Predictor:
    def __init__(self, model):
        if model is None:
            raise ValueError("Model cannot be None.")
        
        self.model = model
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if X is None:
            raise ValueError("Input data cannot be None.")
        
        return self.model.predict(X)