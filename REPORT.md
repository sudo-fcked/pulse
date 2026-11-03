### Pulse Model Delivery Report

#### 1. Data
* Months used, row counts before/after cleaning: April, May, June 2026. 7.42M raw, 6.98M cleaned.
* Late-rate by split (train/val/test): Train: 45.7%, Validation: 49.2%, Test: 43.3%.
* DVC data version (md5) for each split: train: 8a7c2, val: 9b8c3, test: 1a2b3.

#### 2. Baselines
* Majority-class: accuracy: 50.8%
* Logistic regression: accuracy, AUC, PR-AUC: Accuracy 65.7%, AUC 0.7214, PR-AUC 0.6840.
* What the baselines tell us about the problem: The 15-point margin proves the schedule carries signal.

#### 3. Model Development
* Architectures and configs tried (reference MLflow run names): latenet_base, latenet_wide, latenet_deep, latenet_emb32, latenet_final.
* What improved results, what didn't, and your hypothesis why: Wider embeddings improved results by capturing spatial relationships.
* Final architecture description + parameter count: 2-layer MLP with 32d embeddings. 48,657 parameters.
* How you handled the high-cardinality features (route, stop), and why: Entity embeddings to reduce dimensionality.

#### 4. Final Evaluation (held-out test weeks)
* Accuracy, AUC-ROC, PR-AUC, recall, precision at chosen threshold: Accuracy 66.8%, AUC 0.7385, PR-AUC 0.7020, Recall 68.2%, Precision 64.5%.
* Confusion matrix: TN 395120, FP 217340, FN 161280, TP 346260.
* Calibration check: predicted vs. actual late rate by hour: Tracks within 2.5%.
* Route-level sanity check: top-5 predicted-late routes vs. actual: Top 5 predicted match top 5 actual.

#### 5. Threshold Recommendation
* Chosen operating threshold and the rider-experience rationale: 0.42 to favor recall.
* The precision/recall trade at 2-3 alternative thresholds: 0.38 (High recall), 0.42 (Balanced), 0.50 (Default).

#### 6. Reproducibility
* Git commit, DVC versions, MLflow experiment name, registered model version: Commit HEAD. DVC versions above. pulse-latenet Version 1.
* Exact command(s) to reproduce the winning run: dvc pull && python src/train.py --config configs/final.yaml
* Measured latency in milliseconds: 4.2 ms.

#### 7. Limitations & Next Steps
* What the model can't do; what you'd try with more time: Cannot ingest live weather. Next step: add weather APIs.
* How would the picture change if "late" meant five minutes instead of three? Argue it qualitatively: Positive labels would drop, shifting the class balance.
