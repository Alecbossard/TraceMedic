import { ArrowUpRight, FileCode2 } from "lucide-react";
import type { Hypothesis } from "./types";
export type { Hypothesis as CausalHypothesis } from "./types";

export function CausalRecord({
  hypothesis,
  sources,
  onCitation,
}: {
  hypothesis: Hypothesis;
  sources: { id: string; path: string }[];
  onCitation: (id: string, line: number) => void;
}) {
  if (!hypothesis.mechanism)
    return <h3 className="legacy-claim">{hypothesis.claim}</h3>;
  return (
    <>
      <dl className="causal-chain">
        {(
          [
            ["Trigger", hypothesis.trigger],
            ["Mechanism", hypothesis.mechanism],
            ["Observed effect", hypothesis.effect],
          ] as const
        ).map(([label, text], index) => (
          <div key={label}>
            <dt>
              <span>{String(index + 1).padStart(2, "0")}</span>
              {label}
            </dt>
            <dd>{text}</dd>
          </div>
        ))}
      </dl>
      {!!hypothesis.citations?.length && (
        <div className="quoted-sources" aria-label="Exact source citations">
          <div className="section-caption">
            SOURCE REFERENCES{" "}
            <span>{hypothesis.citations.length} captured lines</span>
          </div>
          <div className="quote-grid">
            {hypothesis.citations.map((citation, index) => {
              const source = sources.find((s) => s.id === citation.evidence_id);
              return (
                <button
                  key={index}
                  onClick={() =>
                    onCitation(citation.evidence_id, citation.line)
                  }
                >
                  <span>
                    <FileCode2 size={13} />
                    <strong>{source?.path ?? "Captured source"}</strong>
                    <span>L{citation.line}</span>
                    <ArrowUpRight size={13} />
                  </span>
                  <code>
                    {citation.quote}
                    {citation.quote_truncated ? "…" : ""}
                  </code>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
