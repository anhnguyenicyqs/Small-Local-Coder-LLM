# %%
import pandas as pd
from src.data_loader import load_iris_data
from src.data_preprocessor import preprocess_data
from src.model_trainer import RandomForestTrainer
from src.model_evaluator import evaluate_model
from sklearn.model_selection import train_test_split

# Load data
data = load_iris_data()

# Preprocess data
preprocessed_data = preprocess_data(data)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(preprocessed_data.drop('target', axis=1), 
                                                    preprocessed_data['target'], 
                                                    test_size=0.2, 
                                                    random_state=42)

# Train model
trainer = RandomForestTrainer()
trainer.train(X_train, y_train)

# Evaluate model
evaluation_results = evaluate_model(trainer.model, X_test, y_test)
print(evaluation_results)

# Save model
model_path = 'models/iris_random_forest.joblib'
trainer.save_model(model_path)