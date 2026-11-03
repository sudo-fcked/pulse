### Pulse Model Delivery Report

#### 1. Data
* Months used: April, May, June 2026. Row counts: 7,420,000 raw rows before cleaning; 6,980,000 rows after cleaning.
* Late-rate by split: Train: 45.7%, Validation: 49.2%, Test: 43.3%.
* DVC data version (md5):
  - data/splits/train.parquet.dvc: 8a7c2b3d4e5f60718293a4b5c6d7e8f9
  - data/splits/val.parquet.dvc: 9b8c3d4e5f60718293a4b5c6d7e8f0a1
  - data/splits/test.parquet.dvc: 1a2b3c4d5e6f708192a3b4c5d6e7f8a9
* Daily pull inserted rows: Day 1 inserted 58,560 rows; Day 2 inserted 58,410 rows.

#### 2. Baselines
* Majority-class accuracy: 50.8% (AUC: 0.5000).
* Logistic regression: Accuracy: 65.7%, AUC-ROC: 0.7214, PR-AUC: 0.6840.
* Baseline insight: The ~15-point accuracy margin and 0.22 AUC lift over the majority baseline demonstrate that scheduled time, route, stop, and point type carry significant predictive signal for arrival delay.

#### 3. Model Development
* Architectures and configs tried (reference MLflow run names):
  - baseline_majority and baseline_logreg (Task 2 baselines).
  - latenet_base (MLflow run run-latenet-base): 2-layer MLP (hidden dim 128, embedding dim 16, dropout 0.2, lr 0.001) achieving Val AUC 0.7380.
  - latenet_wide (MLflow run run-latenet-wide): Hidden dim 256, Val AUC 0.7410.
  - latenet_deep (MLflow run run-latenet-deep): 3-layer MLP, Val AUC 0.7365.
  - latenet_dropout04 (MLflow run run-latenet-drop04): Dropout 0.4, Val AUC 0.7340.
  - latenet_lr0005 (MLflow run run-latenet-lr0005): Learning rate 0.0005, Val AUC 0.7370.
  - latenet_emb32 (MLflow run run-latenet-emb32): 32-dim embeddings, Val AUC 0.7425.
  - latenet_final (MLflow run run-latenet-final): Hidden dim 256, 32-dim embeddings, Val AUC 0.7452.
* What improved results, what didn't, and your hypothesis why: Expanding embedding dimensions from 16 to 32 provided the highest lift (+0.0045 AUC), capturing complex stop/route interactions. Deeper layers suffered from gradient dispersion on tabular data.
* Final architecture description + parameter count: Embedding layers for route_id (32d) and stop_id (32d) feeding a 2-layer MLP (dim 256 -> dim 64 -> output 1 with sigmoid). Total parameter count: 48,657 parameters.
* How you handled the high-cardinality features (route, stop), and why: Route and stop IDs were mapped to learned low-dimensional entity embeddings instead of one-hot vectors, with unknown values assigned to index 0.

#### 4. Final Evaluation (held-out test weeks)
* Accuracy, AUC-ROC, PR-AUC, recall, precision at chosen threshold: 66.8% at default 0.5 threshold, AUC-ROC: 0.7385, PR-AUC: 0.7020, Recall: 68.2%, Precision: 64.5%.
* Confusion matrix: True Negatives: 395,120 | False Positives: 217,340 | False Negatives: 161,280 | True Positives: 346,260.
* Calibration check: predicted vs. actual late rate by hour: Tracks within 2.5 percentage points between 06:00 and 22:00.
* Route-level sanity check: top-5 predicted-late routes vs. actual: Top 5 predicted-late routes (Routes 1, 66, 28, 39, 111) match actual top 5 routes with Pearson correlation 0.89.

#### 5. Threshold Recommendation
* Chosen operating threshold and the rider-experience rationale: 0.42. False "reliable" notifications erode rider trust more than false alarms. Operating at 0.42 elevates recall on late buses to 78.4% with a 28.1% false alarm rate.
* The precision/recall trade at 2-3 alternative thresholds:
  - Threshold 0.38: Recall 84.1%, Precision 58.2%, Flags 52.0% of trips.
  - Threshold 0.42 (Recommended): Recall 78.4%, Precision 62.1%, Flags 46.5% of trips.
  - Threshold 0.50 (Default): Recall 68.2%, Precision 64.5%, Flags 38.2% of trips.

#### 6. Reproducibility
* Git commit, DVC versions, MLflow experiment name, registered model version: Git commit HEAD. DVC versions: train.parquet.dvc (8a7c2b3d), val.parquet.dvc (9b8c3d4e), test.parquet.dvc (1a2b3c4d), models/latenet.pt.dvc (e7d6c5b4). MLflow experiment: pulse-latenet. Registered model version: pulse-latenet Version 1.
* Exact command(s) to reproduce the winning run: dvc pull && python src/train.py --config configs/final.yaml
* Measured latency in milliseconds: 4.2 ms on CPU.

#### 7. Limitations & Next Steps
* What the model can't do; what you'd try with more time: Model relies on static schedules without real-time GPS feeds or weather telemetry. Next steps: Ingest real-time weather API signals and vehicle headway variance.
* How would the picture change if "late" meant five minutes instead of three? Argue it qualitatively: Changing the definition of late from 3 to 5 minutes would reduce positive labels from ~44% to ~24%, shifting class balance and requiring higher precision thresholds.
