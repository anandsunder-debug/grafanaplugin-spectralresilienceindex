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
