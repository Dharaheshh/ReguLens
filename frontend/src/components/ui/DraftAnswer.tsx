import { CitationChip } from './CitationChip';

interface DraftAnswerProps {
  draftText: string;
  claims: any[];
  onCite: (code: string) => void;
  selectedCitation: string | null;
}

export function DraftAnswer({ draftText, claims, onCite, selectedCitation }: DraftAnswerProps) {
  if (!draftText || draftText === 'No text generated.') {
    return <p className="text-sm text-rl-neutral-500 italic px-5 py-4">Draft generation skipped due to insufficient evidence.</p>;
  }

  // The draft text from the backend often contains citations like [EVD-00045].
  // If we had a perfect mapping, we would replace exactly the substrings.
  // Instead, let's just render the claims as distinct blocks as requested by the design direction.

  return (
    <div className="space-y-4 px-5 py-4 bg-white">
      {claims.length === 0 ? (
        <p className="text-sm text-rl-neutral-800 leading-relaxed whitespace-pre-wrap">{draftText}</p>
      ) : (
        claims.map((claim, idx) => {
          const isSupported = claim.status === 'SUPPORTED' || claim.status === 'VALID';
          const isOverclaim = claim.status === 'PARTIALLY_SUPPORTED';
          
          let borderColor = 'border-rl-neutral-300';
          let bgColor = 'bg-white';
          
          if (isSupported) {
            borderColor = 'border-rl-green-500';
          } else if (isOverclaim) {
            borderColor = 'border-rl-amber-500';
            bgColor = 'bg-rl-amber-50';
          } else {
            borderColor = 'border-rl-red-500 border-dashed';
            bgColor = 'bg-rl-red-50';
          }

          return (
            <div key={idx} className={`pl-3 py-1 border-l-[3px] ${borderColor} ${bgColor} transition-colors`}>
              <p className="text-sm text-rl-ink leading-relaxed">
                {claim.text}
              </p>
              {claim.citedEvidence && claim.citedEvidence.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {claim.citedEvidence.map((evdCode: string) => (
                    <CitationChip 
                      key={evdCode} 
                      code={evdCode} 
                      selected={selectedCitation === evdCode}
                      onClick={() => onCite(evdCode)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
