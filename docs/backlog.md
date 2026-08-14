- Category classification and filter (tech, jeunesse, littérature...) —
  open question: where does the category come from (manual, dc:subject,
  external lookup)? One category per book or several?
- In-browser PDF reader (pdf.js) — deferred, not excluded. Decide after
  deployment, based on the actual share of PDFs in the library
- Backup: CLI command producing a consistent SQLite snapshot (.backup),
  plus incremental sync of $DATA_DIR/books and covers to local storage.
  Content-hash filenames make the sync idempotent. Needed once other
  users start uploading — until then the local library is the backup
- Playwright as frontend devDependency — layout/touch-target scanner, and
  possibly end-to-end tests for the main flows. Decide scope before
  installing