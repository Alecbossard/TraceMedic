import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const recorded = JSON.parse(
  await fs.readFile(path.join(root, "docs/evidence/v2/demo-real.json"), "utf8"),
);
const runId = process.env.TRACE_QA_RUN_ID || recorded.id;
const base = process.env.TRACE_QA_URL || "http://127.0.0.1:8000";
const output = path.resolve(
  root,
  process.env.TRACE_REFRESH_OUTPUT || "docs/evidence/ui-refresh",
);
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch(
  process.platform === "win32" && process.env.TRACE_QA_BROWSER !== "chromium"
    ? { channel: "msedge", headless: true }
    : { headless: true },
);
const page = await browser.newPage();
let release;
const gate = new Promise((resolve) => {
  release = resolve;
});
let requested;
const requestedGate = new Promise((resolve) => {
  requested = resolve;
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/motion-features-*.js", async (route) => {
  requested();
  await gate;
  await route.continue().catch(() => {});
});
try {
  await page.goto(base + "/?run=" + encodeURIComponent(runId), {
    waitUntil: "domcontentloaded",
  });
  await Promise.race([
    requestedGate,
    new Promise((_, reject) =>
      setTimeout(
        () => reject(Error("Animation feature request was not intercepted")),
        5000,
      ),
    ),
  ]);
  // The model trace and source navigation must work before animation features arrive.
  await page.locator(".finding-preview").waitFor({ timeout: 10000 });
  await page.locator(".quoted-sources button").first().click();
  await page.locator(".source-line.cited-line").waitFor({ timeout: 10000 });
  if (errors.length) throw Error(errors.join("\n"));
  release();
  const proof = {
    status: "passed",
    run_id: runId,
    browser: browser.version(),
    fresh_inference: false,
    scope:
      "Cold deep link and exact-line navigation succeed while the lazy animation feature request is deliberately blocked.",
    errors,
  };
  await fs.writeFile(
    path.join(output, "cold-start.json"),
    JSON.stringify(proof, null, 2) + "\n",
  );
  console.log(JSON.stringify(proof));
} finally {
  release();
  await browser.close();
}
