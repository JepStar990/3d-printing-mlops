"""
Train ML model for surface roughness prediction.
Log experiment to DagsHub via MLflow.
"""
import os
import pickle
import sys
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import mlflow
import dagshub

# Allow import from sibling directory
sys.path.append('..')
from utils.load_data import load_historical_data


def main():
    # Configure MLflow tracking (local or DagsHub)
    dagshub_repo = os.getenv('DAGSHUB_REPO')
    if dagshub_repo and dagshub_repo.strip():
        # Extract owner and repo name from URL (supports https://dagshub.com/<owner>/<repo>.git)
        import re
        match = re.search(r'https?://dagshub\.com/([^/]+)/([^/.]+)', dagshub_repo)
        if match:
            repo_owner = match.group(1)
            repo_name = match.group(2)
            dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
            mlflow_tracking_uri = f'https://dagshub.com/{repo_owner}/{repo_name}.mlflow'
            mlflow.set_tracking_uri(mlflow_tracking_uri)
            print(f"Configured DagsHub MLflow tracking: {mlflow_tracking_uri}")
        else:
            print(f"Could not parse DAGSHUB_REPO: {dagshub_repo}. Using local MLflow.")
            mlflow.set_tracking_uri('file:///tmp/mlruns')
    else:
        print("DAGSHUB_REPO not set. Using local MLflow.")
        mlflow.set_tracking_uri('file:///tmp/mlruns')

    # Load historical data
    print("Loading historical data...")
    df = load_historical_data()
    if df.empty:
        raise ValueError("Historical data is empty.")

    # Define features and target
    feature_candidates = [
        'print_speed', 'nozzle_temperature', 'bed_temperature',
        'vibration', 'humidity'
    ]
    target = 'surface_roughness'

    available_features = [col for col in feature_candidates if col in df.columns]
    if len(available_features) == 0:
        raise ValueError("No predefined features found in the dataset.")
    print(f"Using features: {available_features}")

    X = df[available_features].values
    y = df[target].values if target in df.columns else None
    if y is None:
        raise ValueError(f"Target column '{target}' not found.")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Model selection based on environment variable
    model_type = os.getenv('MODEL_TYPE', 'kNN').lower()
    if model_type == 'knn':
        model = KNeighborsRegressor(n_neighbors=5)
    else:
        raise ValueError(f"Unsupported MODEL_TYPE: {model_type}")

    # Start MLflow run
    with mlflow.start_run():
        mlflow.log_param('model_type', model_type)
        mlflow.log_param('n_features', len(available_features))
        mlflow.log_param('features', ','.join(available_features))

        # Train
        model.fit(X_train_scaled, y_train)

        # Predict and evaluate
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        mlflow.log_metric('mae', mae)
        mlflow.log_metric('r2', r2)

        # Log the sklearn model
        mlflow.sklearn.log_model(model, 'model')

        # Save model, scaler and feature list locally for runtime use
        os.makedirs('models', exist_ok=True)
        model_path = os.getenv('MODEL_PATH', 'models/model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump((model, scaler, available_features), f)
        print(f"Model saved to {model_path}")

        # Upload as artifact
        mlflow.log_artifact(model_path)

        print(f"Training completed. MAE: {mae:.3f}, R²: {r2:.3f}")


if __name__ == '__main__':
    main()
