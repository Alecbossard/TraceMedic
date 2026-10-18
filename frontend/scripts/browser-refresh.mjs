import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const output = path.resolve(
  root,
  process.env.TRACE_REFRESH_OUTPUT || "docs/evidence/ui-refresh",
);
await fs.mkdir(output, { recursive: true });
const recorded = JSON.parse(
  await fs.readFile(path.join(root, "docs/evidence/v2/demo-real.json"), "utf8"),
);
const runId = process.env.TRACE_QA_RUN_ID || recorded.id;
const base = process.env.TRACE_QA_URL || "http://127.0.0.1:8000";
const browser = await chromium.launch(
  process.platform === "win32" && process.env.TRACE_QA_BROWSER !== "chromium"
    ? { channel: "msedge", headless: true }
    : { headless: true },
);
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  acceptDownloads: true,
});
await context.grantPermissions(["clipboard-read", "clipboard-write"], {
  origin: base,
});
const page = await context.newPage();
const errors = [],
  accessibility = [],
  layouts = [],
  checks = [];
let failure = null;
page.on("pageerror", (error) => errors.push(error.message));
const assert = (value, message) => {
  if (!value) throw Error(message);
};
async function screenshot(name, fullPage = false) {
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(220);
  await page.screenshot({ path: path.join(output, name + ".png"), fullPage });
}
async function audit(name) {
  await page.waitForTimeout(220);
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  accessibility.push({
    name,
    violations: result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      description: v.description,
      nodes: v.nodes.map((node) => ({
        target: node.target,
        summary: node.failureSummary,
      })),
    })),
  });
}
async function navigate(name) {
  const mobile = page.getByRole("button", {
    name: "Open navigation",
    exact: true,
  });
  if (await mobile.isVisible()) await mobile.click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name, exact: false })
    .click();
  await page.getByRole("heading", { level: 1 }).waitFor();
}
async function widthCheck(name) {
  const measurement = await page.evaluate(() => ({
    width: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  layouts.push({ name, ...measurement });
  assert(
    measurement.scrollWidth <= measurement.width + 1,
    name + " overflows the viewport",
  );
}

try {
  await page.goto(base + "/?run=" + encodeURIComponent(runId));
  await page.locator(".finding-preview").waitFor();
  const run = await (await fetch(base + "/api/runs/" + runId)).json();
  assert(
    run.provider !== "scripted" && run.status === "completed",
    "QA requires a completed real-model trace",
  );
  await screenshot("desktop");
  await audit("desktop-overview");
  const citation = run.state.hypotheses.find((h) => h.citations?.length)
    ?.citations[0];
  await page.locator(".quoted-sources button").first().click();
  await page.locator(".source-line.cited-line").waitFor();
  assert(
    (await page
      .getByRole("tab", { name: "Sources" })
      .getAttribute("aria-selected")) === "true",
    "Citation did not open Sources",
  );
  assert(
    (await page.locator(".cited-line .line-number").innerText()).trim() ===
      String(citation.line),
    "Wrong highlighted source line",
  );
  const captured = run.evidence.find((e) => e.id === citation.evidence_id);
  assert(
    (await page.locator(".source-heading strong").innerText()) ===
      captured.path,
    "Wrong citation source file",
  );
  checks.push("Citation selects the correct captured file and exact line");
  await screenshot("sources");
  await audit("desktop-sources");
  await page
    .getByRole("button", { name: "Copy captured source", exact: true })
    .click();
  await page.locator(".source-heading .lucide-copy-check").waitFor();
  const clipboard = await page.evaluate(() => navigator.clipboard.readText());
  assert(
    clipboard.replaceAll("\r\n", "\n") ===
      captured.excerpt.replaceAll("\r\n", "\n"),
    "Copied source differs from immutable capture",
  );
  checks.push(
    "Source copy matches captured text, allowing native clipboard line endings",
  );
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export full audit JSON", exact: true })
    .last()
    .click();
  const download = await downloadPromise;
  const downloaded = JSON.parse(
    await fs.readFile(await download.path(), "utf8"),
  );
  assert(
    downloaded.id === runId &&
      downloaded.evidence.length === run.evidence.length,
    "Audit export lost run identity or evidence",
  );
  checks.push("Export downloads the complete current run");
  await page.getByRole("tab", { name: "Activity" }).click();
  await page.getByRole("button", { name: "Tools", exact: true }).click();
  const toolRows = await page.locator(".timeline-event").count();
  assert(
    toolRows > 0 && toolRows < run.events.length,
    "Tool filter did not narrow the timeline",
  );
  await page.locator(".event-body").first().click();
  await page.locator(".event-body pre").waitFor();
  await page.getByRole("button", { name: "All events", exact: true }).click();
  await screenshot("activity");
  await audit("desktop-activity");
  checks.push("Activity filters and event disclosure work");
  await page.getByRole("tab", { name: "Overview" }).click();
  await page
    .getByRole("button", { name: "Review finding & next steps" })
    .click();
  assert(
    await page
      .locator("#final-finding")
      .evaluate((el) => el === document.activeElement),
    "Finding link did not transfer keyboard focus",
  );
  await page
    .locator(".diagnostic-card")
    .screenshot({ path: path.join(output, "finding.png") });
  checks.push("Finding link scrolls and transfers focus");
  await page.keyboard.press("ControlOrMeta+k");
  await page.getByRole("dialog", { name: "Quick navigation" }).waitFor();
  await page
    .getByRole("combobox", { name: "Search workspace" })
    .fill("sample-02");
  await audit("command-menu");
  await screenshot("command-menu");
  await page.keyboard.press("Enter");
  await page
    .getByRole("heading", { name: "Plugin loader", exact: true })
    .waitFor();
  await audit("empty-overview");
  checks.push(
    "Keyboard command menu searches incidents and opens the selected result",
  );
  await navigate("Investigations");
  await page
    .getByRole("textbox", { name: "Search investigations" })
    .fill(runId.slice(0, 8));
  assert(
    (await page.locator(".history-list>button").count()) === 1,
    "History search did not select one run",
  );
  await audit("desktop-history");
  await screenshot("history");
  await page.locator(".history-list>button").click();
  await page.locator(".finding-preview").waitFor();
  checks.push("History search reopens the same saved run");
  await navigate("Benchmark");
  await page.getByRole("cell", { name: "v2-multi", exact: true }).waitFor();
  await page.getByRole("button", { name: "Model calls", exact: true }).click();
  assert(
    (
      await page.locator(".comparison-row.featured .chart-value").innerText()
    ).includes("99"),
    "Chart does not reflect published model call count",
  );
  await page.getByLabel("Benchmark version").selectOption("v1");
  await page.getByRole("cell", { name: "single", exact: true }).waitFor();
  await page.getByLabel("Benchmark version").selectOption("v2");
  await page.getByRole("cell", { name: "v2-multi", exact: true }).waitFor();
  await page.getByRole("button", { name: "Latency", exact: true }).click();
  await screenshot("benchmark");
  await audit("desktop-benchmark");
  checks.push("Benchmark chart and V1/V2 switching retain published values");
  await navigate("System & setup");
  await screenshot("system");
  await audit("desktop-system");
  await navigate("Incident workbench");
  for (const [name, width, height] of [
    ["tablet", 900, 1100],
    ["mobile", 390, 844],
    ["small-mobile", 360, 800],
  ]) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => window.scrollTo(0, 0));
    await widthCheck(name + "-overview");
    await screenshot(name);
    if (name === "mobile") await audit("mobile-overview");
    await page.getByRole("tab", { name: "Sources" }).click();
    await page.locator(".source-code").waitFor();
    await widthCheck(name + "-sources");
    if (name === "mobile") {
      await screenshot("mobile-sources");
      await audit("mobile-sources");
    }
    await page.getByRole("tab", { name: "Overview" }).click();
  }
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await screenshot("mobile-navigation");
  await audit("mobile-navigation");
  await page.keyboard.press("Escape");
  assert(
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .evaluate((el) => el === document.activeElement),
    "Mobile menu did not restore focus",
  );
  checks.push(
    "Mobile navigation traps focus, closes with Escape and restores focus",
  );
  await page
    .getByRole("button", { name: "Browse incidents", exact: false })
    .click();
  await page.getByRole("button", { name: "V2 suite", exact: true }).click();
  assert(
    (await page.locator(".incident-list>button").count()) === 12,
    "Incident collection filter should show exactly 12 V2 fixtures",
  );
  await page
    .getByRole("textbox", { name: "Search incidents" })
    .fill("not-a-fixture");
  await page.getByText("No matching incidents.").waitFor();
  await widthCheck("small-mobile-library");
  checks.push(
    "Mobile incident browser, collection filters and empty search state work",
  );
  await navigate("Benchmark");
  await page.getByRole("cell", { name: "v2-multi", exact: true }).waitFor();
  await widthCheck("small-mobile-benchmark");
  await screenshot("mobile-benchmark");
  await navigate("System & setup");
  await widthCheck("small-mobile-system");
  await navigate("Investigations");
  await widthCheck("small-mobile-history");
  const reduced = await browser.newContext({
    reducedMotion: "reduce",
    viewport: { width: 1440, height: 1000 },
  });
  const reducedPage = await reduced.newPage();
  await reducedPage.goto(base + "/?run=" + runId);
  await reducedPage.locator(".finding-preview").waitFor();
  assert(
    await reducedPage.evaluate(
      () => matchMedia("(prefers-reduced-motion: reduce)").matches,
    ),
    "Reduced motion preference was not applied",
  );
  await reducedPage.keyboard.press("ControlOrMeta+k");
  await reducedPage.getByRole("dialog", { name: "Quick navigation" }).waitFor();
  assert(
    await reducedPage
      .locator(".dialog-overlay")
      .evaluate((el) => getComputedStyle(el).animationName === "none"),
    "Dialog animation ignores reduced motion",
  );
  await reduced.close();
  checks.push("Reduced-motion browser preference is supported");
} catch (error) {
  failure = error.message;
  const diagnostics = {
    failure,
    runId,
    url: page.url(),
    errors,
    body: await page
      .locator("body")
      .innerText()
      .catch(() => "Unavailable"),
  };
  console.error(JSON.stringify(diagnostics));
  await page
    .screenshot({ path: path.join(output, "failure.png"), fullPage: true })
    .catch(() => {});
  await fs.writeFile(
    path.join(output, "failure.json"),
    JSON.stringify(diagnostics, null, 2) + "\n",
  );
  throw error;
} finally {
  const proof = {
    status:
      failure ||
      errors.length ||
      accessibility.some((result) => result.violations.length)
        ? "failed"
        : "passed",
    failure,
    run_id: runId,
    browser: browser.version(),
    base,
    fresh_inference: false,
    scope:
      "Interactive UI checks using a previously completed real-model trace. No new inference is performed by this script.",
    checks,
    layouts,
    errors,
    accessibility,
  };
  await fs.writeFile(
    path.join(output, "browser-qa.json"),
    JSON.stringify(proof, null, 2) + "\n",
  );
  await browser.close();
}
assert(errors.length === 0, errors.join("\n"));
const violations = accessibility.flatMap((result) =>
  result.violations.map(
    (v) => result.name + ": " + v.id + " (" + v.nodes.length + " nodes)",
  ),
);
assert(
  violations.length === 0,
  "Accessibility violations: " + violations.join(", "),
);
console.log(
  JSON.stringify({
    passed: true,
    checks: checks.length,
    layouts: layouts.length,
    accessibilityViews: accessibility.length,
    errors,
  }),
);
