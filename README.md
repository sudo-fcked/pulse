# Pulse Model & API

## Overview
Machine learning model and production serving API for the MBTA bus reliability prediction service.

## Setup & Reproduction
1. Clone the repository:
   ```bash
   git clone [https://github.com/sudo-fcked/pulse-api.git](https://github.com/sudo-fcked/pulse-api.git)
   cd pulse-api
   ```
2. Pull DVC-tracked model artifacts and frozen datasets:
   ```bash
   dvc pull
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run inference latency check:
   ```bash
   python src/latency_check.py
   ```
5. Deploy multi-replica cluster with OpenTofu:
   ```bash
   tofu init
   tofu apply -auto-approve
   ```
