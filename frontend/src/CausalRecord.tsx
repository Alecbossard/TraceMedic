import { FileCode2 } from 'lucide-react';

export type SourceQuote = {evidence_id: string; line: number; quote: string; quote_truncated?: boolean};
export type CausalHypothesis = {
  id: string; alias?: string; claim: string; status: string; reason: string;
  evidence_ids: string[]; check_ids: string[]; trigger?: string; mechanism?: string;
  effect?: string; citations?: SourceQuote[]; support_level?: string;
};

export function CausalRecord({hypothesis, sources, onCitation}: {
  hypothesis: CausalHypothesis;
  sources: {id: string; path: string}[];
  onCitation: (id: string, line: number) => void;
}) {
  if (!hypothesis.mechanism) return <h3>{hypothesis.claim}</h3>;
  return <>
    <dl className="causal-chain">
      {([['Trigger', hypothesis.trigger], ['Mechanism', hypothesis.mechanism],
        ['Observed effect', hypothesis.effect]] as const).map(([label, text]) =>
        <div key={label}><dt>{label}</dt><dd>{text}</dd></div>)}
    </dl>
    <div className="quoted-sources" aria-label="Exact source citations">
      {hypothesis.citations?.map((citation, index) => {
        const source = sources.find(s => s.id === citation.evidence_id);
        return <button key={index} onClick={() => onCitation(citation.evidence_id, citation.line)}>
          <span><FileCode2 size={12}/>{source?.path ?? 'Captured source'}:{citation.line}</span>
          <code>{citation.quote}{citation.quote_truncated?'…':''}</code>
        </button>;
      })}
    </div>
  </>;
}
