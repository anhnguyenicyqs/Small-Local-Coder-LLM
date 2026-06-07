# src/data_loader.py
import pandas as pd
from typing import Tuple

def load_data(file_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    try:
        df = pd.read_csv(file_path)
        if 'result' not in df.columns:
            raise KeyError("Cột 'result' không tồn tại trong file CSV")
        X = df.drop(columns=['result'])
        y = df['result']
        return X, y
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} không tồn tại")
    except pd.errors.EmptyDataError:
        raise ValueError("File CSV rỗng")
    except pd.errors.ParserError:
        raise ValueError("File CSV định dạng không đúng")

# src/preprocessor.py
import pandas as pd

def preprocess(data: pd.DataFrame) -> pd.DataFrame:
    # One-hot encoding for categorical columns
    data = pd.get_dummies(data)
    return data

# src/trainer.py
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from typing import Any

class DecisionTreeTrainer:
    def __init__(self):
        self.model = DecisionTreeClassifier()

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        self.model.fit(X_train, y_train)

    def predict(self, X_test: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X_test)

class RandomForestTrainer:
    def __init__(self):
        self.model = RandomForestClassifier()

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        self.model.fit(X_train, y_train)

    def predict(self, X_test: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X_test)

# src/evaluator.py
from sklearn.metrics import accuracy_score
import numpy as np

def evaluate(y_true: pd.Series, y_pred: np.ndarray) -> float:
    return accuracy_score(y_true, y_pred)

# src/main.py
# from data_loader import load_data
# from preprocessor import preprocess
# from trainer import DecisionTreeTrainer, RandomForestTrainer
# from evaluator import evaluate
import pandas as pd

def main() -> None:
    try:
        # Load data
        X, y = load_data('data/dataset.csv')
        
        # Preprocess data
        X_processed = preprocess(X)
        
        # Split data into train and test (for simplicity, using the same set for both)
        X_train, X_test = X_processed, X_processed
        y_train, y_test = y, y
        
        # Train models
        dt_trainer = DecisionTreeTrainer()
        rf_trainer = RandomForestTrainer()
        
        dt_trainer.train(X_train, y_train)
        rf_trainer.train(X_train, y_train)
        
        # Predict
        dt_predictions = dt_trainer.predict(X_test)
        rf_predictions = rf_trainer.predict(X_test)
        
        # Evaluate
        dt_accuracy = evaluate(y_test, dt_predictions)
        rf_accuracy = evaluate(y_test, rf_predictions)
        
        print(f"Decision Tree Accuracy: {dt_accuracy}")
        print(f"Random Forest Accuracy: {rf_accuracy}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()