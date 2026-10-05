import numpy as np
import pandas as pd

def add_features(df, target_encoders=None):
    df = df.copy()
    df['scheduled'] = pd.to_datetime(df['scheduled'])
    
    # Cyclic time encodings
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7.0)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7.0)
    
    # Target encoding for high-cardinality features if training encoder is provided
    if target_encoders is not None:
        global_mean = target_encoders['global_mean']
        for col in ['stop_id', 'route_id', 'time_point_id']:
            mapping = target_encoders[col]
            df[f'{col}_encoded'] = df[col].map(mapping).fillna(global_mean)
    
    return df

def fit_target_encoders(train_df):
    global_mean = train_df['late'].mean()
    encoders = {'global_mean': global_mean}
    
    for col in ['stop_id', 'route_id', 'time_point_id']:
        # Compute mean late rate per category with smoothing
        agg = train_df.groupby(col)['late'].agg(['mean', 'count'])
        smoothing = 10
        encoders[col] = (agg['mean'] * agg['count'] + global_mean * smoothing) / (agg['count'] + smoothing)
        
    return encoders
