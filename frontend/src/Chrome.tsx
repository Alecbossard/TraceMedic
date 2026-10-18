import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tooltip from "@radix-ui/react-tooltip";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpRight,
  ChartNoAxesColumnIncreasing,
  Check,
  ChevronRight,
  Command,
  CornerDownLeft,
  Cpu,
  FlaskConical,
  GitBranch,
  Github,
  Layers3,
  Search,
  Settings2,
  X,
} from "lucide-react";
import { repo, shortId } from "./lib";
import type { Health, Incident, View } from "./types";

export function Mark({ small = false }: { small?: boolean }) {
  return (
    <span className={"brand-mark" + (small ? " small" : "")} aria-hidden="true">
      <svg viewBox="0 0 28 28" fill="none">
        <path
          d="M4 15h5l3-8 4 14 3-6h5"
          stroke="currentColor"
          strokeWidth="2.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export function Hint({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content className="tooltip" sideOffset={7}>
          {label}
          <Tooltip.Arrow />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export const destinations: { id: View; name: string; icon: typeof Layers3 }[] =
  [
    { id: "workbench", name: "Incident workbench", icon: Layers3 },
    { id: "history", name: "Investigations", icon: GitBranch },
    { id: "benchmark", name: "Benchmark", icon: ChartNoAxesColumnIncreasing },
    { id: "system", name: "System & setup", icon: Settings2 },
  ];

export function Sidebar({
  view,
  navigate,
  health,
  count,
  openSearch,
}: {
  view: View;
  navigate: (view: View) => void;
  health: Health | null;
  count: number;
  openSearch: () => void;
}) {
  return (
    <>
      <a
        className="brand"
        href="#"
        onClick={(e) => {
          e.preventDefault();
          navigate("workbench");
        }}
      >
        <Mark />
        <span>
          TraceMedic<span className="brand-version">02</span>
        </span>
      </a>
      <div className="workspace-switch">
        <span className="workspace-avatar">L</span>
        <div>
          <strong>Local workspace</strong>
          <span>Personal environment</span>
        </div>
        <span className="local-badge">LOCAL</span>
      </div>
      <button className="sidebar-search" onClick={openSearch}>
        <Search size={15} />
        <span>Quick search</span>
        <kbd>{shortcutLabel}</kbd>
      </button>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        {destinations.map(({ id, name, icon: Icon }) => (
          <button
            key={id}
            className={view === id ? "selected" : ""}
            aria-current={view === id ? "page" : undefined}
            onClick={() => navigate(id)}
          >
            <Icon size={17} strokeWidth={1.7} />
            <span>{name}</span>
            {id === "history" && <span className="nav-count">{count}</span>}
            {view === id && <span className="nav-indicator" />}
          </button>
        ))}
      </nav>
      <div className="sidebar-spacer" />
      <div className="model-card">
        <div className="model-card-label">
          <Cpu size={14} />
          <span>INFERENCE</span>
          <span className={"dot " + (health?.available ? "live" : "")} />
        </div>
        <strong>{health?.model || "Checking model…"}</strong>
        <span>
          {!health
            ? "Connecting to local endpoint"
            : health.available
              ? "Model connected"
              : "Endpoint unavailable"}
        </span>
      </div>
      <a
        className="sidebar-source"
        href={repo}
        target="_blank"
        rel="noreferrer"
      >
        <Github size={15} />
        <span>Source & documentation</span>
        <ArrowUpRight size={13} />
      </a>
      <div className="sidebar-bottom">
        <span>v0.2.0</span>
        <span>Local research build</span>
      </div>
    </>
  );
}

type CommandItem = {
  id: string;
  label: string;
  detail: string;
  icon: typeof Search;
  action: () => void;
};
export function CommandMenu({
  open,
  onOpenChange,
  incidents,
  navigate,
  selectIncident,
}: {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  incidents: Incident[];
  navigate: (view: View) => void;
  selectIncident: (id: string) => void;
}) {
  const [query, setQuery] = useState(""),
    [index, setIndex] = useState(0);
  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
    }
  }, [open]);
  const all: CommandItem[] = [
    ...destinations.map((d) => ({
      id: d.id,
      label: d.name,
      detail: "Navigate",
      icon: d.icon,
      action: () => navigate(d.id),
    })),
    ...incidents.map((i) => ({
      id: i.id,
      label: i.title,
      detail: i.id,
      icon: FlaskConical,
      action: () => selectIncident(i.id),
    })),
  ];
  const results = all
    .filter((item) =>
      (item.label + " " + item.detail)
        .toLowerCase()
        .includes(query.toLowerCase()),
    )
    .slice(0, 9);
  const choose = (item: CommandItem) => {
    item.action();
    onOpenChange(false);
  };
  useEffect(() => {
    if (open)
      document
        .getElementById("command-result-" + index)
        ?.scrollIntoView({ block: "nearest" });
  }, [index, open]);
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger asChild>
        <button className="topbar-command" aria-label="Open quick navigation">
          <Search size={15} />
          <span>Quick navigation</span>
          <kbd>{shortcutLabel}</kbd>
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="command-dialog">
          <Dialog.Title className="sr-only">Quick navigation</Dialog.Title>
          <Dialog.Description className="sr-only">
            Search incidents or navigate between workspace pages. Use the arrow
            keys and Enter to select.
          </Dialog.Description>
          <div className="command-input">
            <Search size={19} />
            <input
              placeholder="Search incidents or jump to…"
              aria-label="Search workspace"
              role="combobox"
              aria-expanded="true"
              aria-controls="command-results"
              aria-autocomplete="list"
              aria-activedescendant={
                results.length ? "command-result-" + index : undefined
              }
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setIndex(0);
              }}
              onKeyDown={(e) => {
                if (["ArrowDown", "ArrowUp"].includes(e.key)) {
                  e.preventDefault();
                  setIndex((i) =>
                    results.length
                      ? (i +
                          (e.key === "ArrowDown" ? 1 : -1) +
                          results.length) %
                        results.length
                      : 0,
                  );
                }
                if (e.key === "Enter" && results[index]) {
                  e.preventDefault();
                  choose(results[index]);
                }
              }}
            />
            <Dialog.Close
              className="escape-key"
              aria-label="Close quick navigation"
            >
              esc
            </Dialog.Close>
          </div>
          <div className="command-group">
            {query ? "SEARCH RESULTS" : "QUICK ACCESS"}
          </div>
          <div
            className="command-results"
            id="command-results"
            role="listbox"
            aria-label="Workspace results"
          >
            {results.map((item, i) => (
              <button
                role="option"
                aria-selected={index === i}
                id={"command-result-" + i}
                key={item.id}
                className={index === i ? "highlighted" : ""}
                onPointerMove={() => setIndex(i)}
                onClick={() => choose(item)}
              >
                <span className="command-item-icon">
                  <item.icon size={17} />
                </span>
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
                {index === i ? (
                  <CornerDownLeft size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
              </button>
            ))}
            {!results.length && (
              <div className="command-empty">No results for “{query}”.</div>
            )}
          </div>
          <div className="command-footer">
            <span>
              <kbd>
                <ArrowUp size={10} />
              </kbd>
              <kbd>
                <ArrowDown size={10} />
              </kbd>{" "}
              to navigate
            </span>
            <span>
              <kbd>↵</kbd> to open
            </span>
            <Command size={13} />
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function MobileNavigation({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay drawer-overlay" />
        <Dialog.Content
          className="mobile-drawer"
          onCloseAutoFocus={(event) => {
            event.preventDefault();
            (
              document.querySelector(".mobile-menu") as HTMLElement | null
            )?.focus();
          }}
        >
          <Dialog.Title className="sr-only">Workspace navigation</Dialog.Title>
          <Dialog.Description className="sr-only">
            Navigate TraceMedic pages and inspect the local model status.
          </Dialog.Description>
          <Dialog.Close className="drawer-close" aria-label="Close navigation">
            <X size={18} />
          </Dialog.Close>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export const shortcutLabel = /Mac|iPhone|iPad/.test(navigator.platform)
  ? "⌘ K"
  : "Ctrl K";

export function Status({ status }: { status: string }) {
  return (
    <span className={"status " + status}>
      <span className="dot" />
      {status === "confirmed" && <Check size={11} />}
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function IncidentNumber({ id }: { id: string }) {
  return <span className="incident-number">{shortId(id)}</span>;
}
