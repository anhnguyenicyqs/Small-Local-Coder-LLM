from sklearn.metrics import accuracy_score, f1_score

def evaluate_model(model, X_test, y_test):
    if not hasattr(model, 'predict'):
        raise ValueError("Model must have a predict method.")
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    return {'accuracy': accuracy, 'f1_score': f1}