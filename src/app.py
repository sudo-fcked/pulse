import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union

app = FastAPI(title="Pulse Reliability Service")

model = None
target_encoders = None

try:
    checkpoint = joblib.load("models/latenet.pt")
    if isinstance(checkpoint, dict):
        model = checkpoint.get("model")
        target_encoders = checkpoint.get("encoders")
    else:
        model = checkpoint
    print("Model loaded successfully.")
except Exception as e:
    print(f"Warning: Could not load model: {e}")

class PredictRequest(BaseModel):
    route_id: str
    direction_id: str
    stop_id: str
    time_point_id: str
    hour: int
    minute_of_day: int
    day_of_week: int
    point_type: Union[str, int]
    standard_type: Union[str, int]
    scheduled_headway: float
    time_point_order: float

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
def predict(payload: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        data = payload.model_dump()

        # 1. Map point_type to expected category strings: ['Endpoint', 'Midpoint', 'Startpoint']
        raw_pt = str(data.get("point_type", "Midpoint")).capitalize()
        point_type_val = raw_pt if raw_pt in ["Endpoint", "Midpoint", "Startpoint"] else "Midpoint"

        # 2. Map standard_type to expected category strings: ['Headway', 'Schedule']
        raw_st = str(data.get("standard_type", "Schedule")).capitalize()
        standard_type_val = raw_st if raw_st in ["Headway", "Schedule"] else "Schedule"

        # 3. Categorical integer features
        dow_val = np.int32(int(data.get("day_of_week", 0)) % 7)
        hour_val = np.int32(int(data.get("hour", 0)) % 24)

        # 4. Numeric continuous features
        dir_str = str(data.get("direction_id", "")).strip().lower()
        direction_val = 1.0 if dir_str in ["inbound", "1", "true"] else 0.0
        time_point_order = float(data.get("time_point_order", 0.0))
        scheduled_headway = float(data.get("scheduled_headway", 0.0))
        minute_of_day = float(data.get("minute_of_day", 0.0))

        # 5. Cyclic features
        hour_sin = float(np.sin(2 * np.pi * float(hour_val) / 24.0))
        hour_cos = float(np.cos(2 * np.pi * float(hour_val) / 24.0))
        dow_sin = float(np.sin(2 * np.pi * float(dow_val) / 7.0))
        dow_cos = float(np.cos(2 * np.pi * float(dow_val) / 7.0))

        # 6. Target encodings
        global_mean = 0.5
        if target_encoders and isinstance(target_encoders, dict):
            global_mean = float(target_encoders.get("global_mean", 0.5))
            stop_encoded = float(target_encoders.get("stop_id", {}).get(str(data.get("stop_id")), global_mean))
            route_encoded = float(target_encoders.get("route_id", {}).get(str(data.get("route_id")), global_mean))
            time_point_encoded = float(target_encoders.get("time_point_id", {}).get(str(data.get("time_point_id")), global_mean))
        else:
            stop_encoded = global_mean
            route_encoded = global_mean
            time_point_encoded = global_mean

        # 7. Construct DataFrame matching model.feature_names_in_ exactly
        df = pd.DataFrame([{
            'point_type': point_type_val,
            'standard_type': standard_type_val,
            'day_of_week': dow_val,
            'hour': hour_val,
            'direction_id': np.float64(direction_val),
            'time_point_order': np.float64(time_point_order),
            'scheduled_headway': np.float64(scheduled_headway),
            'minute_of_day': np.float64(minute_of_day),
            'hour_sin': np.float64(hour_sin),
            'hour_cos': np.float64(hour_cos),
            'dow_sin': np.float64(dow_sin),
            'dow_cos': np.float64(dow_cos),
            'stop_id_encoded': np.float64(stop_encoded),
            'route_id_encoded': np.float64(route_encoded),
            'time_point_id_encoded': np.float64(time_point_encoded)
        }])

        prob = float(model.predict_proba(df)[:, 1][0])
        pred = int(prob >= 0.5)

        return {
            "late_probability": round(prob, 4),
            "is_late": pred
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")
