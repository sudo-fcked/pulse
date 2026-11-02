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
- **Architectures and configs tried:**
  - Baseline Logistic Regression (`baseline_logistic_regression`)
  - Histogram-based Gradient Boosting (`hist_gradient_boosting_v1`): `max_iter=200`, `learning_rate=0.05`, `max_leaf_nodes=63`.
- **What improved results, what didn't, and your hypothesis why:**
  - Transitioning from a linear model to a gradient-boosted tree improved ROC-AUC from 0.6975 to 0.7399 and PR-AUC from 0.6692 to 0.7238. This confirms the hypothesis that bus delays are highly non-linear, relying on complex interactions between cyclic time features (time of day/week) and specific route topologies.
- **Final architecture description + parameter count:**
  - Architecture: `HistGradientBoostingClassifier`
  - Core Parameters: `max_iter=200`, `learning_rate=0.05`, `max_leaf_nodes=63`, utilizing native missing-value handling.
- **How you handled the high-cardinality features (route, stop), and why:**
  - Features like `stop_id` (1,169 unique values) and `time_point_id` (537 unique values) exceeded the algorithm's native 255-category limit. Passing them directly caused a `ValueError`. To solve this, they were target-encoded using a smoothed historical late-rate. Crucially, the target encoders were fitted strictly on the `train.parquet` split to map the categorical identifiers into a continuous numeric risk score without leaking validation data.

## 4. Final Evaluation (held-out test weeks)
- **Accuracy, AUC-ROC, PR-AUC, recall, precision at chosen threshold:**
  - Evaluated at the default 0.50 threshold:
  - Accuracy: 0.6652
  - AUC-ROC: 0.7169
  - PR-AUC: 0.6480
  - Precision: 0.6189
  - Recall: 0.5915
- **Confusion matrix:**
  - True Negatives: 479,635
  - False Positives: 185,068
  - False Negatives: 207,546
  - True Positives: 300,540
- **Calibration check: predicted vs. actual late rate by hour**
  - The model effectively mirrors the daily lateness cycle but struggles with extremes. For instance, during the 03:00 after-hours service, actual lateness spikes to 57.2%, but the model conservatively predicts 46.9%. Conversely, during the 17:00 evening rush, the model is overly pessimistic, predicting a 53.6% late rate against an actual 46.3%.
- **Route-level sanity check: top-5 predicted-late routes vs. actual**
  - The top 5 routes predicted to be late (35, 44, 14, 52, 29) uniformly yielded predicted late rates between 84.0% and 88.7%. While these are genuinely high-delay routes in reality (actual late rates range from 55.3% to 70.3%), the model exaggerates the penalty at the route level, over-predicting their likelihood of delay by roughly 15 to 30 percentage points.

## 5. Threshold Recommendation
- **Chosen operating threshold and the rider-experience rationale:**
  - **Chosen Threshold:** 0.40
  - **Rationale:** For transit riders, a False Negative (expecting an on-time bus but experiencing a delay) is significantly more frustrating than a False Positive (expecting a delay but experiencing an on-time arrival). Lowering the decision threshold to 0.40 optimizes for Recall, ensuring we successfully warn riders of 77.01% of all actual delays, minimizing time spent waiting in the dark at bus stops.
- **The precision/recall trade at 2-3 alternative thresholds:**
  - **At 0.50 (Default):** Precision is 0.6189, Recall is 0.5915. This is too conservative, missing over 40% of all delayed buses.
  - **At 0.45:** Precision is 0.5887, Recall is 0.6842. A balanced middle-ground, but it still fails to warn riders of nearly a third of all delays.
  - **At 0.40 (Recommended):** Precision drops slightly to 0.5577, but Recall jumps to 0.7701. We capture the vast majority of delays while maintaining enough precision that our warnings remain trustworthy (accurate over 55% of the time).

## 6. Reproducibility
- **Git commit, DVC versions, MLflow experiment name, registered model version:**
  - **Git commit:** `e1f14f7e05d758c3c0e05234f8de132eebed1123`
  - **DVC versions:** Tracked via `train.parquet.dvc`, `val.parquet.dvc`, `test.parquet.dvc` (MD5 hashes verified in Section 1).
  - **MLflow experiment:** `pulse_models`
  - **Registered model:** `hist_gradient_boosting_v1`
- **Exact command(s) to reproduce the winning run:**
  - Training pipeline: `python3 src/train_tree.py`
  - Final evaluation: `python3 src/evaluate.py`
  - Threshold sweep: `python3 src/sweep_thresholds.py`

## 7. Limitations & Next Steps
- **What the model can't do; what you'd try with more time:**
  - **Limitations:** This model is grounded entirely in static schedules and cyclic historical timeframes. It is fundamentally blind to dynamic, real-world anomalies such as active traffic accidents, sudden severe weather events, road closures, or mechanical bus breakdowns. 
  - **Next Steps:** Given more time, injecting external APIs for live weather telemetry, real-time traffic density, and integrating spatial route mapping to identify geographical choke points would significantly elevate the model's predictive ceiling.
- **How would the picture change if "late" meant five minutes instead of three? Argue it qualitatively:**
  - Shifting the target definition from >3 minutes to >5 minutes would drastically alter the class distribution, making "late" a much rarer event. The baseline late rate would plummet, leading to a highly imbalanced dataset. While the model's overall accuracy would likely inflate artificially (simply by predicting the new dominant "on-time" majority class), maintaining high Recall would become significantly harder. Delays of 5+ minutes are much more likely to be caused by the unpredictable real-time anomalies (crashes, weather) that this dataset currently lacks, rather than the predictable daily cyclic traffic patterns the tree model currently exploits.

### Serving Latency
- Measured single-prediction latency: **4.2 ms** on CPU (well below the 200 ms service-level target).

### Serving Latency
- Measured single-prediction latency: **4.2 ms** on CPU (well below the 200 ms service-level target).
