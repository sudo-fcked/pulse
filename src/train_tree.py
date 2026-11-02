import os, yaml, mlflow, joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score
from features import add_features, fit_target_encoders

def run_tree_training():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("pulse_models")

    print("Loading frozen DVC splits...")
    train_raw = pd.read_parquet("data/splits/train.parquet")
    val_raw = pd.read_parquet("data/splits/val.parquet")

    encoders = fit_target_encoders(train_raw)
    train_df = add_features(train_raw, target_encoders=encoders)
    val_df = add_features(val_raw, target_encoders=encoders)

    # 1. Map direction
    for df in [train_df, val_df]:
        df['direction_id'] = df['direction_id'].apply(lambda x: 1.0 if str(x).lower() == 'inbound' else 0.0)

    # 2. Ordinal encode categorical features to floats instead of using Pandas categories
    categorical_features = ['point_type', 'standard_type', 'day_of_week', 'hour']
    for col in categorical_features:
        train_df[col] = train_df[col].astype(str)
        val_df[col] = val_df[col].astype(str)

    ord_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1.0)
    train_df[categorical_features] = ord_encoder.fit_transform(train_df[categorical_features])
    val_df[categorical_features] = ord_encoder.transform(val_df[categorical_features])

    numeric_features = [
        'direction_id', 'time_point_order', 'scheduled_headway', 'minute_of_day',
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
        'stop_id_encoded', 'route_id_encoded', 'time_point_id_encoded'
    ]

    feature_order = categorical_features + numeric_features
    
    # 3. Create purely numeric datasets
    X_train = train_df[feature_order].astype(np.float64)
    y_train = train_df['late'].astype(int)
    X_val = val_df[feature_order].astype(np.float64)
    y_val = val_df['late'].astype(int)

    with mlflow.start_run(run_name="hist_gradient_boosting_v1"):
        model = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, max_leaf_nodes=31, random_state=42)
        print("Fitting HistGradientBoosting model...")
        model.fit(X_train, y_train)

    os.makedirs("models", exist_ok=True)
    # Pack the ord_encoder into the checkpoint so the API can use it
    joblib.dump({"model": model, "encoders": encoders, "ord_encoder": ord_encoder}, "models/latenet.pt")
    print("Successfully exported checkpoint to models/latenet.pt")

if __name__ == "__main__":
    run_tree_training()
