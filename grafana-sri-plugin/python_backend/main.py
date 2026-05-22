from fastapi import FastAPI
from pydantic import BaseModel
import requests
import numpy as np

app = FastAPI()

class SriRequest(BaseModel):
    from_: str = None
    to: str
    stepMs: int | None = 60000
    promUrl: str
    cpuQuery: str
    memoryQuery: str
    latencyQuery: str
    errorRateQuery: str
    restartQuery: str
    availabilityQuery: str

    class Config:
        fields = {'from_': 'from'}

def query_prometheus_range(base_url, query, start, end, step_seconds):
    resp = requests.get(
        f"{base_url}/api/v1/query_range",
        params={
            "query": query,
            "start": start,
            "end": end,
            "step": step_seconds
        },
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()["data"]["result"]
    if not data:
        return []
    return data[0]["values"]

def normalize_inverse(values, cap=1.0):
    arr = np.array(values, dtype=float)
    arr = np.clip(arr, 0, cap)
    return 1.0 - (arr / cap)

def normalize_direct(values, cap=1.0):
    arr = np.array(values, dtype=float)
    arr = np.clip(arr, 0, cap)
    return arr / cap

def compute_sri(cpu, mem, latency, err, restarts, avail):
    cpu_n = normalize_inverse(cpu, cap=1.0)
    mem_n = normalize_inverse(mem, cap=1.0)
    lat_n = normalize_inverse(latency, cap=max(max(latency), 1))
    err_n = normalize_inverse(err, cap=max(max(err), 0.01))
    rst_n = normalize_inverse(restarts, cap=max(max(restarts), 1))
    avl_n = normalize_direct(avail, cap=1.0)

    M = np.vstack([cpu_n, mem_n, lat_n, err_n, rst_n, avl_n]).T
    cov = np.cov(M, rowvar=False)
    eigvals = np.linalg.eigvalsh(cov + 1e-9 * np.eye(cov.shape[0]))
    sri = float(np.min(eigvals) / np.max(eigvals))
    composite = np.mean(M, axis=1)

    return np.clip(composite * sri, 0, 1)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/sri")
def sri(req: SriRequest):
    step_seconds = max(int((req.stepMs or 60000) / 1000), 15)

    cpu = query_prometheus_range(req.promUrl, req.cpuQuery, req.from_, req.to, step_seconds)
    mem = query_prometheus_range(req.promUrl, req.memoryQuery, req.from_, req.to, step_seconds)
    lat = query_prometheus_range(req.promUrl, req.latencyQuery, req.from_, req.to, step_seconds)
    err = query_prometheus_range(req.promUrl, req.errorRateQuery, req.from_, req.to, step_seconds)
    rst = query_prometheus_range(req.promUrl, req.restartQuery, req.from_, req.to, step_seconds)
    avl = query_prometheus_range(req.promUrl, req.availabilityQuery, req.from_, req.to, step_seconds)

    min_len = min(len(cpu), len(mem), len(lat), len(err), len(rst), len(avl))
    cpu = cpu[:min_len]
    mem = mem[:min_len]
    lat = lat[:min_len]
    err = err[:min_len]
    rst = rst[:min_len]
    avl = avl[:min_len]

    timestamps = [int(float(x[0]) * 1000) for x in cpu]
    cpu_v = [float(x[1]) for x in cpu]
    mem_v = [float(x[1]) for x in mem]
    lat_v = [float(x[1]) for x in lat]
    err_v = [float(x[1]) for x in err]
    rst_v = [float(x[1]) for x in rst]
    avl_v = [float(x[1]) for x in avl]

    sri_values = compute_sri(cpu_v, mem_v, lat_v, err_v, rst_v, avl_v)

    return {
        "series": [
            {"time": ts, "sri": float(val)}
            for ts, val in zip(timestamps, sri_values)
        ]
    }
