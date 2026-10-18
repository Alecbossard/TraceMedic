export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(
    "/api" + path,
    body !== undefined
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : undefined,
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "The request failed.");
  return data;
}

export const roles: Record<string, string> = {
  coordinator: "Coordinator",
  investigator: "Investigator",
  verifier: "Verifier",
  single: "Single agent",
  system: "System",
};
export const activeStatuses = ["running", "queued"];
export const statusLabel: Record<string, string> = {
  running: "Investigating",
  queued: "Queued",
  completed: "Completed",
  interrupted: "Interrupted",
  cancelled: "Cancelled",
  error: "Error · resumable",
  failed: "Stopped · error",
  budget_exhausted: "Budget reached",
};
export const time = (value: string) =>
  new Date(value).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
export const shortId = (id: string) =>
  id.startsWith("sample-") ? "S" + id.slice(7) : id.replace("case-", "");
export const reducedScroll = () =>
  matchMedia("(prefers-reduced-motion: reduce)").matches
    ? ("instant" as const)
    : ("smooth" as const);
export const repo =
  "https://github.com/Alecbossard/TraceMedic/tree/codex/v2-evidence";
