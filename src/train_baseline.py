import os
import subprocess
import yaml
import mlflow
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")
    except Exception:
        return "unknown"

def run_baselines():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("pulse_baselines")

    train_df = pd.read_parquet("data/splits/train.parquet")
    val_df = pd.read_parquet("data/splits/val.parquet")

    git_commit = get_git_commit()

    dvc_hashes = {}
    for split in ["train", "val", "test"]:
        dvc_file = f"data/splits/{split}.parquet.dvc"
        if os.path.exists(dvc_file):
            with open(dvc_file, "r") as f:
                content = yaml.safe_load(f)
                dvc_hashes[split] = content.get("outs", [{}])[0].get("md5", "unknown")

    categorical_features = ['route_id', 'direction_id', 'stop_id', 'time_point_id', 'point_type', 'standard_type', 'day_of_week', 'hour']
    numeric_features = ['time_point_order', 'scheduled_headway', 'minute_of_day']

    # 1. Majority Class Baseline
    with open("configs/baseline_majority.yaml", "r") as f:
        config_maj = yaml.safe_load(f)

    with mlflow.start_run(run_name="baseline_majority_class"):
        mlflow.log_params({
            "model_type": "majority_class",
            "git_commit": git_commit,
            "train_dvc_md5": dvc_hashes.get("train", "unknown"),
            "val_dvc_md5": dvc_hashes.get("val", "unknown")
        })
        mlflow.log_artifact("configs/baseline_majority.yaml")

        majority_class = train_df['late'].mode()[0]
        preds = [majority_class] * len(val_df)

        acc = accuracy_score(val_df['late'], preds)
        auc = 0.5
        pr_auc = float(val_df['late'].mean())

        mlflow.log_metrics({"accuracy": acc, "roc_auc": auc, "pr_auc": pr_auc})
        print(f"Majority Baseline -> Accuracy: {acc:.4f}, AUC: {auc:.4f}, PR-AUC: {pr_auc:.4f}")

    # 2. Logistic Regression Baseline
    with open("configs/baseline_logreg.yaml", "r") as f:
        config_lr = yaml.safe_load(f)

    with mlflow.start_run(run_name="baseline_logistic_regression"):
        mlflow.log_params({
            "model_type": "logistic_regression",
            "C": config_lr['C'],
            "max_iter": config_lr['max_iter'],
            "solver": config_lr['solver'],
            "git_commit": git_commit,
            "train_dvc_md5": dvc_hashes.get("train", "unknown"),
            "val_dvc_md5": dvc_hashes.get("val", "unknown")
        })
        mlflow.log_artifact("configs/baseline_logreg.yaml")

        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', categorical_transformer, categorical_features),
                ('num', numeric_transformer, numeric_features)
            ]
        )

        model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(
                C=float(config_lr['C']),
                max_iter=int(config_lr['max_iter']),
                solver=config_lr['solver']
            ))
        ])

        features = categorical_features + numeric_features
        X_train = train_df[features]
        y_train = train_df['late'].astype(int)
        X_val = val_df[features]
        y_val = val_df['late'].astype(int)

        print("Fitting Logistic Regression baseline...")
        model.fit(X_train, y_train)

        probs = model.predict_proba(X_val)[:, 1]
        preds = model.predict(X_val)

        acc = accuracy_score(y_val, preds)
        auc = roc_auc_score(y_val, probs)
        pr_auc = average_precision_score(y_val, probs)

        mlflow.log_metrics({"accuracy": acc, "roc_auc": auc, "pr_auc": pr_auc})
        print(f"Logistic Regression -> Accuracy: {acc:.4f}, AUC: {auc:.4f}, PR-AUC: {pr_auc:.4f}")

    # Export runs to mlflow_runs.csv
    runs_df = mlflow.search_runs(experiment_names=["pulse_baselines"])
    runs_df.to_csv("mlflow_runs.csv", index=False)
    print("Exported MLflow run history to mlflow_runs.csv")

if __name__ == "__main__":
    run_baselines()
