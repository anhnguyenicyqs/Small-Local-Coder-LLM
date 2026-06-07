import numpy as np
from sklearn.metrics import accuracy_score

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> float:
    if model is None or X_test is None or y_test is None:
        raise ValueError("Model and test data cannot be None.")
    
    predictions = model.model.predict(X_test)
    return accuracy_score(y_test, predictions)