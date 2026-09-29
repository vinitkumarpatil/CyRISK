// ML Model card — documents the genuine scikit-learn model and how it is fused
// with the actuarial formulas (hybrid), with feature importances and metrics.

import { useApi } from '../lib/useApi'
import { BrainCircuit } from 'lucide-react'
import {
  Loading, ErrorState, CardPad, SectionTitle, Disclaimer, StatCard, ProgressBar,
} from '../components/ui'
import { pct } from '../lib/format'

interface ModelResp {
  algorithm: string; purpose: string; metrics: Record<string, any>
  feature_importances: { feature: string; importance: number; description: string }[]
  features: string[]; training: { seed: number; data: string } | Record<string, any>
  hybrid_note: string; disclaimer: string
}

export default function ModelCard() {
  const { data, loading, error, reload } = useApi<ModelResp>('/api/model', { refreshOnTelemetry: true })
  if (loading) return <Loading label="Loading model card…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  const imps = [...(data.feature_importances ?? [])].sort((a, b) => b.importance - a.importance)

  return (
    <div className="space-y-6">
      <SectionTitle title="Incident Likelihood Model" subtitle={data.purpose} />

      <CardPad>
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand-gradient shadow-glow"><BrainCircuit className="h-6 w-6 text-white" /></div>
          <div>
            <div className="text-lg font-semibold text-fg">{data.algorithm}</div>
            <div className="text-sm text-subtle">scikit-learn · {data.features?.length ?? 0} features · seed {(data.training as any)?.seed ?? '—'}</div>
          </div>
        </div>
      </CardPad>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Object.entries(data.metrics).map(([k, v]) => (
          <StatCard key={k} label={k.replace(/_/g, ' ')} value={typeof v === 'number' ? (v as number).toFixed(3) : String(v)} />
        ))}
      </div>

      <CardPad>
        <SectionTitle title="Feature importances" subtitle="Gini importance from the trained classifier" />
        <div className="space-y-3">
          {imps.map(f => (
            <div key={f.feature}>
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-body">{f.feature.replace(/_/g, ' ')}</span>
                <span className="text-muted">{pct(f.importance)}</span>
              </div>
              <div className="mt-1"><ProgressBar value={f.importance} /></div>
              {f.description && <div className="mt-1 text-xs text-subtle">{f.description}</div>}
            </div>
          ))}
        </div>
      </CardPad>

      <CardPad>
        <SectionTitle title="Hybrid model design" />
        <p className="text-sm leading-relaxed text-body">{data.hybrid_note}</p>
        {(data.training as any)?.data && (
          <p className="mt-2 text-xs text-subtle">Training data: {(data.training as any).data}</p>
        )}
      </CardPad>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
