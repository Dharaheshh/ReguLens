import { AlertTriangle, History } from 'lucide-react';

interface ContradictionAlertProps {
  contradictions: any[];
}

export function ContradictionAlert({ contradictions }: ContradictionAlertProps) {
  if (!contradictions || contradictions.length === 0) return null;

  return (
    <div className="space-y-4 mt-6">
      <h3 className="text-sm font-semibold text-rl-ink flex items-center gap-2">
        <AlertTriangle size={16} className="text-rl-red-600" />
        Contradictions Detected
      </h3>
      
      {contradictions.map((contra, idx) => (
        <div key={idx} className="rl-card border-rl-red-200 overflow-hidden">
          <div className="bg-rl-red-50 px-4 py-2 border-b border-rl-red-200 flex items-center gap-2">
            <span className="text-xs font-bold text-rl-red-800 uppercase tracking-wider">
              {contra.level ? contra.level.replace('_', ' ') : 'CONTRADICTION'}
            </span>
          </div>
          
          <div className="grid grid-cols-2 divide-x divide-rl-neutral-200">
            {/* New Claim */}
            <div className="p-4 bg-white">
              <span className="text-2xs font-mono text-rl-neutral-400 mb-1 block">CURRENT DRAFT</span>
              <p className="text-sm text-rl-ink leading-relaxed">{contra.newClaim.text}</p>
            </div>
            {/* Historical Claim */}
            <div className="p-4 bg-rl-neutral-50">
              <div className="flex items-center gap-1.5 mb-1">
                <History size={12} className="text-rl-neutral-400" />
                <span className="text-2xs font-mono text-rl-neutral-500">HISTORICAL RECORD ({contra.historicalClaim.source})</span>
              </div>
              <p className="text-sm text-rl-neutral-700 leading-relaxed">{contra.historicalClaim.text}</p>
            </div>
          </div>
          
          <div className="p-4 bg-white border-t border-rl-neutral-100">
            <span className="text-xs font-semibold text-rl-ink block mb-1">AI Reasoning</span>
            <p className="text-sm text-rl-neutral-600">{contra.factors && contra.factors.length > 0 ? contra.factors[0] : 'No reasoning provided.'}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
