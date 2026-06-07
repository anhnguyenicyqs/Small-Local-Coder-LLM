import pandas as pd
from sklearn.preprocessing import StandardScaler

def preprocess_data(data):
    # Separate features and target
    X = data.drop('target', axis=1)
    y = data['target']
    
    # Scale the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Combine scaled features with target
    preprocessed_data = pd.DataFrame(X_scaled, columns=X.columns)
    preprocessed_data['target'] = y
    
    return preprocessed_data