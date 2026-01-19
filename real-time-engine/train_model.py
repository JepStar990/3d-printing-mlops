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
    # Initialize DagsHub (requires DAGSHUB_USERNAME and DAGSHUB_TOKEN environment variables)
    dagshub.init(
        repo_owner='<your-username>',
        repo_name='<your-repo>',
        mlflow=True
    )
    mlflow.set_tracking_uri(
        os.getenv('MLFLOW_TRACKING_URI',
                  'https://dagshub.com/<your-username>/<your-repo>.mlflow')
    )

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
