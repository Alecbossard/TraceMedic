import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import * as Tooltip from "@radix-ui/react-tooltip";
import { AnimatePresence, LazyMotion, MotionConfig } from "motion/react";
import * as m from "motion/react-m";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  FileCode2,
  FlaskConical,
  GitBranch,
  Layers3,
  LoaderCircle,
  Menu,
  PanelLeft,
  Play,
  RotateCcw,
  Search,
  Square,
  X,
} from "lucide-react";
import "./style.css";
import {
  CommandMenu,
  destinations,
  Hint,
  IncidentNumber,
  Mark,
  MobileNavigation,
  shortcutLabel,
  Sidebar,
} from "./Chrome";
import { BenchmarkPage, HistoryPage, SystemPage } from "./Pages";
import { EvidencePanel, Overview, Timeline } from "./RunPanels";
import { activeStatuses, api, repo, statusLabel } from "./lib";
import type { Benchmark, Health, Incident, Run, RunTab, View } from "./types";

const loadMotion = () =>
  import("./motion-features").then((module) => module.default);
const runTabs: { id: RunTab; label: string; icon: typeof Layers3 }[] = [
  { id: "overview", label: "Overview", icon: Layers3 },
  { id: "activity", label: "Activity", icon: Activity },
  { id: "evidence", label: "Sources", icon: FileCode2 },
];

