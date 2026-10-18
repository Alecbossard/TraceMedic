import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const output = path.resolve(
  root,
  process.env.TRACE_QA_OUTPUT || "docs/evidence/v2",
);
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch(
  process.platform === "win32"
    ? { channel: "msedge", headless: true }
    : { headless: true },
);
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const base = process.env.TRACE_QA_URL || "http://127.0.0.1:8000";
const assert = (value, message) => {
  if (!value) throw Error(message);
};
await page.goto(base);
await page
  .getByRole("heading", { name: "Telemetry gateway", exact: true })
  .waitFor();
const labels =
  (await page.locator("body").innerText()) +
  (await page.getByLabel("Search incidents").getAttribute("placeholder"));
assert(!/Â·|â€¦|â€“|â†/.test(labels), "Interface contains mojibake");
await page.getByLabel("Workflow version").selectOption("v1");
await page.getByLabel("Workflow version").selectOption("v2");
await page.getByLabel("Search incidents").fill("unmatched-fixture");
await page.getByText("No matching incidents.").waitFor();
await page.getByLabel("Search incidents").fill("");
let runId;
const real = process.argv.includes("--real");
if (real) {
  await page
    .getByRole("button", { name: "Start investigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Cancel investigation", exact: true })
    .waitFor();
  await page
    .getByRole("button", { name: "Cancel investigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Resume investigation", exact: true })
    .waitFor({ timeout: 120000 });
  runId = await page.evaluate(() => localStorage.getItem("tracemedic.run"));
  await page.screenshot({
    path: path.join(output, "cancelled.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Resume investigation", exact: true })
    .click();
  await page.locator(".diagnostic-card").waitFor({ timeout: 180000 });
  assert(
    (await page.evaluate(() => localStorage.getItem("tracemedic.run"))) ===
      runId,
    "Resume changed run ID",
  );
} else {
  runId =
    process.env.TRACE_QA_RUN_ID ||
    JSON.parse(
      await fs.readFile(
        path.join(root, "docs/evidence/v2/demo-real.json"),
        "utf8",
      ),
    ).id;
  await page.evaluate(
    (id) => localStorage.setItem("tracemedic.run", id),
    runId,
  );
  await page.reload();
  await page.locator(".diagnostic-card").waitFor({ timeout: 15000 });
}
await page.waitForFunction(
  async (id) => {
    const run = await (await fetch("/api/runs/" + id)).json();
    const diagnostic = run.events.findLast(
      (event) => event.kind === "diagnostic",
    );
    return (
      run.status === "completed" &&
      diagnostic &&
      run.events.some(
        (event) => event.kind === "session_end" && event.seq > diagnostic.seq,
      )
    );
  },
  runId,
  { timeout: 15000 },
);
const run = await (await fetch(base + "/api/runs/" + runId)).json();
await page.reload();
await page.locator(".diagnostic-card").waitFor();
assert(
  run.provider !== "scripted" && run.status === "completed",
  "Not a completed real-model trace",
);
assert(run.state.engine_version === "v2", "Wrong saved workflow");
assert(
  run.state.diagnostic.rendered_from_reviewed_records,
  "Missing reviewed-record rendering",
);
assert(
  ["coordinator", "investigator", "verifier"].every((role) =>
    run.state.visited.includes(role),
  ),
  "Missing role decisions",
);
assert(
  run.events.some((event) => event.kind === "cancelled"),
  "Missing actual cancellation",
);
assert(
  run.events.some((event) => event.kind === "resumed"),
  "Missing actual resume",
);
await page.locator(".quoted-sources button").first().click();
await page.locator(".source-line.cited-line").waitFor();
assert(
  (await page.locator(".source-line.cited-line").count()) === 1,
  "Citation did not highlight exact source line",
);
await page.getByRole("tab", { name: "Overview" }).click();
await page.locator(".reviewed-record-note").waitFor();
const layouts = [];
for (const [name, width, height] of [
  ["desktop", 1440, 1000],
  ["tablet", 900, 1100],
  ["mobile", 390, 844],
]) {
  await page.setViewportSize({ width, height });
  await page.evaluate(() => window.scrollTo(0, 0));
  const scrollWidth = await page.evaluate(
    () => document.documentElement.scrollWidth,
  );
  assert(scrollWidth <= width + 1, name + " has horizontal overflow");
  layouts.push({ name, width, scrollWidth });
  await page.screenshot({
    path: path.join(output, name + ".png"),
    fullPage: name === "desktop",
  });
  if (name === "desktop")
    await page.screenshot({ path: path.join(output, "workbench.png") });
}
await page.setViewportSize({ width: 1440, height: 1000 });
await page
  .locator(".diagnostic-card")
  .screenshot({ path: path.join(output, "diagnostic.png") });
await page
  .locator(".hypotheses-panel")
  .screenshot({ path: path.join(output, "causal-record.png") });
await page.getByRole("button", { name: "Benchmark", exact: true }).click();
await page.getByLabel("Benchmark version").selectOption("v1");
await page.getByText("Original V1 study:", { exact: false }).waitFor();
await page.getByLabel("Benchmark version").selectOption("v2");
await page
  .getByText("12 fresh reserved incidents.", { exact: false })
  .waitFor();
await page.getByRole("cell", { name: "v2-multi", exact: true }).waitFor();
await page.screenshot({
  path: path.join(output, "benchmark.png"),
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
assert(
  (await page.evaluate(() => document.documentElement.scrollWidth)) <= 391,
  "Benchmark table overflows mobile page",
);
await page.screenshot({
  path: path.join(output, "mobile-benchmark.png"),
  fullPage: true,
});
await page.setViewportSize({ width: 1440, height: 1000 });
await page
  .getByRole("button", { name: "Investigations", exact: false })
  .first()
  .click();
await page
  .getByRole("heading", { name: "Investigations", exact: true })
  .waitFor();
await page.getByRole("button", { name: "System & setup", exact: true }).click();
await page
  .getByRole("heading", { name: "System & setup", exact: true })
  .waitFor();
await fs.writeFile(
  path.join(output, "demo-real.json"),
  JSON.stringify(run, null, 2) + "\n",
);
const proof = {
  run_id: runId,
  browser: browser.version(),
  base,
  fresh_inference: real,
  layouts,
  errors,
};
await fs.writeFile(
  path.join(output, "browser-qa.json"),
  JSON.stringify(proof, null, 2) + "\n",
);
await fs.writeFile(
  path.join(output, real ? "browser-real-run.json" : "browser-replay.json"),
  JSON.stringify(proof, null, 2) + "\n",
);
await browser.close();
assert(!errors.length, errors.join("\n"));
console.log(JSON.stringify({ passed: true, runId, real, layouts, errors }));
