import { useState, useRef, useEffect } from 'react';
import { Play, ArrowRight, X } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { EvidenceDrawer } from '../components/ui/EvidenceDrawer';
import { PipelineStepper } from '../components/ui/PipelineStepper';
import { SufficiencyBanner } from '../components/ui/SufficiencyBanner';
import { DraftAnswer } from '../components/ui/DraftAnswer';
import { ContradictionAlert } from '../components/ui/ContradictionAlert';
import { DEMO_QUERY } from '../data/mockData';

export function QueryWorkspacePage() {
  const [queryText, setQueryText] = useState('');
  const [analysisState, setAnalysisState] = useState<'idle'|'analyzing'|'complete'|'failed'>('idle');
  const [elapsedMs, setElapsedMs] = useState(0);
  const [showDemo, setShowDemo] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);
  
  const [responseData, setResponseData] = useState<any>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const timerRef = useRef<number | null>(null);

  const handleCitationClick = (id: string) => {
    setSelectedCitation(id);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedCitation(null);
  };

  const runAnalysis = async () => {
    if (!queryText.trim()) return;
    setAnalysisState('analyzing');
    setShowDemo(false);
    setElapsedMs(0);

    const startTime = Date.now();
    timerRef.current = window.setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 100);

    try {
      const res = await fetch('/api/v1/queries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: queryText })
      });
      if (!res.ok) throw new Error('API failed');
      const data = await res.json();
      
      if (timerRef.current) clearInterval(timerRef.current);
      
      // Adapt API response
      const mappedRequirements = (data.requirements || []).map((r: any) => ({
        code: r.req_code, description: r.description,
        coverage: r.status
      }));
      
      const mappedClaims = (data.claims || []).map((c: any) => ({
        id: c.claim_id, code: c.claim_code, text: c.claim_text,
        status: (c.validation_state === 'SUPPORTED' || c.validation_state === 'VALID') ? 'SUPPORTED' : (c.validation_state === 'PARTIALLY_SUPPORTED' ? 'PARTIALLY_SUPPORTED' : 'UNSUPPORTED'),
        citedEvidence: (c.citations || []).map((cit: any) => cit.evidence_code)
      }));
      
      const mappedContradictions = (data.contradictions || []).map((c: any) => ({
        id: c.contradiction_id || c.id, level: c.classification,
        newClaim: { text: c.claim_a?.claim_text || 'Draft Claim', source: c.claim_a?.claim_code || c.new_claim_code || 'Draft', date: 'Now' },
        historicalClaim: { text: c.claim_b?.claim_text || c.historical_claim_text || 'Historical Claim', source: c.claim_b?.claim_code || c.historical_claim_code || 'History', date: 'History' },
        factors: [c.reasoning]
      }));

      setResponseData({
        requirements: mappedRequirements,
        draftText: data.draft_text || data.gap_summary || 'No text generated.',
        gapSummary: data.gap_summary,
        claims: mappedClaims,
        contradictions: mappedContradictions,
        status: data.sufficiency_status || 'SUFFICIENT'
      });

      setAnalysisState('complete');
      setShowDemo(true);
    } catch (e: any) {
      if (timerRef.current) clearInterval(timerRef.current);
      setAnalysisState('failed');
      alert("Analysis failed: " + e.message);
    }
  };

  const reset = () => {
    setAnalysisState('idle');
    setElapsedMs(0);
    if (timerRef.current) clearInterval(timerRef.current);
    setShowDemo(false);
    setSelectedCitation(null);
    setDrawerOpen(false);
    setQueryText('');
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return (
    <div className="flex flex-col h-full animate-fade-in pb-20">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-rl-ink">Query Workspace</h2>
        <p className="text-sm text-rl-neutral-500 mt-1">Build an evidence-grounded response to a regulatory question.</p>
      </div>

      <div className="rl-card p-4 mb-6">
        <div className="flex items-start gap-4">
          <textarea
            ref={textareaRef}
            value={queryText}
            onChange={e => setQueryText(e.target.value)}
            placeholder="Enter the regulator's question..."
            disabled={analysisState !== 'idle'}
            rows={3}
            className="flex-1 rl-input resize-none text-sm font-normal disabled:bg-rl-neutral-50 disabled:text-rl-neutral-500"
          />
          <div className="flex flex-col gap-2 shrink-0">
            {analysisState === 'idle' && (
              <>
                <Button variant="primary" size="md" icon={<Play size={14} />} disabled={!queryText.trim()} onClick={runAnalysis}>
                  Run analysis
                </Button>
                <Button variant="ghost" size="sm" onClick={() => { setQueryText(DEMO_QUERY); textareaRef.current?.focus(); }}>
                  Load demo query
                </Button>
              </>
            )}
            {analysisState !== 'idle' && (
              <Button variant="outline" size="sm" onClick={reset} icon={<X size={14} />}>Reset / New query</Button>
            )}
          </div>
        </div>
      </div>

      {analysisState !== 'idle' && !showDemo && (
        <div className="flex justify-center my-10">
          <PipelineStepper status={analysisState === 'failed' ? 'failed' : 'running'} elapsedMs={elapsedMs} />
        </div>
      )}

      {analysisState === 'complete' && showDemo && responseData && (
        <div className="max-w-4xl mx-auto w-full space-y-6 pb-12">
          <SufficiencyBanner 
            status={responseData.status} 
            gapSummary={responseData.gapSummary} 
            requirements={responseData.requirements} 
          />
          
          <div className="rl-card overflow-hidden">
            <div className="px-5 py-3 border-b border-rl-neutral-200 bg-rl-neutral-50">
              <h3 className="text-sm font-semibold text-rl-ink">Drafted Response</h3>
            </div>
            <DraftAnswer 
              draftText={responseData.draftText} 
              claims={responseData.claims} 
              onCite={handleCitationClick} 
              selectedCitation={selectedCitation} 
            />
          </div>

          <ContradictionAlert contradictions={responseData.contradictions} />
        </div>
      )}

      {/* Fixed Action Bar at the bottom */}
      {analysisState === 'complete' && showDemo && responseData && (
        <div className="fixed bottom-0 left-64 right-0 bg-white border-t border-rl-neutral-200 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-rl-ink">Review complete</span>
            <span className="text-xs text-rl-neutral-500">Human-in-the-loop verification required.</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="md">Reject</Button>
            <Button variant="outline" size="md">Edit Draft</Button>
            <Button variant="primary" size="md" iconRight={<ArrowRight size={14} />}>Approve & Finalize</Button>
          </div>
        </div>
      )}

      <EvidenceDrawer
        evidence={selectedCitation ? { id: selectedCitation, code: selectedCitation, documentTitle: 'Fetched Evidence', documentVersion: 1, page: 1, section: 'Body', sourceType: 'document', excerpt: 'Fetching raw evidence details requires full integration, but this simulates the lineage tracing.' } : null}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  );
}
