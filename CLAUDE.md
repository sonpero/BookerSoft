# Personal Ebook Library

## Goal
Store my ebooks (EPUB, PDF) and read them from any device via a browser.

## Stack
- Backend: Python 3.12, FastAPI, SQLite
- Frontend: plain HTML + vanilla JS served by FastAPI
- Env management: uv

## Current state
Milestone 6 Part A — done. Frontend migrated from vanilla HTML/JS to
React + Vite + TypeScript (`frontend/`, strict mode throughout), applying
the visual direction in `docs/design/direction.md`: dark theme, serif
titles, a persistent sidebar, a cover grid on the library page, a book
detail page with inline metadata editing and star ratings. No backend
change; all 123 backend tests pass untouched. The build output
(`src/bookersoft/static/`) is gitignored — run `cd frontend && npm run
build` before starting the server; see README. EPUB reader (Part B) is
next.

## Milestones
1. Upload, list, download and delete — see acceptance criteria below
2. Metadata: auto-extraction + manual editing — see acceptance criteria below
3. Ratings and reviews — data model supports multiple users from the start
   (`user_id` on every row); until milestone 5 every row is attributed to
   the seeded `owner` user, since there is no login yet
4. Search and filters — see acceptance criteria below
5. Authentication: password login, owner-created accounts, per-user ownership
6. In-browser EPUB reader - see acceptance criteria below
7. Remote access (deployment behind HTTPS, session-protected public URL)

## Milestone 1 — acceptance criteria
Done when, in the browser:

Upload
- I can select one or several files at once and upload them
- Only `.epub` and `.pdf` are accepted, validated by content signature
  (ZIP magic bytes for EPUB, `%PDF` for PDF), not by extension alone
- Rejected files are reported by name with the reason; valid files in the
  same batch still go through
- After the upload finishes, a summary is shown: how many books were
  added, and the name and reason for every rejected or duplicate file
- Uploaded files land in `$DATA_DIR/books/`, one database row each
- A `sha256` of the file content is stored; re-uploading the same content
  is reported as a duplicate instead of creating a second row
- Stored filenames are derived from the `sha256` (e.g. `<sha256>.epub`),
  never from the original name; the original filename is kept in the
  database for display and download
- Original filenames with accents and spaces survive the round trip

List
- The list shows every book with its original filename, size and upload
  date, newest first
- An empty library shows a clear empty state, not a blank page

Download
- Each book can be downloaded from the list, through `GET /books/{id}/file`,
  served under its original filename (see File serving)

Delete
- Each book can be deleted from the list, behind an explicit confirmation
  naming the book
- Deletion is permanent: the database row goes first, then the file in
  `$DATA_DIR/books/`
- A missing file on disk never blocks deletion of the row

Out of scope: no metadata extraction, no covers, no search, no detail page.

## Milestone 2 — acceptance criteria
Done when, in the browser:

Detail page
- A book detail page exists at `/books/{id}`, reachable from the list
  - A `description` field is extracted (EPUB: `dc:description`; PDF: rarely
    available, leave empty) and shown on the detail page
  - Descriptions often contain HTML: strip tags at extraction time and store
    plain text. Never render extracted HTML as-is
  - Long descriptions are collapsed behind a native `<details>` disclosure
  - The field is editable like any other, and follows the same
    extracted-vs-manually-set rule

Extraction
- On upload, the following are extracted automatically: title, author,
  language, publication year, publisher, ISBN if present
  (EPUB: OPF metadata; PDF: document info dictionary)
- The cover image is extracted and saved to `$DATA_DIR/covers/`, and shown
  as a thumbnail in the book list; books without a cover get a neutral
  placeholder, never a broken image
- Extraction failure never blocks the upload: the book is still created,
  the filename is used as fallback title, and the book is flagged as
  needing attention
- Books uploaded before this milestone get their metadata extracted too

Manual editing
- Every metadata field is editable from the book detail page
- Each field records whether its current value was auto-extracted or
  manually set
- Re-extraction is always an explicit, manual action — never automatic,
  never triggered by upload of an already-known file
- A re-extraction never overwrites a manually set field; auto-extracted
  fields are refreshed normally
- A normalized (lowercased, accent-stripped) search column is written on
  insert and update, including manual edits — see milestone 4

Housekeeping
- A filter shows books needing attention: extraction failed, or title or
  author missing
