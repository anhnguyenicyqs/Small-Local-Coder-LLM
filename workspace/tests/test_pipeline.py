import pytest
import pandas as pd
import numpy as np
from sklearn.datasets import make_classification
from src.data_loader import load_data
from src.preprocessor import preprocess_data
from src.model_trainer import RandomForestClassifier
from src.model_evaluator import evaluate_model
from src.model_saver import save_model, load_model
from src.predictor import Predictor

# Fixture to create a sample dataset
@pytest.fixture
def sample_dataset(tmpdir):
    X, y = make_classification(n_samples=50, n_features=4)
    df = pd.DataFrame(X, columns=[f'feat_{i}' for i in range(4)])
    df['target'] = y
    file_path = tmpdir.join("sample_data.csv")
    df.to_csv(file_path, index=False)
    return str(file_path)

# Fixture to create a trained model
@pytest.fixture
def trained_model(sample_dataset):
    df = load_data(sample_dataset)
    X = df.drop('target', axis=1).values
    y = df['target'].values
    preprocessor = preprocess_data(df)
    trainer = RandomForestClassifier()
    trainer.train(X, y)
    return trainer

# Test for data_loader.load_data
def test_load_data_valid_file(sample_dataset):
    df = load_data(sample_dataset)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

def test_load_data_invalid_file():
    with pytest.raises(FileNotFoundError):
        load_data("non_existent_file.csv")

# Test for preprocessor.preprocess_data
def test_preprocess_data_valid_data(sample_dataset):
    df = load_data(sample_dataset)
    processed_df = preprocess_data(df)
    assert isinstance(processed_df, pd.DataFrame)
    assert not processed_df.empty

def test_preprocess_data_invalid_data():
    df = pd.DataFrame({'feat_0': [1, 2], 'target': [0, 1]})
    with pytest.raises(Exception):
        preprocess_data(df)

# Test for model_trainer.RandomForestClassifier
def test_random_forest_train(trained_model):
    assert isinstance(trained_model, RandomForestClassifier)

def test_random_forest_invalid_train():
    trainer = RandomForestClassifier()
    with pytest.raises(Exception):
        trainer.train(None, None)

# Test for model_evaluator.evaluate_model
def test_evaluate_model_valid_data(trained_model, sample_dataset):
    df = load_data(sample_dataset)
    X = df.drop('target', axis=1).values
    y = df['target'].values
    accuracy = evaluate_model(trained_model, X, y)
    assert isinstance(accuracy, float)
    assert 0 <= accuracy <= 1

def test_evaluate_model_invalid_data():
    trainer = RandomForestClassifier()
    with pytest.raises(Exception):
        evaluate_model(trainer, None, None)

# Test for model_saver.save_model
def test_save_model_valid_model(tmpdir, trained_model):
    file_path = tmpdir.join("model.joblib")
    save_model(trained_model, str(file_path))
    assert os.path.exists(str(file_path))

def test_save_model_invalid_model():
    with pytest.raises(Exception):
        save_model(None, "non_existent_file.joblib")

# Test for model_saver.load_model
def test_load_model_valid_file(tmpdir, trained_model):
    file_path = tmpdir.join("model.joblib")
    save_model(trained_model, str(file_path))
    loaded_model = load_model(str(file_path))
    assert isinstance(loaded_model, RandomForestClassifier)

def test_load_model_invalid_file():
    with pytest.raises(FileNotFoundError):
        load_model("non_existent_file.joblib")

# Test for predictor.Predictor
def test_predictor_valid_data(trained_model, sample_dataset):
    df = load_data(sample_dataset)
    X = df.drop('target', axis=1).values
    predictor = Predictor(trained_model)
    predictions = predictor.predict(X)
    assert isinstance(predictions, np.ndarray)
    assert len(predictions) == len(X)

def test_predictor_invalid_data():
    trainer = RandomForestClassifier()
    predictor = Predictor(trainer)
    with pytest.raises(Exception):
        predictor.predict(None)