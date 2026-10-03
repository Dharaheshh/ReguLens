import { CheckCircle2, Loader2, Circle } from 'lucide-react';

interface PipelineStepperProps {
  status: 'idle' | 'running' | 'complete' | 'failed';
  elapsedMs: number;
}

const STAGES = [
  { key: 'extraction', label: 'Requirement Extraction', baseMs: 400 },
  { key: 'retrieval', label: 'Hybrid Retrieval (Reranked)', baseMs: 1500 },
  { key: 'generation', label: 'Response Generation', baseMs: 3500 },
  { key: 'citation', label: 'Citation Validation', baseMs: 4500 },
  { key: 'claim', label: 'Claim Validation', baseMs: 5000 },
  { key: 'contradiction', label: 'Contradiction Check', baseMs: 6000 },
  { key: 'sufficiency', label: 'Sufficiency Assessment', baseMs: 6500 },
];

export function PipelineStepper({ status, elapsedMs }: PipelineStepperProps) {
  if (status === 'idle') return null;

  return (
    <div className="rl-card p-5 animate-fade-in w-full max-w-md bg-white">
      <h3 className="text-sm font-semibold text-rl-ink mb-4 flex items-center gap-2">
        {status === 'running' && <Loader2 size={14} className="animate-spin text-rl-green-600" />}
        {status === 'complete' && <CheckCircle2 size={14} className="text-rl-green-600" />}
        {status === 'failed' && <Circle size={14} className="text-rl-red-600" />}
        Pipeline Status
      </h3>
      <div className="space-y-3">
        {STAGES.map((stage, i) => {
          // If status is complete, all are done.
          // Otherwise, if elapsedMs > baseMs, it's done.
          // If elapsedMs is between previous stage baseMs and this stage baseMs, it's active.
          const prevMs = i === 0 ? 0 : STAGES[i - 1].baseMs;
          const isDone = status === 'complete' || elapsedMs >= stage.baseMs;
          const isActive = status === 'running' && !isDone && elapsedMs >= prevMs;

          // Format simulated time
          const displayTime = isDone 
            ? `(~${(stage.baseMs / 1000).toFixed(1)}s)` 
            : isActive ? '(in progress...)' : '';

          return (
            <div key={stage.key} className="flex items-start gap-3">
              <div className="mt-0.5 shrink-0 flex flex-col items-center">
                {isDone ? (
                  <CheckCircle2 size={15} className="text-rl-blue-600" />
                ) : isActive ? (
                  <Loader2 size={15} className="text-rl-green-500 animate-spin" />
                ) : (
                  <div className="w-[15px] h-[15px] rounded-full border-2 border-rl-neutral-200" />
                )}
                {/* Connector line */}
                {i < STAGES.length - 1 && (
                  <div className={`w-px h-4 my-0.5 ${isDone ? 'bg-rl-blue-200' : 'bg-rl-neutral-100'}`} />
                )}
              </div>
              <div className="-mt-0.5">
                <p className={`text-xs font-medium ${isDone ? 'text-rl-ink' : isActive ? 'text-rl-ink animate-pulse' : 'text-rl-neutral-400'}`}>
                  {stage.label}
                </p>
                {displayTime && (
                  <p className={`text-2xs font-mono mt-0.5 ${isDone ? 'text-rl-neutral-500' : 'text-rl-amber-600'}`}>
                    {displayTime}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
