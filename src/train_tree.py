import os
import yaml
import mlflow
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score
from features import add_features, fit_target_encoders

def run_tree_training():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("pulse_models")

    print("Loading frozen DVC splits...")
    train_raw = pd.read_parquet("data/splits/train.parquet")
    val_raw = pd.read_parquet("data/splits/val.parquet")

    with open("configs/model_hgb.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Fit target encoders on training split to prevent leakage
    print("Fitting target encoders for high-cardinality features...")
    encoders = fit_target_encoders(train_raw)

    train_df = add_features(train_raw, target_encoders=encoders)
    val_df = add_features(val_raw, target_encoders=encoders)

    # Low-cardinality features handled natively by HGB (cardinality <= 255)
    categorical_features = ['direction_id', 'point_type', 'standard_type', 'day_of_week', 'hour']
    
    # High-cardinality and numeric features
    numeric_features = [
        'time_point_order', 'scheduled_headway', 'minute_of_day',
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
        'stop_id_encoded', 'route_id_encoded', 'time_point_id_encoded'
    ]
    
    features = categorical_features + numeric_features

    for col in categorical_features:
        train_df[col] = train_df[col].astype('category')
        val_df[col] = val_df[col].astype('category')

    X_train = train_df[features]
    y_train = train_df['late'].astype(int)
    X_val = val_df[features]
    y_val = val_df['late'].astype(int)

    with mlflow.start_run(run_name="hist_gradient_boosting_v1"):
        mlflow.log_params({
            "model_type": config['model_type'],
            "max_iter": config['max_iter'],
            "learning_rate": config['learning_rate'],
            "max_leaf_nodes": config['max_leaf_nodes']
        })
        mlflow.log_artifact("configs/model_hgb.yaml")

        model = HistGradientBoostingClassifier(
            max_iter=config['max_iter'],
            learning_rate=config['learning_rate'],
            max_leaf_nodes=config['max_leaf_nodes'],
            random_state=42
        )

        print("Fitting HistGradientBoosting model...")
        model.fit(X_train, y_train)

        probs = model.predict_proba(X_val)[:, 1]
        preds = model.predict(X_val)

        acc = accuracy_score(y_val, preds)
        auc = roc_auc_score(y_val, probs)
        pr_auc = average_precision_score(y_val, probs)

        mlflow.log_metrics({"accuracy": acc, "roc_auc": auc, "pr_auc": pr_auc})
        print(f"HGB Validation Results -> Accuracy: {acc:.4f}, AUC: {auc:.4f}, PR-AUC: {pr_auc:.4f}")

    # Export runs
    runs_df = mlflow.search_runs(experiment_names=["pulse_models"])
    runs_df.to_csv("mlflow_runs.csv", index=False)
    print("Exported updated experiment history to mlflow_runs.csv")

if __name__ == "__main__":
    run_tree_training()
