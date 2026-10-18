import { ArrowDownRight, CircleCheck, CircleHelp } from "lucide-react";
import { reducedScroll } from "./lib";

export function FindingPreview({
  outcome,
  text,
}: {
  outcome: string;
  text: string;
}) {
  const supported = outcome === "supported";
  return (
    <section
      className={"finding-preview " + (supported ? "supported" : "unresolved")}
      aria-label="Investigation outcome"
    >
      <div className="finding-symbol">
        {supported ? <CircleCheck size={20} /> : <CircleHelp size={20} />}
      </div>
      <div>
        <div className="finding-kicker">
          {supported
            ? "SUPPORTED IN CAPTURED FIXTURE"
            : "INSUFFICIENT EVIDENCE"}
        </div>
        <h2>{supported ? "Reviewed finding" : "Cause not established"}</h2>
        <p>{text}</p>
        <button
          onClick={() => {
            const target = document.getElementById("final-finding");
            target?.scrollIntoView({
              behavior: reducedScroll(),
              block: "start",
            });
            target?.focus({ preventScroll: true });
          }}
        >
          Review finding & next steps
          <ArrowDownRight size={14} />
        </button>
      </div>
    </section>
  );
}
