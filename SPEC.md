## Web Page

Goal: publish a simple static web page that uses `sweden_dataset.json` to let researchers explore Sweden drug trend time series as interactive line charts.

Primary audience:

- Drug Epidemiology research teams at Karolinska Institutet.
- Users who need a quick, reliable way to inspect extracted time series without reading raw spreadsheets or JSON directly.

Core product principles:

- Keep the site static and easy to host.
- Keep the interface clear, restrained, and research-oriented.
- Make provenance and notes visible, not hidden.
- Prefer simple exploration over dashboard complexity.
- Avoid any backend, database, login, or API layer.
- Build only the minimum needed for a useful first release.

Implementation decisions:

- Build the page as plain `HTML`, `CSS`, and `JavaScript`.
- Use `Chart.js` for chart rendering.
- Build a single-page site only.
- Load the hosted `sweden_dataset.json` file directly in the browser.
- Publish `sweden_dataset.json` and `sweden_dataset.csv` alongside the page in the same hosted static site.
- Host the site on GitHub Pages.
- Use the default GitHub Pages URL unless a custom domain is introduced later.

Why this approach:

- It minimizes infrastructure and maintenance.
- It keeps the project easy to hand over to external research teams.
- It creates a stable public URL tied to the repository.
- It keeps the data flow auditable because the page reads the same exported dataset that is shared with researchers.

Required functionality:

- Load the combined dataset from `sweden_dataset.json`.
- Let users select a single series to view as a line chart.
- Show chart title, unit, source, and notes near the chart.
- Show hover values by year.
- Provide direct download links for the JSON and CSV datasets.
- Work well on desktop and acceptably on mobile.

Recommended page structure:

- Overview section:
  - Brief explanation of the dataset.
  - Short description of included sources: `EUDA` and `FOHM`.
  - Download links for `JSON` and `CSV`.
- Chart explorer section:
  - One main chart shown at a time.
  - Controls for selecting source, metric, and series.
- Metadata section:
  - Series label.
  - Source description.
  - Source file or provenance details.
  - Notes attached to the series.
  - Compact year-value table below the chart.

Chart behavior:

- Use line charts only.
- Show a single selected series by default.
- Support hover tooltips with year and value.
- Do not include multi-series comparison in the MVP.

Design guidance:

- Use a clean, light visual design.
- Favor readability and visual calm over dashboard density.
- Use generous spacing and strong hierarchy for labels, metadata, and notes.
- Optimize for laptop and desktop use first, since the main audience is research teams.
- Preserve established project simplicity and avoid ornamental UI.

Data handling expectations:

- The page should treat `sweden_dataset.json` as the canonical input.
- The CSV remains a downloadable derived artifact.
- The page should display the normalized labels and notes already prepared by the extractor.
- No additional transformation service should exist outside the front end.
- The chart metadata panel must update with the selected series and remain visible without extra clicks.

Technical scope:

- Use a static site only.
- Use plain `HTML`, `CSS`, and `JavaScript`.
- Use `Chart.js` for interactive line charts.
- Do not introduce a backend framework or server-rendered application.

Hosting requirements:

- Host the web page on GitHub Pages.
- Keep deployment as simple as possible.
- Publish the site from the repository so updates are made through normal commits.
- Ensure the shared researcher URL points to the hosted chart page.
- Use a simple static deployment model suitable for direct repository handoff.

Out of scope for the first version:

- Authentication or user accounts.
- Custom backend APIs.
- Database storage.
- Editable annotations.
- Advanced dashboard layouts with many simultaneous charts.
- Multi-series comparison.
- Text search.
- Chart image export.
- Shareable URL state.

Success criteria:

- A researcher can open the page, understand what the dataset contains, and view a selected time series without documentation.
- A researcher can see the relevant notes and provenance for a charted series.
- The site can be deployed and updated with minimal operational work.
- The final handoff package is simple: cleaned datasets, repository, and public chart URL.
