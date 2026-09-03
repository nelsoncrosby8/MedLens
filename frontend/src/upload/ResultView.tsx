import { useState } from 'react'
import { DISCLAIMER } from '../components/DisclaimerFooter'
import { ProbabilityBar } from '../components/ProbabilityBar'
import type { PredictResponse } from '../lib/types'

type View = 'heatmap' | 'original'

export function ResultView({
  result,
  previewUrl,
}: {
  result: PredictResponse
  previewUrl: string
}) {
  const [view, setView] = useState<View>('heatmap')
  const isPneumonia = result.label === 'PNEUMONIA'

  return (
    <section className="mt-8 space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Result</h2>
        <span
          className={`rounded-full px-3 py-1 text-sm font-semibold ${
            isPneumonia ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
          }`}
        >
          {result.label}
        </span>
      </div>

      <ProbabilityBar probability={result.probability} label={result.label} />

      <div>
        <div className="mb-2 inline-flex overflow-hidden rounded-md border border-slate-300 text-sm">
          {(['heatmap', 'original'] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className={view === v ? 'bg-slate-900 px-3 py-1 text-white' : 'px-3 py-1 text-slate-600'}
            >
              {v === 'heatmap' ? 'Heatmap' : 'Original'}
            </button>
          ))}
        </div>
        <img
          src={view === 'heatmap' ? result.heatmap : previewUrl}
          alt={view === 'heatmap' ? 'Grad-CAM heatmap overlay' : 'Uploaded chest X-ray'}
          className="w-full rounded-md border border-slate-200 bg-black object-contain"
        />
        <p className="mt-1 text-xs text-slate-500">
          {view === 'heatmap'
            ? 'Warmer colours mark the regions that most influenced the model.'
            : 'Your uploaded image.'}
        </p>
      </div>

      <p className="text-xs text-slate-500">
        Analyzed {new Date(result.created_at).toLocaleString()}. {DISCLAIMER}
      </p>
    </section>
  )
}
