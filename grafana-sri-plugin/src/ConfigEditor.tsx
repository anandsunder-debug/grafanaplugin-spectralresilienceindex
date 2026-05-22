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
