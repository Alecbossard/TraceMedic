import { useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  ChevronDown,
  Circle,
  Clipboard,
  CopyCheck,
  FileCode2,
  Fingerprint,
  FlaskConical,
  GitBranch,
  LoaderCircle,
  LockKeyhole,
  ScanLine,
  ShieldCheck,
} from "lucide-react";
import { CausalRecord } from "./CausalRecord";
import { FindingPreview } from "./FindingPreview";
import { Hint, Status } from "./Chrome";
import { activeStatuses, roles, time } from "./lib";
import type { Evidence, Run, TraceEvent } from "./types";

function EmptyPanel({ kind }: { kind: "overview" | "activity" | "evidence" }) {
  const content = {
    overview: {
      icon: ScanLine,
      title: "No investigation started",
      text: "Start an investigation to connect the failure, the source code and a reproducible check.",
    },
    activity: {
      icon: Activity,
      title: "No activity recorded",
      text: "Model decisions, tool calls and reviews appear here as they happen.",
    },
    evidence: {
      icon: FileCode2,
      title: "No sources captured",
      text: "Captured files appear here during a run. Follow any citation to its exact source line.",
    },
  }[kind];
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <content.icon size={24} strokeWidth={1.4} />
      </span>
      <h3>{content.title}</h3>
      <p>{content.text}</p>
      <span className="empty-caption">
        <LockKeyhole size={12} />
        Local execution · read-only incident files
      </span>
    </div>
  );
}

export function CitationChips({
  ids,
  sources,
  openSource,
}: {
  ids: string[];
  sources: Evidence[];
  openSource: (id: string, line?: number) => void;
}) {
  return (
    <div className="citations">
      {ids.map((id) => {
        const source = sources.find((s) => s.id === id);
        return (
          source && (
            <button key={id} onClick={() => openSource(id)}>
              <FileCode2 size={12} />
              {source.path}
              <span>
                L{source.start_line}
                {source.end_line !== source.start_line
                  ? "–" + source.end_line
                  : ""}
              </span>
              <ArrowRight size={11} />
            </button>
          )
        );
      })}
    </div>
  );
}

