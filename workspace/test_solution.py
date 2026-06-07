import pytest
from solution import load_data, preprocess, DecisionTreeTrainer, RandomForestTrainer, evaluate
import pandas as pd
import numpy as np
from sklearn.datasets import make_classification

# Mock data for testing
@pytest.fixture
def mock_dataset():
    X, y = make_classification(n_samples=50, n_features=4)
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(4)])
    df['result'] = y
    return df

# Test load_data function
def test_load_data(mock_dataset):
    import os
    os.makedirs('data', exist_ok=True)
    # Save mock dataset to a CSV file
    mock_dataset.to_csv('data/dataset.csv', index=False)
    
    # Load data using the function
    X, y = load_data('data/dataset.csv')
    
    # Check if the loaded data has the correct shape
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert X.shape[0] == 50
    assert y.shape[0] == 50

def test_load_data_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        load_data('data/nonexistent.csv')

# Test preprocess function
def test_preprocess(mock_dataset):
    # Preprocess the mock dataset
    preprocessed_df = preprocess(mock_dataset.drop(columns=['result']))
    
    # Check if the preprocessed data has the correct shape
    assert isinstance(preprocessed_df, pd.DataFrame)
    assert preprocessed_df.shape[0] == 50

# Test DecisionTreeTrainer class
def test_decision_tree_trainer(mock_dataset):
    X_train, y_train = mock_dataset.drop(columns=['result']), mock_dataset['result']
    
    # Initialize and train the model
    dt_trainer = DecisionTreeTrainer()
    dt_trainer.train(X_train, y_train)
    
    # Predict using the trained model
    predictions = dt_trainer.predict(X_train)
    
    # Check if predictions have the correct shape
    assert isinstance(predictions, np.ndarray)
    assert predictions.shape[0] == 50

# Test RandomForestTrainer class
def test_random_forest_trainer(mock_dataset):
    X_train, y_train = mock_dataset.drop(columns=['result']), mock_dataset['result']
    
    # Initialize and train the model
    rf_trainer = RandomForestTrainer()
    rf_trainer.train(X_train, y_train)
    
    # Predict using the trained model
    predictions = rf_trainer.predict(X_train)
    
    # Check if predictions have the correct shape
    assert isinstance(predictions, np.ndarray)
    assert predictions.shape[0] == 50

# Test evaluate function
def test_evaluate(mock_dataset):
    X_train, y_train = mock_dataset.drop(columns=['result']), mock_dataset['result']
    
    # Initialize and train the model
    dt_trainer = DecisionTreeTrainer()
    dt_trainer.train(X_train, y_train)
    
    # Predict using the trained model
    predictions = dt_trainer.predict(X_train)
    
    # Evaluate the model
    accuracy = evaluate(y_train, predictions)
    
    # Check if accuracy is within a reasonable range (0 to 1)
    assert isinstance(accuracy, float)
    assert 0 <= accuracy <= 1

# Test edge case for missing target column
def test_load_data_missing_target_column(mock_dataset):
    import os
    os.makedirs('data', exist_ok=True)
    mock_dataset.drop(columns=['result']).to_csv('data/dataset.csv', index=False)
    
    with pytest.raises(KeyError):
        load_data('data/dataset.csv')