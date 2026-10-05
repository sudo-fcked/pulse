import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score, confusion_matrix, precision_score, recall_score
from features import add_features, fit_target_encoders

def evaluate_final_model():
    print("Unsealing test data...")
    train_raw = pd.read_parquet("data/splits/train.parquet")
    test_raw = pd.read_parquet("data/splits/test.parquet")

    print("Fitting target encoders...")
    encoders = fit_target_encoders(train_raw)
    train_df = add_features(train_raw, target_encoders=encoders)
    test_df = add_features(test_raw, target_encoders=encoders)

    categorical_features = ['direction_id', 'point_type', 'standard_type', 'day_of_week', 'hour']
    numeric_features = [
        'time_point_order', 'scheduled_headway', 'minute_of_day',
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
        'stop_id_encoded', 'route_id_encoded', 'time_point_id_encoded'
    ]
    features = categorical_features + numeric_features

    for col in categorical_features:
        train_df[col] = train_df[col].astype('category')
        test_df[col] = test_df[col].astype('category')

    X_train, y_train = train_df[features], train_df['late'].astype(int)
    X_test, y_test = test_df[features], test_df['late'].astype(int)

    print("Fitting final HGB model...")
    model = HistGradientBoostingClassifier(
        max_iter=200, 
        learning_rate=0.05, 
        max_leaf_nodes=63, 
        random_state=42
    )
    model.fit(X_train, y_train)

    print("Scoring on held-out test split...")
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    test_df['pred_prob'] = probs
    test_df['pred_class'] = preds

    print("\n=== 1. Core Metrics (Threshold = 0.5) ===")
    print(f"Accuracy:  {accuracy_score(y_test, preds):.4f}")
    print(f"AUC-ROC:   {roc_auc_score(y_test, probs):.4f}")
    print(f"PR-AUC:    {average_precision_score(y_test, probs):.4f}")
    print(f"Precision: {precision_score(y_test, preds):.4f}")
    print(f"Recall:    {recall_score(y_test, preds):.4f}")

    print("\n=== 2. Confusion Matrix ===")
    cm = confusion_matrix(y_test, preds)
    print(f"True Negatives:  {cm[0][0]} | False Positives: {cm[0][1]}")
    print(f"False Negatives: {cm[1][0]} | True Positives:  {cm[1][1]}")

    print("\n=== 3. Calibration Check (Hourly) ===")
    hourly = test_df.groupby('hour')[['late', 'pred_prob']].mean()
    hourly.rename(columns={'late': 'Actual Rate', 'pred_prob': 'Predicted Rate'}, inplace=True)
    print(hourly.round(3).head(24))

    print("\n=== 4. Route-Level Sanity Check (Top 5 Predicted Late) ===")
    route_stats = test_df.groupby('route_id')[['late', 'pred_class']].mean()
    route_stats['trip_count'] = test_df.groupby('route_id').size()
    # Filter out routes with tiny sample sizes that skew percentages
    route_stats = route_stats[route_stats['trip_count'] > 500]
    top_routes = route_stats.sort_values('pred_class', ascending=False).head(5)
    top_routes.rename(columns={'late': 'Actual Rate', 'pred_class': 'Predicted Rate'}, inplace=True)
    print(top_routes.round(3))

if __name__ == "__main__":
    evaluate_final_model()
