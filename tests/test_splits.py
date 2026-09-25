import os
import pandas as pd

def test_split_files_exist():
    assert os.path.exists("data/splits/train.parquet")
    assert os.path.exists("data/splits/val.parquet")
    assert os.path.exists("data/splits/test.parquet")

def test_splits_temporal_isolation():
    train = pd.read_parquet("data/splits/train.parquet")
    val = pd.read_parquet("data/splits/val.parquet")
    test = pd.read_parquet("data/splits/test.parquet")
    
    assert pd.to_datetime(train["scheduled"]).max() < pd.to_datetime(val["scheduled"]).min(), "Train overlaps with Val"
    assert pd.to_datetime(val["scheduled"]).max() < pd.to_datetime(test["scheduled"]).min(), "Val overlaps with Test"

def test_no_target_leakage_in_features():
    train = pd.read_parquet("data/splits/train.parquet")
    forbidden = ["actual", "delay_min"]
    for col in forbidden:
        assert col not in train.columns, f"Forbidden column {col} found in features!"
