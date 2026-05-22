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

  getDefaultQuery(_: any): Partial<MyQuery> {
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
