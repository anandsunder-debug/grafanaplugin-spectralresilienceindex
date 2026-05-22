from pathlib import Path
import json
import textwrap

plugin_id = "anandsunder-sri-datasource"
plugin_name = "SRI Infra Datasource"
root = Path("grafana-sri-plugin")
src = root / "src"
backend = root / "python_backend"

files = {
    root / "package.json": json.dumps({
        "name": plugin_id,
        "version": "0.0.1",
        "private": True,
        "scripts": {
            "build": "grafana-toolkit plugin:build",
            "dev": "grafana-toolkit plugin:dev",
            "test": "grafana-toolkit plugin:test"
        },
        "devDependencies": {
            "@grafana/data": "latest",
            "@grafana/runtime": "latest",
            "@grafana/toolkit": "latest",
            "@grafana/ui": "latest",
            "typescript": "^5.4.0"
        }
    }, indent=2),

    src / "plugin.json": json.dumps({
        "type": "datasource",
        "name": plugin_name,
        "id": plugin_id,
        "metrics": True,
        "info": {
            "description": "Grafana datasource for computing Spectral Resilience Index from infrastructure metrics",
            "author": {"name": "Anand Sunder"},
            "keywords": ["sri", "resilience", "infra", "observability"],
            "logos": {"small": "img/logo.svg", "large": "img/logo.svg"},
            "version": "0.0.1",
            "updated": "2026-05-22"
        },
        "dependencies": {
            "grafanaDependency": ">=10.0.0",
            "plugins": []
        }
    }, indent=2),

    src / "types.ts": textwrap.dedent("""
        export interface MyQuery {
          refId: string;
          intervalMs?: number;
          maxDataPoints?: number;
          target?: string;
          promUrl?: string;
          cpuQuery?: string;
          memoryQuery?: string;
          latencyQuery?: string;
          errorRateQuery?: string;
          restartQuery?: string;
          availabilityQuery?: string;
        }

        export interface MyDataSourceOptions {
          url?: string;
        }

        export const defaultQuery: Partial<MyQuery> = {
          cpuQuery: 'avg(rate(node_cpu_seconds_total{mode!="idle"}[5m]))',
          memoryQuery: '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))',
          latencyQuery: 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))',
          errorRateQuery: 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))',
          restartQuery: 'sum(increase(kube_pod_container_status_restarts_total[15m]))',
          availabilityQuery: 'avg(up)'
        };
    """),

    src / "module.ts": textwrap.dedent("""
        import { DataSourcePlugin } from '@grafana/data';
        import { DataSource } from './datasource';
        import { ConfigEditor } from './ConfigEditor';
        import { QueryEditor } from './QueryEditor';
        import { MyDataSourceOptions, MyQuery } from './types';

        export const plugin = new DataSourcePlugin<DataSource, MyQuery, MyDataSourceOptions>(DataSource)
          .setConfigEditor(ConfigEditor)
          .setQueryEditor(QueryEditor);
    """),

    src / "datasource.ts": textwrap.dedent("""
        import {
          DataQueryRequest,
          DataQueryResponse,
          DataSourceApi,
          DataSourceInstanceSettings,
          MutableDataFrame,
          FieldType
        } from '@grafana/data';
        import { MyDataSourceOptions, MyQuery, defaultQuery } from './types';

        export class DataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {
          url?: string;

          constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {
            super(instanceSettings);
            this.url = instanceSettings.jsonData.url;
          }

          getDefaultQuery(_: CoreApp): Partial<MyQuery> {
            return defaultQuery;
          }

          async query(options: DataQueryRequest<MyQuery>): Promise<DataQueryResponse> {
            const q = options.targets[0];
            const res = await fetch(`${this.url}/sri`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                from: options.range.from.toISOString(),
                to: options.range.to.toISOString(),
                stepMs: options.intervalMs,
                promUrl: q.promUrl,
                cpuQuery: q.cpuQuery,
                memoryQuery: q.memoryQuery,
                latencyQuery: q.latencyQuery,
                errorRateQuery: q.errorRateQuery,
                restartQuery: q.restartQuery,
                availabilityQuery: q.availabilityQuery
              })
            });

            const data = await res.json();

            const frame = new MutableDataFrame({
              refId: q.refId,
              fields: [
                { name: 'time', type: FieldType.time },
                { name: 'SRI', type: FieldType.number }
              ]
            });

            for (const point of data.series) {
              frame.add({
                time: point.time,
                SRI: point.sri
              });
            }

            return { data: [frame] };
          }

          async testDatasource() {
            return { status: 'success', message: 'SRI datasource is working', title: 'Success' };
          }
        }
    """),

    src / "ConfigEditor.tsx": textwrap.dedent("""
        import React from 'react';
        import { InlineField, Input } from '@grafana/ui';

        export function ConfigEditor(props: any) {
          const { onOptionsChange, options } = props;
          const { jsonData } = options;

          return (
            <div>
              <InlineField label="Backend URL" labelWidth={20}>
                <Input
                  width={40}
                  value={jsonData.url || 'http://localhost:8000'}
                  onChange={(e) =>
                    onOptionsChange({
                      ...options,
                      jsonData: { ...jsonData, url: e.currentTarget.value },
                    })
                  }
                />
              </InlineField>
            </div>
          );
        }
    """),

    src / "QueryEditor.tsx": textwrap.dedent("""
        import React from 'react';
        import { InlineField, Input } from '@grafana/ui';

        export function QueryEditor(props: any) {
          const { query, onChange, onRunQuery } = props;

          const update = (key: string, value: string) => {
            onChange({ ...query, [key]: value });
            onRunQuery();
          };

          return (
            <div>
              <InlineField label="Prometheus URL" labelWidth={20}>
                <Input value={query.promUrl || 'http://localhost:9090'} onChange={(e) => update('promUrl', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="CPU Query" labelWidth={20}>
                <Input value={query.cpuQuery || ''} onChange={(e) => update('cpuQuery', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="Memory Query" labelWidth={20}>
                <Input value={query.memoryQuery || ''} onChange={(e) => update('memoryQuery', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="Latency Query" labelWidth={20}>
                <Input value={query.latencyQuery || ''} onChange={(e) => update('latencyQuery', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="Error Rate Query" labelWidth={20}>
                <Input value={query.errorRateQuery || ''} onChange={(e) => update('errorRateQuery', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="Restart Query" labelWidth={20}>
                <Input value={query.restartQuery || ''} onChange={(e) => update('restartQuery', e.currentTarget.value)} />
              </InlineField>
              <InlineField label="Availability Query" labelWidth={20}>
                <Input value={query.availabilityQuery || ''} onChange={(e) => update('availabilityQuery', e.currentTarget.value)} />
              </InlineField>
            </div>
          );
        }
    """),

    backend / "requirements.txt": textwrap.dedent("""
        fastapi
        uvicorn
        requests
        numpy
    """),

    backend / "main.py": textwrap.dedent("""
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
    """),

    root / "README.md": textwrap.dedent(f"""
        # {plugin_name}

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
    """)
}

for path, content in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

print(f"Generated plugin skeleton at: {root.resolve()}")