function App() {
  const [view, setView] = useState<View>("workbench"),
    [tab, setTab] = useState<RunTab>("overview");
  const [incidents, setIncidents] = useState<Incident[]>([]),
    [selected, setSelected] = useState("case-01");
  const [incidentsLoading, setIncidentsLoading] = useState(true);
  const [search, setSearch] = useState(""),
    [libraryFilter, setLibraryFilter] = useState("all");
  const [health, setHealth] = useState<Health | null>(null),
    [runs, setRuns] = useState<Run[]>([]),
    [run, setRun] = useState<Run | null>(null);
  const [runId, setRunId] = useState<string | null>(
    new URLSearchParams(location.search).get("run") ||
      localStorage.getItem("tracemedic.run"),
  );
  const [workflow, setWorkflow] = useState("v2"),
    [mode, setMode] = useState("multi");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [refresh, setRefresh] = useState(0);
  const [evidenceId, setEvidenceId] = useState<string | null>(null),
    [focusedLine, setFocusedLine] = useState<number | null>(null);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null),
    [benchmarkVersion, setBenchmarkVersion] = useState("v2");
  const [commandOpen, setCommandOpen] = useState(false),
    [mobileOpen, setMobileOpen] = useState(false),
    [libraryOpen, setLibraryOpen] = useState(false);

  useEffect(() => {
    let disposed = false;
    const failed = (error: Error) => {
      if (!disposed) setError(error.message);
    };
    void api<Incident[]>("/incidents")
      .then((items) => {
        if (!disposed) setIncidents(items);
      })
      .catch(failed)
      .finally(() => {
        if (!disposed) setIncidentsLoading(false);
      });
    void api<Health>("/health")
      .then((status) => {
        if (!disposed) setHealth(status);
      })
      .catch(failed);
    void api<Run[]>("/runs")
      .then((history) => {
        if (!disposed) setRuns(history);
      })
      .catch(failed);
    void api<Benchmark>("/benchmark")
      .then((results) => {
        if (!disposed) setBenchmark(results);
      })
      .catch(failed);
    return () => {
      disposed = true;
    };
  }, []);
  useEffect(() => {
    const url = new URL(location.href);
    if (runId) url.searchParams.set("run", runId);
    else url.searchParams.delete("run");
    history.replaceState(null, "", url);
  }, [runId]);
  useEffect(() => {
    if (!runId) return;
    let disposed = false,
      first = true,
      lastStatus = "",
      terminalPolls = 0;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const saved = await api<Run>("/runs/" + encodeURIComponent(runId));
        if (disposed) return;
        setRun(saved);
        setSelected(saved.incident_id);
        if (first) {
          setWorkflow(saved.state.engine_version || "v1");
          setMode(saved.mode);
          first = false;
        }
        if (saved.status === "completed" && activeStatuses.includes(lastStatus))
          setTab("overview");
        lastStatus = saved.status;
        localStorage.setItem("tracemedic.run", saved.id);
        if (
          activeStatuses.includes(saved.status) ||
          (saved.events.at(-1)?.kind !== "session_end" && terminalPolls++ < 3)
        )
          timer = setTimeout(load, 1200);
        else
          api<Run[]>("/runs")
            .then((items) => {
              if (!disposed) setRuns(items);
            })
            .catch(() => {});
      } catch (e) {
        if (!disposed) setError((e as Error).message);
      }
    };
    void load();
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [runId, refresh]);
  useEffect(() => {
    const shortcut = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing =
        ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) ||
        target.isContentEditable;
      if (
        ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") ||
        (!typing && e.key === "/")
      ) {
        e.preventDefault();
        setCommandOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);

  function navigate(next: View) {
    setView(next);
    setMobileOpen(false);
    window.scrollTo({ top: 0 });
    if (next === "history")
      api<Run[]>("/runs")
        .then(setRuns)
        .catch((e) => setError(e.message));
    if (next === "benchmark") changeBenchmark(benchmarkVersion);
    if (next === "system")
      api<Health>("/health")
        .then(setHealth)
        .catch((e) => setError(e.message));
  }
  function pickIncident(id: string) {
    setSelected(id);
    if (id.startsWith("sample-")) setWorkflow("v2");
    setRunId(null);
    setRun(null);
    setEvidenceId(null);
    setFocusedLine(null);
    setTab("overview");
    setLibraryOpen(false);
    localStorage.removeItem("tracemedic.run");
    navigate("workbench");
  }
  function openRun(id: string) {
    setRun(null);
    setRunId(id);
    setRefresh((value) => value + 1);
    setTab("overview");
    setEvidenceId(null);
    setFocusedLine(null);
    navigate("workbench");
  }
  function openSource(id: string, line?: number) {
    setEvidenceId(id);
    setFocusedLine(line ?? null);
    setTab("evidence");
  }
  function changeBenchmark(version: string) {
    setBenchmarkVersion(version);
    api<Benchmark>("/benchmark?version=" + version)
      .then(setBenchmark)
      .catch((e) => setError(e.message));
  }
  async function launch() {
    setBusy(true);
    setError("");
    try {
      const created = await api<{ id: string }>("/runs", {
        incident_id: selected,
        mode,
        workflow,
      });
      setRun(null);
      setEvidenceId(null);
      setFocusedLine(null);
      setRunId(created.id);
      setTab("activity");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function control(action: string) {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      await api("/runs/" + run.id + "/" + action, {});
      setRun(await api<Run>("/runs/" + run.id));
      setRefresh((value) => value + 1);
      if (action === "resume") setTab("activity");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function exportRun() {
    if (!run) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(run, null, 2)], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "tracemedic-" + run.id + ".json";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  const incident = incidents.find((item) => item.id === selected);
  const active = !!run && activeStatuses.includes(run.status),
    canResume =
      !!run && ["interrupted", "cancelled", "error"].includes(run.status);
  const elapsed =
    (run?.events
      .filter((e) => e.kind === "session_end")
      .reduce((sum, event) => sum + Number(event.data.elapsed_ms || 0), 0) ||
      0) / 1000;
  const filteredIncidents = incidents.filter(
    (item) =>
      (libraryFilter === "all" ||
        (libraryFilter === "v2"
          ? item.id.startsWith("sample-")
          : item.id.startsWith("case-"))) &&
      (item.title + " " + item.id).toLowerCase().includes(search.toLowerCase()),
  );
  const sidebar = (
    <Sidebar
      view={view}
      navigate={navigate}
      health={health}
      count={runs.length}
      openSearch={() => {
        setMobileOpen(false);
        setCommandOpen(true);
      }}
    />
  );

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">{sidebar}</aside>
      <MobileNavigation open={mobileOpen} onOpenChange={setMobileOpen}>
        {sidebar}
      </MobileNavigation>
      <main id="main-content" tabIndex={-1}>
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMobileOpen(true)}
          >
            <Menu size={19} />
          </button>
          <span className="mobile-brand">
            <Mark small />
          </span>
          <div className="breadcrumbs">
            <span>Workspace</span>
            <ChevronRight size={12} />
            <strong>
              {destinations.find((item) => item.id === view)?.name}
            </strong>
            {view === "workbench" && (
              <>
                <ChevronRight size={12} />
                <span className="breadcrumb-id">{selected.toUpperCase()}</span>
              </>
            )}
          </div>
          <div className="topbar-actions">
            <CommandMenu
              open={commandOpen}
              onOpenChange={setCommandOpen}
              incidents={incidents}
              navigate={navigate}
              selectIncident={pickIncident}
            />
            <a
              className="repo-link"
              href={repo}
              target="_blank"
              rel="noreferrer"
            >
              View source
              <ArrowUpRight size={13} />
            </a>
            <span className="topbar-avatar" title="Local workspace">
              L
            </span>
          </div>
        </header>
        <div className="page-content">
          <AnimatePresence>
            {error && (
              <m.div
                className="error-banner"
                role="alert"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <span>{error}</span>
                <button aria-label="Dismiss error" onClick={() => setError("")}>
                  <X size={16} />
                </button>
              </m.div>
            )}
          </AnimatePresence>
          <AnimatePresence mode="wait" initial={false}>
            <m.div
              key={view}
              className={"page-view view-" + view}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.16 }}
            >
              {view === "workbench" && (
                <>
                  <div className="page-heading">
                    <div>
                      <h1>Incident workbench</h1>
                      <p>Local incident investigation and evidence review.</p>
                    </div>
                    <span className="workspace-context">
                      <span className="dot live" />
                      Local environment<kbd>{shortcutLabel}</kbd>
                    </span>
                  </div>
                  <button
                    className="mobile-library-toggle secondary"
                    onClick={() => setLibraryOpen((value) => !value)}
                    aria-expanded={libraryOpen}
                  >
                    <PanelLeft size={15} />
                    Browse incidents<span>{incidents.length}</span>
                    <ChevronDown size={14} />
                  </button>
                  <div className="workbench-grid">
                    <section
                      className={
                        "incident-library surface " +
                        (libraryOpen ? "rail-mobile-open" : "")
                      }
                    >
                      <div className="library-title">
                        <h2>Incidents</h2>
                        <span className="count">{incidents.length}</span>
                        <Hint label="Search all workspace pages and incidents">
                          <button
                            className="icon-button"
                            aria-label="Find an incident"
                            onClick={() => setCommandOpen(true)}
                          >
                            <Search size={15} />
                          </button>
                        </Hint>
                      </div>
                      <label className="search library-search">
                        <Search size={14} />
                        <input
                          aria-label="Search incidents"
                          placeholder="Filter incidents…"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                        <kbd>/</kbd>
                      </label>
                      <div
                        className="library-filters"
                        aria-label="Incident collection"
                      >
                        {[
                          ["all", "All"],
                          ["v1", "Original"],
                          ["v2", "V2 suite"],
                        ].map(([value, label]) => (
                          <button
                            key={value}
                            className={libraryFilter === value ? "on" : ""}
                            aria-pressed={libraryFilter === value}
                            onClick={() => setLibraryFilter(value)}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                      <div className="incident-list">
                        {filteredIncidents.map((item) => (
                          <button
                            key={item.id}
                            className={
                              "incident-button " +
                              (selected === item.id ? "chosen" : "")
                            }
                            aria-current={
                              selected === item.id ? "true" : undefined
                            }
                            onClick={() => pickIncident(item.id)}
                          >
                            <IncidentNumber id={item.id} />
                            <span>
                              <strong>{item.title}</strong>
                              <small>{item.description}</small>
                            </span>
                            {selected === item.id && <ChevronRight size={13} />}
                          </button>
                        ))}
                        {incidentsLoading && (
                          <p className="no-match" role="status">
                            Loading incidents…
                          </p>
                        )}
                        {!incidentsLoading && !filteredIncidents.length && (
                          <p className="no-match">No matching incidents.</p>
                        )}
                      </div>
                      <div className="library-footer">
                        <FlaskConical size={12} />
                        Synthetic fixtures
                        <span>
                          {filteredIncidents.length} / {incidents.length}
                        </span>
                      </div>
                    </section>
                    <div className="investigation-column surface">
                      <section className="case-card">
                        <div className="case-top">
                          <span className="case-id">
                            <span className="case-id-icon">
                              <GitBranch size={12} />
                            </span>
                            <span className="case-number">
                              {selected.toUpperCase()}
                            </span>
                            <span className="case-collection">
                              {selected.startsWith("sample-")
                                ? "V2 reserved suite"
                                : "Original corpus"}
                            </span>
                          </span>
                          <span
                            className={"status " + (run?.status || "ready")}
                          >
                            {active ? (
                              <LoaderCircle className="spin" size={12} />
                            ) : (
                              <span className="dot" />
                            )}
                            {run
                              ? statusLabel[run.status] || run.status
                              : "Ready"}
                          </span>
                        </div>
                        <h2>{incident?.title || "Choose an incident"}</h2>
                        <p>{incident?.description}</p>
                        <div className="case-controls">
                          <div
                            className="segmented"
                            aria-label="Investigation mode"
                          >
                            <button
                              className={mode === "multi" ? "on" : ""}
                              aria-pressed={mode === "multi"}
                              onClick={() => setMode("multi")}
                              disabled={active}
                            >
                              <GitBranch size={13} />
                              Multi-agent
                            </button>
                            <button
                              className={mode === "single" ? "on" : ""}
                              aria-pressed={mode === "single"}
                              onClick={() => setMode("single")}
                              disabled={active}
                            >
                              Single agent
                            </button>
                          </div>
                          <label className="workflow-select">
                            <select
                              aria-label="Workflow version"
                              value={workflow}
                              onChange={(e) => setWorkflow(e.target.value)}
                              disabled={active}
                            >
                              <option value="v2">V2 · Causal records</option>
                              <option
                                value="v1"
                                disabled={selected.startsWith("sample-")}
                              >
                                V1 · Reference
                              </option>
                            </select>
                          </label>
                          <div className="run-actions">
                            {active ? (
                              <button
                                className="secondary"
                                onClick={() => control("cancel")}
                                disabled={busy || !!run?.cancel_requested}
                              >
                                <Square size={12} />
                                {run?.cancel_requested
                                  ? "Stopping…"
                                  : "Cancel investigation"}
                              </button>
                            ) : canResume ? (
                              <>
                                <button
                                  className="secondary"
                                  onClick={launch}
                                  disabled={busy}
                                >
                                  New run
                                </button>
                                <button
                                  className="primary"
                                  onClick={() => control("resume")}
                                  disabled={busy}
                                >
                                  <RotateCcw size={14} />
                                  Resume investigation
                                </button>
                              </>
                            ) : (
                              <button
                                className="primary"
                                onClick={launch}
                                disabled={
                                  busy || !incident || !health?.available
                                }
                              >
                                {busy ? (
                                  <LoaderCircle className="spin" size={14} />
                                ) : (
                                  <Play size={13} fill="currentColor" />
                                )}
                                Start investigation
                              </button>
                            )}
                          </div>
                        </div>
                        {run && (
                          <div className="run-meta">
                            <span className="run-id">
                              RUN{" "}
                              <span title={run.id}>{run.id.slice(0, 8)}</span>
                            </span>
                            <span>
                              {(run.state.engine_version || "v1").toUpperCase()}
                              <span className="meta-separator">·</span>
                              {run.provider === "scripted"
                                ? "Test double"
                                : run.provider === "ollama"
                                  ? "Local model"
                                  : run.provider}
                            </span>
                            <Hint label="Export full audit JSON">
                              <button
                                className="icon-button"
                                aria-label="Export full audit JSON"
                                onClick={exportRun}
                              >
                                <ArrowDownToLine size={14} />
                              </button>
                            </Hint>
                          </div>
                        )}
                      </section>
                      <div className="metrics-row">
                        <div>
                          <span>Model calls</span>
                          <strong>
                            {run?.metrics.model_calls ?? "—"}
                            <small> / {health?.limits.model_calls ?? 18}</small>
                          </strong>
                        </div>
                        <div>
                          <span>Tool calls</span>
                          <strong>
                            {run?.metrics.tool_calls ?? "—"}
                            <small> / {health?.limits.tool_calls ?? 14}</small>
                          </strong>
                        </div>
                        <div>
                          <span>Reported tokens</span>
                          <strong>
                            {run?.metrics.usage_complete
                              ? (
                                  (run.metrics.input_tokens || 0) +
                                  (run.metrics.output_tokens || 0)
                                ).toLocaleString()
                              : "—"}
                          </strong>
                        </div>
                        <div>
                          <span>Finished session time</span>
                          <strong>
                            {elapsed ? elapsed.toFixed(1) : "—"}
                            <small>{elapsed ? " s" : ""}</small>
                          </strong>
                        </div>
                      </div>
                      <div
                        className="run-tabs"
                        role="tablist"
                        aria-label="Investigation views"
                      >
                        {runTabs.map((item, index) => (
                          <button
                            key={item.id}
                            id={"tab-" + item.id}
                            role="tab"
                            aria-selected={tab === item.id}
                            tabIndex={tab === item.id ? 0 : -1}
                            aria-controls={"panel-" + item.id}
                            className={tab === item.id ? "active" : ""}
                            onClick={() => setTab(item.id)}
                            onKeyDown={(e) => {
                              if (
                                [
                                  "ArrowRight",
                                  "ArrowLeft",
                                  "Home",
                                  "End",
                                ].includes(e.key)
                              ) {
                                e.preventDefault();
                                const next =
                                  e.key === "Home"
                                    ? 0
                                    : e.key === "End"
                                      ? 2
                                      : (index +
                                          (e.key === "ArrowRight" ? 1 : -1) +
                                          3) %
                                        3;
                                setTab(runTabs[next].id);
                                document
                                  .getElementById("tab-" + runTabs[next].id)
                                  ?.focus();
                              }
                            }}
                          >
                            <item.icon size={14} />
                            {item.label}
                            {item.id === "activity" && !!run?.events.length && (
                              <span>
                                {
                                  run.events.filter(
                                    (event) =>
                                      ![
                                        "model_response",
                                        "session_end",
                                        "model_reused",
                                      ].includes(event.kind),
                                  ).length
                                }
                              </span>
                            )}
                            {item.id === "evidence" &&
                              !!run?.evidence.length && (
                                <span>{run.evidence.length}</span>
                              )}
                          </button>
                        ))}
                        <span className="tab-saved">
                          {run && (
                            <>
                              <Check size={11} />
                              Saved locally
                            </>
                          )}
                        </span>
                      </div>
                      <div
                        id={"panel-" + tab}
                        role="tabpanel"
                        aria-labelledby={"tab-" + tab}
                        className="run-panel"
                      >
                        <AnimatePresence mode="wait" initial={false}>
                          <m.div
                            key={tab + ":" + (run?.id || "empty")}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.12 }}
                          >
                            {tab === "overview" && (
                              <Overview
                                run={run}
                                openSource={openSource}
                                showActivity={() => setTab("activity")}
                              />
                            )}
                            {tab === "activity" && <Timeline run={run} />}
                            {tab === "evidence" && (
                              <EvidencePanel
                                run={run}
                                evidenceId={evidenceId}
                                focusedLine={focusedLine}
                                choose={(id) => {
                                  setEvidenceId(id);
                                  setFocusedLine(null);
                                }}
                                exportRun={exportRun}
                              />
                            )}
                          </m.div>
                        </AnimatePresence>
                      </div>
                    </div>
                  </div>
                  <footer className="page-footer">
                    <span>
                      <span className="dot live" />
                      Audit stored in your local workspace
                    </span>
                    <span>
                      Synthetic corpus<span>·</span>V1 / V2 compatible
                    </span>
                  </footer>
                </>
              )}
              {view === "history" && (
                <HistoryPage
                  runs={runs}
                  incidents={incidents}
                  openRun={openRun}
                  newRun={() => navigate("workbench")}
                />
              )}
              {view === "benchmark" && (
                <BenchmarkPage
                  benchmark={benchmark}
                  version={benchmarkVersion}
                  changeVersion={changeBenchmark}
                />
              )}
              {view === "system" && <SystemPage health={health} />}
            </m.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MotionConfig reducedMotion="user" transition={{ duration: 0.18 }}>
      <LazyMotion features={loadMotion} strict>
        <Tooltip.Provider delayDuration={350}>
          <App />
        </Tooltip.Provider>
      </LazyMotion>
    </MotionConfig>
  </React.StrictMode>,
);