- Deleting a book also deletes its cover file

Out of scope: no external metadata lookup (OpenLibrary, Google Books),
no bulk editing, no manual cover upload, no author deduplication.

## Milestone 3 — acceptance criteria
Done when, in the browser:
- On a book detail page I can set a rating (1-5) and write an optional
  review, then save
- The form shows my existing rating and review when I already have one;
  saving updates it instead of creating a second row
- I can delete my own review, behind a confirmation
- The detail page shows the average rating, the number of ratings, and
  every review with its author and date
- The book list shows the average rating next to each book
- A book with no rating shows "not rated yet", never 0 or an empty star row
- Rating without writing a review is allowed; a review without a rating is not

Out of scope: no review editing history, no likes, no comments on reviews,
no sorting or filtering by rating (milestone 4).

## Milestone 4 — acceptance criteria
Done when, in the browser:
- A single search box filters the book list on title and author
- Search is case- and accent-insensitive: "miserables" finds
  "Les Misérables". Query against the normalized search column
- Partial words match ("miser" finds "Misérables")
- Results update as I type, without a page reload
- Filters, combinable with search and with each other:
  - format (EPUB / PDF)
  - minimum average rating
  - uploaded by (user)
- Sort options: recently added, title, author, average rating
- Active filters are visible and clearable in one click
- The current search and filters live in the URL query string, so a
  filtered view can be bookmarked and shared
- Empty result shows a clear "no match" state, not a blank page

Out of scope: no full-text search inside book contents, no tags,
no saved searches.

## Milestone 6 — acceptance criteria
Part A — frontend migration, no behaviour change
- React + Vite, built to static files served by FastAPI. Single runtime,
  no CORS, no dev proxy in production
- Every existing screen works identically: list, filters, search, upload,
  detail page, metadata editing, reviews, login
- URL state (search and filters) still works, including bookmarking
- No backend change. All existing tests still pass untouched
- The migration applies the visual direction in `docs/design/direction.md`.
  This is not a neutral-styling pass: the design direction ships with the
  migration, not after it

Part B — EPUB reader
- `/books/{id}/read` opens the book in the browser, for EPUB only.
  PDFs keep the download link, no in-browser PDF reader
- Reader shows: paginated content, table of contents, font size control,
  light/dark following `prefers-color-scheme`
- Reading position is stored in `localStorage`, per device, keyed by book id
- Reopening a book returns to the last position on that device
- The reader streams the file through the authenticated endpoint; the EPUB
  is never exposed as a static file
- Keyboard navigation: arrows for pages, Escape to exit

## Design references
Visual references live in `docs/design/`. Read the relevant file when
working on that screen.
- `direction.md` — the visual direction: palette, typography, layout rules.
  Authoritative for all styling
- `book-detail-reference.png` — structure and hierarchy of the book detail
  page only; style comes from `direction.md`, not from this image

## Storage
Everything persistent lives under one configurable data directory
(env var `DATA_DIR`, defaults to `./data` in dev):
- `$DATA_DIR/library.db` — SQLite database
- `$DATA_DIR/books/` — uploaded book files
- `$DATA_DIR/covers/` — extracted cover images

Never hardcode storage paths, and never write persistent data outside
`DATA_DIR`. The database stores file paths, not file contents. This keeps
deployment to a mounted volume (Railway, VPS, self-hosted) a configuration
change, not a refactor.

`./data/` is gitignored. Never commit book files, covers or the database.

SQLite foreign keys are off by default: enable `PRAGMA foreign_keys = ON`
on every connection, otherwise `ON DELETE CASCADE` silently does nothing.

## File serving
- Book files are NEVER exposed as a static directory. No `StaticFiles`
  mount over the data directory.
- Downloads go through `GET /books/{id}/file`: it resolves the current
  user, looks up the stored path from the database by id, and streams
  the file back.
- File paths are always resolved from database records, never built
  from user-supplied strings.
- Correct MIME types (`application/epub+zip`, `application/pdf`) and
  RFC 5987 encoding for filenames with accents in `Content-Disposition`.
- Record each download (user, book, timestamp).

## Users and access
The library is private and invite-only: a small, hand-picked group of
people I know personally. There is no public signup.

- Every route that touches user data depends on a single `current_user`
  resolver. Before milestone 5 it returns the seeded `owner` user with
  no authentication. Milestone 5 replaces that one function and nothing
  else — do not scatter auth checks across routes.
