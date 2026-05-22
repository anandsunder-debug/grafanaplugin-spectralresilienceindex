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
