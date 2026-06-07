import numpy as np
from sklearn.ensemble import RandomForestClassifier

class RandomForestClassifier:
    def __init__(self, n_estimators=100, max_depth=None):
        self.model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        if X_train is None or y_train is None:
            raise ValueError("Training data cannot be None.")
        
        self.model.fit(X_train, y_train)