- Every user-generated row (book, review, download) carries a `user_id`
  owner from the very first migration.
- Until milestone 5, anyone can delete any book. From milestone 5 on, only
  the uploader and the library owner can delete a book.

## Authentication (milestone 5)
- Username + password, hashed with argon2 through a maintained library.
  Never implement password hashing by hand.
- Accounts are created by the owner through a CLI command. No self-signup,
  no email verification, no password reset flow: the owner resets a
  password with the same command.
- Login sets a signed session cookie: `HttpOnly`, `Secure`, `SameSite=Lax`,
  with a long expiry — this is a personal library, not a bank.
- Rate-limit failed login attempts per IP.
- The whole app requires a valid session, except the login page itself.
- Session secret comes from an env var, never committed.
- Not OAuth: no external provider, no client secret, no callback URLs to
  reconfigure at deployment. The flows that make passwords painful
  (signup, verification, reset) don't exist here.

## Ratings and reviews
- One rating (1-5) and one optional review text per user per book,
  enforced by a `UNIQUE(user_id, book_id)` constraint.
- A user can edit or delete their own review, and only their own.
- Book pages show the average rating and all reviews.
- Reviews and download records are deleted with their book
  (`ON DELETE CASCADE`).

## Frontend
Plain HTML + vanilla JS until milestone 6. The backend exposes a JSON API,
so the frontend stays disposable by design.

Use native HTML elements before reaching for JavaScript: `<details>` for
disclosure and dropdowns, CSS Grid for layout, `<dl>` for metadata blocks.
Keep JS for actual state.

At milestone 6 (EPUB reader), migrate to React + Vite, built to static
files and served by FastAPI. Single runtime, single deployment, no CORS.
Not Next.js: SSR and SEO are worthless behind auth, and its server layer
would duplicate FastAPI.

The reader remembers the last position per device only, in `localStorage`.
No server-side reading state, no cross-device sync — deliberately out of scope.

## Design references
Visual references live in `docs/design/`. Read the relevant file when
working on that screen.
- `book-detail-reference.png` — target layout for the book detail page
  (structure and hierarchy only; use our own neutral palette, not the
  colors or branding from the reference)

## Principles
- Every increment must be demonstrable in the browser
- No new dependency without discussing it first. Pre-approved for
  milestone 1: fastapi, uvicorn, pytest, httpx, python-multipart
- Routes are plain `def`, not `async def`. SQLite and file I/O are
  synchronous here, and FastAPI runs sync routes in a threadpool.
  No `aiosqlite`, no `aiofiles`, no async test plumbing
- Readable code over clever code: short functions, explicit names,
  early returns over nesting. No abstraction introduced before the
  second concrete use case — no repository pattern, no service layer,
  no dependency injection framework
- Type hints on every function signature; validation belongs to Pydantic
  models, not to hand-written checks in routes
- Errors surface as clear HTTP responses, never as bare 500s

## Testing
Tests exist so the loop can close without me clicking through the browser.
They are the executable form of the acceptance criteria.

- pytest, with FastAPI's `TestClient`. Tests run against a temporary
  `DATA_DIR` and a fresh database, never against my real library
- From milestone 1 on, tests are written before the implementation:
  sketch the routes and Pydantic schemas, then write the tests from the
  acceptance criteria, then implement until they pass
- Every acceptance criterion has at least one test. A milestone is not
  done until all of them pass
- Tests ship in the same commit as the feature they cover
- Priority targets: file validation (a `.jpg` renamed `.epub` is rejected),
  duplicate detection by hash, two different books sharing the original
  filename `book.epub` coexisting, accented filenames round-tripping,
  deletion with a missing file on disk, path traversal attempts on the
  download endpoint, every uploaded book being attributed to the seeded
  `owner` user
- Test names describe the behaviour: `test_renamed_jpg_is_rejected`,
  not `test_upload_2`
- No mocking of the filesystem or the database; use real temporary ones
- Fixtures include real minimal `.epub` and `.pdf` files in `tests/fixtures/`
- Coverage percentage is not a goal. Cover what breaks

## Conventions
- Code, identifiers, tables and comments in English
- Commit messages in English, conventional commits format
  (e.g. `feat: add upload endpoint`, `fix: handle accented filenames`)
- Domain vocabulary: book, author, cover, review, rating, download, library