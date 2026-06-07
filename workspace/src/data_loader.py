import pandas as pd

def load_iris_data():
    # Load Iris dataset from sklearn.datasets
    from sklearn.datasets import load_iris
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    df['target'] = iris.target
    return df