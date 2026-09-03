import type { Label } from '../lib/types'

/** Horizontal bar for P(PNEUMONIA), coloured by the predicted label. */
export function ProbabilityBar({ probability, label }: { probability: number; label: Label }) {
  const pct = Math.round(probability * 1000) / 10
  const barColor = label === 'PNEUMONIA' ? 'bg-red-500' : 'bg-emerald-500'

  return (
    <div>
      <div className="mb-1 flex justify-between text-sm text-slate-600">
        <span>Probability of pneumonia</span>
        <span className="font-medium tabular-nums">{pct}%</span>
      </div>
      <div
        className="h-3 w-full overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={`h-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