export function Overview({
  run,
  openSource,
  showActivity,
}: {
  run: Run | null;
  openSource: (id: string, line?: number) => void;
  showActivity: () => void;
}) {
  if (!run) return <EmptyPanel kind="overview" />;
  const diagnostic = run.state.diagnostic;
  const hypotheses = run.state.hypotheses || [];
  return (
    <div className="overview-content">
      {diagnostic ? (
        <FindingPreview
          outcome={diagnostic.outcome}
          text={
            hypotheses.find((h) => diagnostic.hypothesis_ids?.includes(h.id))
              ?.mechanism || diagnostic.summary
          }
        />
      ) : (
        <div className="pending-finding">
          <span className="pending-icon">
            {activeStatuses.includes(run.status) ? (
              <LoaderCircle className="spin" size={20} />
            ) : (
              <GitBranch size={20} />
            )}
          </span>
          <div>
            <strong>
              {activeStatuses.includes(run.status)
                ? "Following the evidence"
                : "Investigation paused"}
            </strong>
            <p>
              {activeStatuses.includes(run.status)
                ? "The result will appear after investigation and review."
                : "The audit and captured sources are preserved. Resume from the last saved action."}
            </p>
          </div>
          <button className="text-button" onClick={showActivity}>
            View activity
            <ArrowRight size={14} />
          </button>
        </div>
      )}
      {hypotheses.length > 0 && (
        <section className="hypotheses-panel">
          <div className="section-heading">
            <h2>Causal records</h2>
            <span className="count">{hypotheses.length}</span>
            <span className="section-description">Proposed, then reviewed</span>
          </div>
          {hypotheses.map((h, index) => (
            <article className="causal-record" key={h.id}>
              <div className="hypothesis-top">
                <span className="record-id">
                  <GitBranch size={14} />
                  {h.alias || "H" + String(index + 1).padStart(2, "0")}
                </span>
                <Status status={h.status} />
              </div>
              <CausalRecord
                hypothesis={h}
                sources={run.evidence}
                onCitation={openSource}
              />
              {h.reason && (
                <div className="review-reason">
                  <ShieldCheck size={14} />
                  <p>{h.reason}</p>
                </div>
              )}
              {!h.mechanism && (
                <CitationChips
                  ids={h.evidence_ids}
                  sources={run.evidence}
                  openSource={openSource}
                />
              )}
            </article>
          ))}
        </section>
      )}
      {!!run.state.checks?.length && (
        <section className="checks">
          <div className="section-heading">
            <h2>Executed checks</h2>
            <span className="count">{run.state.checks.length}</span>
          </div>
          {run.state.checks.map((check) => (
            <div className="check-row" key={check.check_id}>
              <span className="check-symbol">
                <FlaskConical size={16} />
              </span>
              <div>
                <div className="check-title">
                  <strong>
                    {check.kind === "intervention"
                      ? "Isolated experiment"
                      : "Fixture reproduction"}
                  </strong>
                  <Status status={check.status} />
                </div>
                {check.kind === "intervention" && (
                  <p className="experiment-comparison">
                    Baseline <b>{check.baseline?.status}</b>
                    <ArrowRight size={13} />
                    Trial <b>{check.trial?.status}</b>
                  </p>
                )}
                {check.changes?.map((change, i) => (
                  <code key={i}>
                    {change.path} = {JSON.stringify(change.value)}
                  </code>
                ))}
                <pre>{check.detail}</pre>
                <span className="subtle mono">{check.check_id}</span>
              </div>
            </div>
          ))}
        </section>
      )}
      {diagnostic && (
        <section
          id="final-finding"
          tabIndex={-1}
          className={"diagnostic-card " + diagnostic.outcome}
        >
          <div className="section-heading">
            <h2>
              <ShieldCheck size={16} />
              Finding & next steps
            </h2>
            <span className="status">
              {diagnostic.outcome === "supported"
                ? "Supported in fixture"
                : "Cause not established"}
            </span>
          </div>
          <p className="diagnostic-summary">{diagnostic.summary}</p>
          {diagnostic.rendered_from_reviewed_records && (
            <div className="reviewed-record-note">
              <Check size={13} />
              {diagnostic.support_level === "controlled_intervention"
                ? "Reproduced + isolated intervention"
                : diagnostic.support_level === "reproduction"
                  ? "Reproduced behavior · causal record reviewed"
                  : "Explicit uncertainty"}
              <span>Assembled from reviewed records</span>
            </div>
          )}
          <CitationChips
            ids={diagnostic.evidence_ids}
            sources={run.evidence}
            openSource={openSource}
          />
          <div className="diagnostic-bottom">
            <div>
              <h3>Proposed next actions</h3>
              <ol>
                {diagnostic.next_actions.map((action, index) => (
                  <li key={index}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <p>{action}</p>
                  </li>
                ))}
              </ol>
              <span className="recommendation-note">
                Model suggestions · require your review
              </span>
            </div>
            <div className="limitations">
              <h3>Scope & limitations</h3>
              {diagnostic.limitations.map((limit, index) => (
                <p key={index}>{limit}</p>
              ))}
              <span>
                <LockKeyhole size={12} />
                No correction has been applied.
              </span>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

const eventIcon = (event: TraceEvent) =>
  event.kind === "tool_result"
    ? FileCode2
    : event.kind === "review"
      ? ShieldCheck
      : event.kind === "delegation"
        ? GitBranch
        : event.kind === "diagnostic"
          ? Check
          : Circle;
export function Timeline({ run }: { run: Run | null }) {
  const [expanded, setExpanded] = useState<number | null>(null),
    [filter, setFilter] = useState("all");
  if (!run) return <EmptyPanel kind="activity" />;
  const events = run.events.filter(
    (e) => !["model_response", "session_end", "model_reused"].includes(e.kind),
  );
  const visible = events.filter(
    (e) =>
      filter === "all" ||
      (filter === "tools"
        ? ["tool_result", "tool_error", "mcp_connected"].includes(e.kind)
        : [
            "delegation",
            "review",
            "diagnostic",
            "model_attempt",
            "hypothesis",
          ].includes(e.kind)),
  );
  const active = activeStatuses.includes(run.status);
  const attempt = run.events.filter((e) => e.kind === "model_attempt").at(-1);
  const response = run.events
    .filter((e) => ["model_response", "error"].includes(e.kind))
    .at(-1);
  const waiting =
    active && attempt && (!response || attempt.seq > response.seq);
  return (
    <section className="timeline-panel">
      <div className="activity-toolbar">
        <div>
          <h2>Investigation timeline</h2>
          <span>{events.length} recorded events</span>
        </div>
        <div className="mini-segment" aria-label="Filter activity">
          {[
            ["all", "All events"],
            ["decisions", "Decisions"],
            ["tools", "Tools"],
          ].map(([value, label]) => (
            <button
              key={value}
              className={filter === value ? "on" : ""}
              onClick={() => setFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="agent-lanes">
        {(run.mode === "single"
          ? ["single"]
          : ["coordinator", "investigator", "verifier"]
        ).map((role) => (
          <span
            key={role}
            className={active && attempt?.role === role ? "lane-active" : ""}
          >
            <i className={"role-dot " + role} />
            {roles[role]}
            {active && attempt?.role === role && waiting && (
              <LoaderCircle className="spin" size={11} />
            )}
          </span>
        ))}
      </div>
      <div className="timeline">
        {visible.map((event) => {
          const Icon = eventIcon(event);
          return (
            <article className={"timeline-event " + event.role} key={event.seq}>
              <span className="event-marker">
                <Icon size={13} />
              </span>
              <button
                className="event-body"
                aria-expanded={expanded === event.seq}
                onClick={() =>
                  setExpanded(expanded === event.seq ? null : event.seq)
                }
              >
                <div className="event-top">
                  <span>
                    {roles[event.role] || event.role}
                    <span className="event-kind">
                      {event.kind.replaceAll("_", " ")}
                    </span>
                  </span>
                  <span>
                    <time>{time(event.timestamp)}</time>
                    <ChevronDown size={13} />
                  </span>
                </div>
                <p>{event.message}</p>
                {expanded === event.seq && (
                  <pre>{JSON.stringify(event.data, null, 2)}</pre>
                )}
              </button>
            </article>
          );
        })}
        {!visible.length && (
          <p className="no-match">No events in this category.</p>
        )}
        {waiting && (
          <div className="actual-wait" role="status">
            <LoaderCircle className="spin" size={14} />
            {roles[attempt.role]} is awaiting the local model.
          </div>
        )}
      </div>
    </section>
  );
}

function CodeLine({ text }: { text: string }) {
  const tokens = text.split(
    /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#[^\n]*|\b(?:def|return|if|else|elif|for|in|import|from|assert|raise|try|except|class|None|True|False|and|or|not|with|as)\b|\b\d+(?:\.\d+)?\b)/g,
  );
  return (
    <>
      {tokens.map((token, index) => (
        <span
          key={index}
          className={
            /^['"]/.test(token)
              ? "syntax-string"
              : /^#/.test(token)
                ? "syntax-comment"
                : /^\d/.test(token)
                  ? "syntax-number"
                  : /^(def|return|if|else|elif|for|in|import|from|assert|raise|try|except|class|None|True|False|and|or|not|with|as)$/.test(
                        token,
                      )
                    ? "syntax-keyword"
                    : undefined
          }
        >
          {token}
        </span>
      ))}
    </>
  );
}

export function EvidencePanel({
  run,
  evidenceId,
  focusedLine,
  choose,
  exportRun,
}: {
  run: Run | null;
  evidenceId: string | null;
  focusedLine: number | null;
  choose: (id: string) => void;
  exportRun: () => void;
}) {
  const [copied, setCopied] = useState(false),
    [copyError, setCopyError] = useState("");
  const evidence =
    run?.evidence.find((e) => e.id === evidenceId) || run?.evidence[0];
  async function copy() {
    if (!evidence) return;
    try {
      await navigator.clipboard.writeText(evidence.excerpt);
      setCopied(true);
      setCopyError("");
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopyError("Clipboard unavailable. Select and copy the source text.");
    }
  }
  if (!evidence) return <EmptyPanel kind="evidence" />;
  return (
    <section className="evidence-panel">
      <div className="evidence-toolbar">
        <div>
          <h2>Captured sources</h2>
          <span>{run?.evidence.length} immutable snapshots</span>
        </div>
        <Hint label="Export full audit JSON">
          <button
            className="icon-button"
            aria-label="Export full audit JSON"
            onClick={exportRun}
          >
            <ArrowDownToLine size={16} />
          </button>
        </Hint>
      </div>
      <div className="evidence-layout">
        <div className="source-file-list" aria-label="Captured files">
          {run?.evidence.map((source) => (
            <button
              key={source.id}
              className={source.id === evidence.id ? "selected" : ""}
              onClick={() => choose(source.id)}
            >
              <FileCode2 size={15} />
              <span>
                {source.path}
                <small>
                  L{source.start_line}–{source.end_line}
                </small>
              </span>
              {source.id === evidence.id && (
                <span className="source-selected-dot" />
              )}
            </button>
          ))}
        </div>
        <div className="code-editor">
          <div className="source-heading">
            <FileCode2 size={14} />
            <strong>{evidence.path}</strong>
            <span>
              L{evidence.start_line}–{evidence.end_line}
            </span>
            <Hint label={copied ? "Copied" : "Copy captured source"}>
              <button
                className="icon-button"
                onClick={copy}
                aria-label="Copy captured source"
              >
                {copied ? <CopyCheck size={14} /> : <Clipboard size={14} />}
              </button>
            </Hint>
          </div>
          <div
            className="source-code"
            tabIndex={0}
            role="region"
            aria-label={"Captured contents of " + evidence.path}
          >
            {evidence.excerpt.split("\n").map((line, index) => (
              <div
                className={
                  "source-line " +
                  (focusedLine === index + evidence.start_line
                    ? "cited-line"
                    : "")
                }
                key={index}
              >
                <span className="line-number">
                  {index + evidence.start_line}
                </span>
                <code>
                  <CodeLine text={line || " "} />
                </code>
              </div>
            ))}
          </div>
          <div className="source-hash">
            <Fingerprint size={12} />
            <span title={evidence.sha256}>
              SHA-256 {evidence.sha256.slice(0, 18)}…
            </span>
            <span>
              <LockKeyhole size={11} />
              Read-only snapshot
            </span>
          </div>
        </div>
      </div>
      <div className="source-notice">
        <ShieldCheck size={13} />
        Captured content is treated as untrusted data, never as instructions.
        {copyError && <span role="alert">{copyError}</span>}
      </div>
    </section>
  );
}
