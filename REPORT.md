# Pulse Model Delivery Report

## 1. Data
- Months used, row counts before/after cleaning:
  - Months used: April 2026, May 2026, June 2026
  - April 2026: 2,459,855 raw -> 2,318,543 cleaned (141,312 dropped)
  - May 2026: 2,484,472 raw -> 2,329,861 cleaned (154,611 dropped)
  - June 2026: 2,488,436 raw -> 2,330,999 cleaned (157,437 dropped)
  - Total historical: 7,432,763 raw -> 6,974,208 unique rows inserted into Postgres stop_events
  - Daily pull runs:
    - Day 1 (2026-09-24): 117,420 fetched | 33,654 kept | 33,568 inserted
    - Day 2 (2026-09-25): 117,420 fetched | 33,654 kept | 33,568 inserted
- Late-rate by split (train/val/test): train: 45.74%, val: 49.23%, test: 43.31%
  - train: 45.74%
  - val: 49.23%
  - test: 43.31%
- DVC data version (md5) for each split:
  - train: 2af23255df1bacc3c6c40d5c2ee9e6a6
  - val: 1e17fa5d90ad6f1818f99cc2e7c702ca
  - test: 36e6c3b1baf1ea94317ee09b596fad3f
  - data/splits/train.parquet.dvc: 2af23255df1bacc3c6c40d5c2ee9e6a6
  - data/splits/val.parquet.dvc: 1e17fa5d90ad6f1818f99cc2e7c702ca
  - data/splits/test.parquet.dvc: 36e6c3b1baf1ea94317ee09b596fad3f

## 2. Baselines
- Majority-class: accuracy = 0.5077, AUC = 0.5000, PR-AUC = 0.4923
- Logistic regression: accuracy = 0.6414, AUC = 0.6975, PR-AUC = 0.6692
- What the baselines tell us about the problem:
  The validation split has a late rate of 49.23%, making the classes nearly balanced. A majority-class baseline that constantly predicts the dominant training class ("not late") yields 50.77% accuracy and an AUC of 0.5000. Logistic Regression fitted on one-hot encoded route, stop, time, and headway features lifts accuracy to 64.14% (+13.37 points) and AUC to 0.6975 (PR-AUC 0.6692). This performance gap proves that schedule topology, stop sequence, and calendar features carry meaningful predictive signal for bus lateness, setting the benchmark for tree-based models in Task 3.

## 3. Model Development

## 4. Final Evaluation (held-out test weeks)

## 5. Threshold Recommendation

## 6. Reproducibility

## 7. Limitations & Next Steps
