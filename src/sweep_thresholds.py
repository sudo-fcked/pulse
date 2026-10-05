import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score
from features import add_features, fit_target_encoders

def sweep():
    print("Loading data and fitting model for threshold sweep...")
    train_raw = pd.read_parquet("data/splits/train.parquet")
    test_raw = pd.read_parquet("data/splits/test.parquet")
    
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

    model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=63, random_state=42)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]

    print(f"\n{'Threshold':<10} | {'Precision':<10} | {'Recall':<10}")
    print("-" * 35)
    for t in [0.40, 0.45, 0.50, 0.55, 0.60]:
        preds = (probs >= t).astype(int)
        p = precision_score(y_test, preds)
        r = recall_score(y_test, preds)
        print(f"{t:<10.2f} | {p:<10.4f} | {r:<10.4f}")

if __name__ == "__main__":
    sweep()
