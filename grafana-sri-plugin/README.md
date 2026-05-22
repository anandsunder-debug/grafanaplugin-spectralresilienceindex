# SRI Infra Datasource

This plugin computes Spectral Resilience Index (SRI) from infrastructure metrics.

## Structure
- `src/`: Grafana datasource plugin frontend
- `python_backend/`: Python API that fetches Prometheus metrics and computes SRI

## Run backend
```bash
cd python_backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run plugin
```bash
npm install
npm run dev
```

## Example metrics
- CPU utilization
- Memory utilization
- P95 latency
- Error rate
- Restart count
- Availability

## Notes
The current SRI formula uses normalized infra metrics, covariance eigenvalues, and a composite stability score. You can replace this with your preferred FEM- or spectral-based formulation.
