import { useState } from "react";
import * as m from "motion/react-m";
import { useReducedMotion } from "motion/react";
import {
  ArrowRight,
  ArrowUpRight,
  ChevronRight,
  CircleCheck,
  Cpu,
  Database,
  FlaskConical,
  GitBranch,
  Info,
  Search,
  ShieldCheck,
  Terminal,
  Unplug,
} from "lucide-react";
import { repo, statusLabel } from "./lib";
import type { Benchmark, Health, Incident, Run } from "./types";

export function HistoryPage({
  runs,
  incidents,
  openRun,
  newRun,
}: {
  runs: Run[];
  incidents: Incident[];
  openRun: (id: string) => void;
  newRun: () => void;
}) {
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all");
  const filtered = runs.filter(
    (run) =>
      (filter === "all" || run.status === filter) &&
      (
        run.id +
        " " +
        (incidents.find((i) => i.id === run.incident_id)?.title ||
          run.incident_id)
      )
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Investigations</h1>
          <p>Saved runs, captured sources and every decision in between.</p>
        </div>
        <button className="primary" onClick={newRun}>
          Open workbench
          <ArrowRight size={14} />
        </button>
      </div>
      <section className="history-panel surface">
        <div className="list-toolbar">
          <label className="search">
            <Search size={15} />
            <input
              aria-label="Search investigations"
              placeholder="Find a run…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <select
            aria-label="Filter investigations by status"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All statuses</option>
            {["completed", "cancelled", "interrupted", "error", "running"].map(
              (status) => (
                <option key={status} value={status}>
                  {statusLabel[status]}
                </option>
              ),
            )}
          </select>
          <span>{filtered.length} runs</span>
        </div>
        <div className="history-columns">
          <span>Incident / run</span>
          <span>Workflow</span>
          <span>Status</span>
          <span>Created</span>
        </div>
        <div className="history-list">
          {filtered.map((run) => (
            <button key={run.id} onClick={() => openRun(run.id)}>
              <span className="history-icon">
                <GitBranch size={17} />
              </span>
              <span className="history-name">
                <strong>
                  {incidents.find((i) => i.id === run.incident_id)?.title ||
                    run.incident_id}
                </strong>
                <small>{run.id}</small>
              </span>
              <span className="history-workflow">
                <b>{(run.engine_version || "v1").toUpperCase()}</b>
                {run.mode === "multi" ? "Multi-agent" : "Single agent"}
                {run.provider === "scripted" && <small>Test double</small>}
              </span>
              <span className={"status " + run.status}>
                <span className="dot" />
                {statusLabel[run.status] || run.status}
              </span>
              <time>
                {new Date(run.created_at).toLocaleDateString("en-GB", {
                  day: "2-digit",
                  month: "short",
                })}
              </time>
              <ChevronRight size={15} />
            </button>
          ))}
        </div>
        {!filtered.length && (
          <div className="empty-state">
            <span className="empty-icon">
              <GitBranch size={24} />
            </span>
            <h3>
              {runs.length
                ? "No matching investigations."
                : "Your first investigation starts here."}
            </h3>
            <p>
              {runs.length
                ? "Try another search or status filter."
                : "Open an incident to start a durable trace."}
            </p>
          </div>
        )}
      </section>
    </>
  );
}

