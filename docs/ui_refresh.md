# TraceMedic interface refresh

The workbench is an investigation tool. Its visual hierarchy now prioritizes the selected incident, the current run and its evidence rather than introductory marketing panels.

## Design and interaction

- Graphite navigation, neutral surfaces, a single indigo action color, restrained borders and compact controls. The original hero, slogans and introductory agent banner are removed.
- A searchable incident rail with real Original/V2 collection filters. On small screens it opens on demand instead of consuming the viewport.
- Three accessible keyboard-navigable run views: **Overview**, **Activity** and **Sources**. Opening a citation selects Sources and highlights the actual captured line; it does not synthesize another excerpt.
- The source viewer includes captured-file navigation, basic lexical coloring, line numbers, source copy, checksum metadata and complete audit export. Files remain immutable. Lexical coloring is presentation only, not a Python parser or editor.
- Activity filters and expandable event payloads reveal actual decisions and tool results. The latest running action is shown without simulated activity.
- Searchable run history; benchmark latency/call comparison charts plus the full outcome table and existing semantic limits; a compact system environment view.
- `Ctrl+K` on Windows/Linux, `⌘K` on macOS, or `/` outside inputs opens quick navigation. Search, arrows, Enter and Escape work. Mobile navigation traps focus and restores it when dismissed.
- Brief route/tab fades and animated chart changes. The operating system's reduced-motion preference disables transforms and CSS dialog/drawer animations. Source/finding navigation avoids smooth scrolling under that preference.

## Selected libraries

| Dependency | Use | Primary reference |
| --- | --- | --- |
| Motion 14.3.0 | Lazy-loaded animation features, route/tab transitions and chart values | [Bundle-size guidance](https://motion.dev/docs/react-reduce-bundle-size), [reduced motion](https://motion.dev/docs/react-motion-config) |
| Radix Dialog 1.3.1 | Command menu and mobile navigation: modal semantics, keyboard handling and focus management | [Dialog documentation](https://www.radix-ui.com/primitives/docs/components/dialog) |
| Radix Tooltip 1.4.1 | Labels for compact source/export controls | [Primitives](https://www.radix-ui.com/primitives/docs/components) |
| Fontsource Geist / Geist Mono 5.3.0 | Locally served variable typography; Latin font assets only | [Geist](https://fontsource.org/fonts/geist/use), [Fontsource installation](https://fontsource.org/docs/getting-started/install) |

React/Vite and Lucide are retained. No hosted font service, component subscription or new account is needed. Font license copies are included in `frontend/public/licenses/`.

The local production build reports approximately **117.5 kB gzip** for initial JavaScript, **17.8 kB gzip** for deferred Motion features, **13.5 kB gzip** for CSS and **52.5 kB** for the two variable fonts. These are build artifact sizes, not a network performance benchmark. There is an intentional payload increase for accessible primitives and animation support.

## Verification

`frontend/scripts/browser-refresh.mjs` checks actual API-backed behavior using a previously completed real-model trace. It covers source identity and line highlighting, clipboard content (allowing Windows clipboard line endings), audit download, activity filtering, finding focus, command-menu selection, history search, benchmark version/metric switching, mobile menus/filters and reduced motion. Screenshots wait for transition settlement and fonts.

- Automated WCAG A/AA checks using axe on **11 views**: desktop overview/sources/activity/history/benchmark/system, command menu, empty overview, mobile overview/sources/navigation. No violations in this automated scope; this is not a comprehensive manual accessibility certification.
- **10 overflow checks** at 900, 390 and 360 pixels, covering the workbench, sources, incident browser, benchmark, system and history.
- Original V1 trace reopens in the redesigned workbench and passes its compatibility browser script.
- A separate fresh Qwen investigation was created, actually cancelled, resumed under the same ID and completed. Its full trace and `fresh_inference: true` browser proof are in [`evidence/ui-refresh/real-session/`](evidence/ui-refresh/real-session/). The first completed real run is also retained: its capture script initially asserted a citation before the new tab finished entering; the assertion now awaits the highlighted line.

The main [`browser-qa.json`](evidence/ui-refresh/browser-qa.json) is explicitly a replay/interaction check, not fresh inference. Historical V1/V2 evidence and all frozen benchmark outcomes remain unchanged. The refresh does not establish any additional diagnostic accuracy.

With the API serving on port 8000:

```powershell
npm ci --prefix frontend
npm run format:check --prefix frontend
npm run build --prefix frontend
npm run test:ui --prefix frontend
npm audit --prefix frontend --audit-level=high
```

CI runs both historical replay scripts and the new interaction/accessibility suite in Chromium. Local validation uses installed Microsoft Edge through Playwright. To test a different saved real trace, set `TRACE_QA_RUN_ID`; `TRACE_REFRESH_OUTPUT` controls new screenshot/proof output.
