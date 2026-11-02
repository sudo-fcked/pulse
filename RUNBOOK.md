# Pulse API Runbook

## Service Architecture
- 2x API replicas (`pulse-api-1`, `pulse-api-2`) running FastAPI on internal port 8000.
- Nginx reverse proxy load-balancing requests on external port 8080.

## Commands
- **Start (Compose):** `docker compose up -d`
- **Stop (Compose):** `docker compose down`
- **Health Check:** `curl -s http://localhost:8080/health`
- **Inference Check:** Send POST to `http://localhost:8080/predict`
- **OpenTofu Deploy:** `tofu init && tofu apply -auto-approve`
- **OpenTofu Destroy:** `tofu destroy -auto-approve`