const methodNames: Record<string, string> = {
  deterministic: "Deterministic rules",
  rules: "Deterministic rules",
  "v1-multi": "V1 · Multi-agent",
  "v2-single": "V2 · Single agent",
  "v2-multi": "V2 · Multi-agent",
  single: "Single agent",
  multi: "Multi-agent",
};
export function BenchmarkPage({
  benchmark,
  version,
  changeVersion,
}: {
  benchmark: Benchmark | null;
  version: string;
  changeVersion: (version: string) => void;
}) {
  const [measure, setMeasure] = useState("latency");
  const reduced = useReducedMotion();
  const methods = benchmark?.methods || [];
  const maximum = Math.max(
    ...methods.map((method) =>
      measure === "latency" ? method.median_latency_s : method.model_calls,
    ),
    1,
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Benchmark</h1>
          <p>
            Compare workflows on the same incidents. Every outcome published.
          </p>
        </div>
        <label className="inline-select">
          Experiment
          <select
            aria-label="Benchmark version"
            value={version}
            onChange={(e) => changeVersion(e.target.value)}
          >
            <option value="v2">V2 · Reserved suite</option>
            <option value="v1">V1 · Original study</option>
          </select>
        </label>
      </div>
      <div className="benchmark-summary">
        <div>
          <span>RECORDED RUNS</span>
          <strong>
            {benchmark?.total_runs ?? "—"}
            <small>
              {" "}
              / {benchmark?.scheduled_runs || benchmark?.total_runs || "—"}
            </small>
          </strong>
        </div>
        <div>
          <span>RESERVED INCIDENTS</span>
          <strong>12</strong>
        </div>
        <div>
          <span>METHODS COMPARED</span>
          <strong>{methods.length || "—"}</strong>
        </div>
        <div>
          <span>EVALUATION</span>
          <strong className="summary-status">
            <span
              className={
                "dot " + (benchmark?.status === "complete" ? "live" : "")
              }
            />
            {benchmark?.status === "complete" ? "Complete" : "In progress"}
          </strong>
        </div>
      </div>
      <section className="comparison-panel surface">
        <div className="section-heading">
          <div>
            <h2>Efficiency comparison</h2>
            <p>Lower is better. Measurements from the published runs.</p>
          </div>
          <div className="mini-segment" aria-label="Benchmark chart metric">
            <button
              className={measure === "latency" ? "on" : ""}
              onClick={() => setMeasure("latency")}
            >
              Latency
            </button>
            <button
              className={measure === "calls" ? "on" : ""}
              onClick={() => setMeasure("calls")}
            >
              Model calls
            </button>
          </div>
        </div>
        <div className="comparison-chart">
          {methods.map((method) => {
            const value =
              measure === "latency"
                ? method.median_latency_s
                : method.model_calls;
            return (
              <div
                className={
                  "comparison-row " +
                  (method.method === "v2-multi" ? "featured" : "")
                }
                key={method.method}
              >
                <div className="chart-method">
                  <strong>{methodNames[method.method] || method.method}</strong>
                  <span>
                    {method.method === "v2-multi"
                      ? "Current default"
                      : method.method === "v1-multi"
                        ? "Reference workflow"
                        : method.runs + " recorded runs"}
                  </span>
                </div>
                <div className="bar-track">
                  <m.div
                    initial={false}
                    animate={{ width: (value / maximum) * 100 + "%" }}
                    transition={{
                      duration: reduced ? 0 : 0.35,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    className="bar-fill"
                  />
                </div>
                <span className="chart-value">
                  {measure === "latency" ? value.toFixed(1) : value}
                  <small>{measure === "latency" ? "s" : "calls"}</small>
                </span>
              </div>
            );
          })}
        </div>
        <div className="chart-footer">
          <span>
            {measure === "latency"
              ? "Median wall time per run"
              : "Total model decisions across all runs"}
          </span>
          <span>Same local model · No paid API</span>
        </div>
      </section>
      <div className="section-heading table-title">
        <h2>All measured outcomes</h2>
        <a
          className="text-link"
          href={
            repo +
            "/benchmarks" +
            (version === "v2" ? "/v2/report.md" : "/report.md")
          }
          target="_blank"
          rel="noreferrer"
        >
          Read full report
          <ArrowUpRight size={13} />
        </a>
      </div>
      <div className="table-wrap surface">
        <table>
          <thead>
            <tr>
              <th>Method</th>
              <th>Runs</th>
              <th>Correct outcomes</th>
              <th>Supported correct</th>
              <th>Unsupported by rubric</th>
              <th>Correct abstentions</th>
              <th>Median latency</th>
              <th>Model calls</th>
            </tr>
          </thead>
          <tbody>
            {methods.map((method) => (
              <tr
                key={method.method}
                className={method.method === "v2-multi" ? "featured" : ""}
              >
                <td>
                  <strong>{method.method}</strong>
                </td>
                <td>{method.runs}</td>
                <td>
                  {method.correct ??
                    method.correct_total ??
                    method.correct_supported}
                  <span className="outcome-denominator"> / {method.runs}</span>
                </td>
                <td>{method.correct_supported}</td>
                <td>{method.unsupported}</td>
                <td>{method.abstention_correct}</td>
                <td>{method.median_latency_s.toFixed(1)} s</td>
                <td>{method.model_calls}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="benchmark-note">
        <Info size={16} />
        <div>
          <strong>
            Efficiency is measured. Semantic reliability remains limited.
          </strong>
          <p>
            {version === "v2"
              ? "12 fresh reserved incidents. Deterministic rules, original V1 multi-agent and both V2 variants. Automatic scores contain false positives; the semantic audit is published. The optional intervention tool was not selected in these benchmark runs."
              : "Original V1 study: 24 synthetic incidents, 12 reserved cases, three methods."}{" "}
            Hardware, electricity and monetary costs are not measured.
          </p>
          <a
            href={
              repo +
              "/benchmarks/" +
              (version === "v2" ? "v2/semantic_audit.md" : "report.md")
            }
            target="_blank"
            rel="noreferrer"
          >
            Inspect scoring & limitations
            <ArrowUpRight size={12} />
          </a>
        </div>
      </div>
    </>
  );
}

export function SystemPage({ health }: { health: Health | null }) {
  const stack = [
    {
      icon: Cpu,
      label: "Model provider",
      value: health?.model || "Unavailable",
      detail: health?.detail || "Checking endpoint",
      tag: health?.available ? "Connected" : "Unavailable",
    },
    {
      icon: Terminal,
      label: "Tool transport",
      value: "MCP over stdio",
      detail:
        "A separate subprocess, bound to the selected incident. No general shell.",
      tag: "Isolated",
    },
    {
      icon: Database,
      label: "Persistence",
      value: "SQLite + LangGraph",
      detail:
        "Graph checkpoints, source snapshots, operation ledger and recorded events.",
      tag: "Durable",
    },
    {
      icon: ShieldCheck,
      label: "Execution budgets",
      value: `${health?.limits.model_calls || 18} model / ${health?.limits.tool_calls || 14} tool calls`,
      detail:
        "Bounded turns, retries and timeouts. Explicit termination at the budget.",
      tag: "Bounded",
    },
  ];
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>System & setup</h1>
          <p>Your local runtime, its connections and its boundaries.</p>
        </div>
        <span
          className={
            "connection-badge " + (health?.available ? "connected" : "")
          }
        >
          {health?.available ? <CircleCheck size={14} /> : <Unplug size={14} />}
          {health?.available ? "Provider reachable" : "Provider unavailable"}
        </span>
      </div>
      <section className="system-stack surface">
        <div className="section-heading">
          <h2>Environment</h2>
          <span className="mono subtle">127.0.0.1 · Local workspace</span>
        </div>
        {stack.map(({ icon: Icon, label, value, detail, tag }) => (
          <div className="stack-row" key={label}>
            <span className="stack-icon">
              <Icon size={20} strokeWidth={1.5} />
            </span>
            <div>
              <span className="stack-label">{label}</span>
              <h2>{value}</h2>
              <p>{detail}</p>
            </div>
            <span className="stack-tag">{tag}</span>
          </div>
        ))}
      </section>
      <section className="setup-card surface">
        <div className="section-heading">
          <div>
            <h2>Reproduce an investigation</h2>
            <p>Run the same workflow from your terminal.</p>
          </div>
          <Terminal size={18} />
        </div>
        <div className="terminal-example">
          <div>
            <span>01</span>
            <span className="terminal-dollar">$</span>
            <code>.venv\Scripts\tracemedic run case-01</code>
          </div>
          <div>
            <span>02</span>
            <span className="terminal-dollar">$</span>
            <code>.venv\Scripts\tracemedic resume &lt;run-id&gt;</code>
          </div>
        </div>
        <div className="setup-bottom">
          <p>
            Installation, model setup, recovery and the limits of synthetic
            validation.
          </p>
          <a
            className="text-link"
            href={repo + "#readme"}
            target="_blank"
            rel="noreferrer"
          >
            Reproduction guide
            <ArrowUpRight size={14} />
          </a>
        </div>
      </section>
      <div className="system-footnote">
        <FlaskConical size={14} />
        Research build · shipped synthetic corpus · production diagnosis is not
        established.
      </div>
    </>
  );
}
