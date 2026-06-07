import pandas as pd
from sklearn.preprocessing import StandardScaler

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    if 'target' not in df.columns:
        raise ValueError("DataFrame must contain a 'target' column.")
    
    features = df.drop('target', axis=1)
    target = df['target']
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    processed_df = pd.DataFrame(scaled_features, columns=features.columns)
    processed_df['target'] = target
    
    return processed_df