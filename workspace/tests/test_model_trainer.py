import pytest
from src.model_trainer import RandomForestTrainer
from sklearn.datasets import make_classification
import pandas as pd
import os
from joblib import dump, load

# Fixture to create a small dataset
@pytest.fixture
def sample_data():
    X, y = make_classification(n_samples=50, n_features=4)
    df = pd.DataFrame(X, columns=[f'feat_{i}' for i in range(4)])
    df['target'] = y
    return df

# Fixture to create a model trainer instance
@pytest.fixture
def trainer():
    return RandomForestTrainer()

# Test case 1: Train with valid data
def test_train_with_valid_data(trainer, sample_data):
    X = sample_data.drop('target', axis=1)
    y = sample_data['target']
    trainer.train(X, y)
    assert hasattr(trainer, 'model')

# Test case 2: Train with invalid data (empty dataframe)
def test_train_with_invalid_data(trainer):
    with pytest.raises(ValueError):
        trainer.train(pd.DataFrame(), pd.Series())

# Test case 3: Save model to file
def test_save_model(trainer, sample_data, tmpdir):
    X = sample_data.drop('target', axis=1)
    y = sample_data['target']
    trainer.train(X, y)
    model_path = os.path.join(tmpdir, 'model.joblib')
    trainer.save_model(model_path)
    assert os.path.exists(model_path)

# Test case 4: Save model to non-existent directory
def test_save_model_to_non_existent_directory(trainer):
    with pytest.raises(FileNotFoundError):
        trainer.save_model('/nonexistent/directory/model.joblib')

# Test case 5: Load model from file
def test_load_model(tmpdir):
    X, y = make_classification(n_samples=50, n_features=4)
    df = pd.DataFrame(X, columns=[f'feat_{i}' for i in range(4)])
    df['target'] = y
    trainer = RandomForestTrainer()
    trainer.train(df.drop('target', axis=1), df['target'])
    model_path = os.path.join(tmpdir, 'model.joblib')
    trainer.save_model(model_path)
    
    loaded_trainer = RandomForestTrainer()
    loaded_trainer.load_model(model_path)
    assert hasattr(loaded_trainer, 'model')

# Test case 6: Load non-existent model file
def test_load_non_existent_model_file():
    with pytest.raises(FileNotFoundError):
        trainer = RandomForestTrainer()
        trainer.load_model('/nonexistent/model.joblib')