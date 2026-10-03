import { AlertTriangle, CheckCircle2, MinusCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface SufficiencyBannerProps {
  status: 'SUFFICIENT' | 'PARTIALLY_SUFFICIENT' | 'INSUFFICIENT' | string;
  gapSummary?: string;
  requirements?: any[];
}

export function SufficiencyBanner({ status, gapSummary, requirements = [] }: SufficiencyBannerProps) {
  const [expanded, setExpanded] = useState(status !== 'SUFFICIENT');

  const isGreen = status === 'SUFFICIENT';
  const isAmber = status === 'PARTIALLY_SUFFICIENT' || status === 'PARTIALLY_COVERED';
  const isRed = status === 'INSUFFICIENT' || status === 'NOT_COVERED';

  const bgColor = isGreen ? 'bg-rl-green-50' : isAmber ? 'bg-rl-amber-50' : isRed ? 'bg-rl-red-50' : 'bg-rl-neutral-50';
  const borderColor = isGreen ? 'border-rl-green-200' : isAmber ? 'border-rl-amber-200' : isRed ? 'border-rl-red-200' : 'border-rl-neutral-200';
  const textColor = isGreen ? 'text-rl-green-800' : isAmber ? 'text-rl-amber-800' : isRed ? 'text-rl-red-800' : 'text-rl-ink';

  const Icon = isGreen ? CheckCircle2 : isAmber ? MinusCircle : AlertTriangle;

  return (
    <div className={`border ${borderColor} ${bgColor} rounded-rl-md overflow-hidden transition-all duration-200`}>
      <div 
        className="px-4 py-3 flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2.5">
          <Icon size={18} className={textColor} />
          <span className={`font-semibold text-sm ${textColor}`}>
            {status === 'SUFFICIENT' ? 'Sufficiency Assessed: Full Coverage' :
             status === 'PARTIALLY_SUFFICIENT' ? 'Sufficiency Assessed: Partial Gaps Detected' :
             'Sufficiency Assessed: Insufficient Evidence'}
          </span>
        </div>
        <button className={`p-1 rounded-full hover:bg-black/5 ${textColor}`}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      
      {expanded && (
        <div className={`px-4 pb-4 pt-1 text-sm border-t ${borderColor} bg-white`}>
          {gapSummary && (
            <div className="mt-3">
              <span className="font-semibold text-rl-ink text-xs uppercase tracking-wider">Gap Analysis</span>
              <p className="mt-1.5 text-rl-neutral-700 leading-relaxed">{gapSummary}</p>
            </div>
          )}
          
          {requirements.length > 0 && (
            <div className="mt-4 space-y-2">
              <span className="font-semibold text-rl-ink text-xs uppercase tracking-wider">Requirement Map</span>
              {requirements.map((req, i) => (
                <div key={i} className="flex items-start gap-2.5 text-sm">
                  {req.coverage === 'COVERED' ? (
                    <CheckCircle2 size={16} className="text-rl-green-600 mt-0.5 shrink-0" />
                  ) : req.coverage === 'PARTIALLY_COVERED' ? (
                    <MinusCircle size={16} className="text-rl-amber-600 mt-0.5 shrink-0" />
                  ) : (
                    <AlertTriangle size={16} className="text-rl-red-600 mt-0.5 shrink-0" />
                  )}
                  <div>
                    <span className="font-mono text-xs text-rl-neutral-500 mr-2">{req.code}</span>
                    <span className="text-rl-ink">{req.description}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
