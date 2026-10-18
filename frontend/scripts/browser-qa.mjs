import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const output = path.join(root, process.env.TRACE_QA_OUTPUT || "docs/evidence");
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch(
  process.platform === "win32"
    ? { channel: "msedge", headless: true }
    : { headless: true },
);
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const base = process.env.TRACE_QA_URL || "http://127.0.0.1:8000";
await page.goto(base);
await page
  .getByRole("button", { name: "Start investigation", exact: true })
  .waitFor();
await page
  .getByRole("heading", { name: "Telemetry gateway", exact: true })
  .waitFor();
await page
  .locator(".model-card strong")
  .filter({ hasText: "Checking model" })
  .waitFor({ state: "hidden" });
await page.screenshot({
  path: path.join(output, "desktop-empty.png"),
  fullPage: true,
});
await page
  .getByRole("textbox", { name: "Search incidents" })
  .fill("nonsense-no-match");
await page.getByText("No matching incidents.").waitFor();
await page.getByRole("textbox", { name: "Search incidents" }).fill("");
let runId =
  process.env.TRACE_QA_RUN_ID ||
  (process.argv.includes("--replay")
    ? JSON.parse(await fs.readFile(path.join(output, "demo-real.json"), "utf8"))
        .id
    : null);
if (process.argv.includes("--real")) {
  await page
    .getByRole("button", { name: "Start investigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Cancel investigation", exact: true })
    .waitFor();
  // Exercise real cooperative cancellation and resume through the browser.
  await page
    .getByRole("button", { name: "Cancel investigation", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Resume investigation", exact: true })
    .waitFor({ timeout: 120000 });
  await page.screenshot({
    path: path.join(output, "cancelled.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Resume investigation", exact: true })
    .click();
  await page.locator(".diagnostic-card").waitFor({ timeout: 180000 });
  runId = await page.evaluate(() => localStorage.getItem("tracemedic.run"));
}
if (runId) {
  await page.evaluate(
    (id) => localStorage.setItem("tracemedic.run", id),
    runId,
  );
  await page.reload();
  await page.locator(".diagnostic-card").waitFor({ timeout: 10000 });
  await page.locator(".citations button").first().click();
  await page.locator(".source-code").waitFor();
  await page.getByRole("tab", { name: "Activity" }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page
    .locator(".timeline")
    .evaluate((el) => (el.scrollTop = el.scrollHeight));
  await page.screenshot({
    path: path.join(output, "desktop-investigation.png"),
  });
  await page.screenshot({
    path: path.join(output, "desktop-full.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Overview" }).click();
  await page
    .locator(".diagnostic-card")
    .screenshot({ path: path.join(output, "diagnostic.png") });
  const run = await (await fetch(base + "/api/runs/" + runId)).json();
  await fs.writeFile(
    path.join(output, "demo-real.json"),
    JSON.stringify(run, null, 2) + "\n",
  );
  if (run.provider === "scripted" || run.status !== "completed")
    throw Error(
      "Browser run did not complete with a real provider: " + run.status,
    );
}
const layouts = [];
for (const [name, width, height] of [
  ["tablet", 900, 1100],
  ["mobile", 390, 844],
]) {
  await page.setViewportSize({ width, height });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(output, `${name}-${runId ? "investigation" : "empty"}.png`),
  });
  const measurement = await page.evaluate(() => ({
    width: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  layouts.push({ name, ...measurement });
  if (measurement.scrollWidth > width + 1)
    throw Error(`${name} has horizontal overflow`);
}
for (const name of ["Investigations", "Benchmark", "System & setup"]) {
  if (
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .click();
  await page.getByRole("button", { name, exact: false }).first().click();
  await page.locator("h1").waitFor();
}
const links = await page
  .locator("a")
  .evaluateAll((nodes) => nodes.map((n) => n.href));
await page.setViewportSize({ width: 1440, height: 1000 });
await page
  .getByRole("button", { name: "Incident workbench", exact: false })
  .first()
  .click();
await fs.writeFile(
  path.join(output, "browser-qa.json"),
  JSON.stringify(
    {
      browser: browser.version(),
      base,
      run_id: runId || null,
      real_run: process.argv.includes("--real"),
      layouts,
      errors,
      links,
    },
    null,
    2,
  ) + "\n",
);
await browser.close();
if (errors.length) throw Error(errors.join("\n"));
console.log(JSON.stringify({ passed: true, runId, layouts, errors }));
