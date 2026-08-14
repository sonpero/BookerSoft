# Visual direction

Dark, quiet, and typographic. The covers are the only saturated color on
screen — everything else recedes so they stand out as objects.

## Palette
Dark theme is the default and only theme for now.

--bg           #0F0E0D   page background, near-black warm
--surface      #1A1917   cards, sidebar, raised areas
--surface-hi   #252320   hover, active rows
--border       #322F2B   hairlines, 1px, never heavier
--text         #EDE8E0   primary text, warm off-white
--text-muted   #948C80   authors, dates, metadata labels
--accent       #C8A45C   aged brass: links, buttons, active nav, stars

Warm neutrals, never blue-grey. The accent is used sparingly — a page
should have two or three accent elements, not ten.

## Typography
- Book titles and page headings: a serif. It signals "book" and gives the
  interface its character. Fraunces or Newsreader from Google Fonts
- Everything else (labels, buttons, metadata, forms): system sans stack
- Titles are not shouted: normal weight, generous size, tight line-height

## Layout
- Persistent left sidebar for navigation (library, upload, account),
  narrow, icon + label
- Library is a responsive grid of covers, not a list: browsing by cover
  matters more here than scanning a table. Columns auto-fill the width
  remaining after the sidebar; covers stay large regardless of window size
- Below each cover: title, then author, then rating — nothing else. Actions
  (download, delete) live on the book's own detail page, not on the tile
- Covers have soft rounded corners (6px) and a subtle drop shadow, as if
  resting on the surface. On this near-black background the shadow needs a
  strong enough alpha (and a hairline highlight on the top edge) to actually
  read — a faint shadow just disappears
- Books without a cover get a typographic placeholder: title set in the
  serif on --surface-hi, never a broken-image icon
- Search sits full-width above the grid, taller than other inputs, with a
  clearly rounded corner (~12px) to read as the page's primary action. The
  filter row (format, rating, uploader, sort) sits left-aligned below it;
  "needs attention" is the odd one out (a state toggle, not a narrowing
  filter) and sits pushed to the far right
- Generous whitespace. Every page fills the full width after the sidebar —
  library grid and book detail alike, no empty gutter, no page-level
  max-width. Only self-contained forms (upload, the review form) stay
  narrow, for readability, not because the page itself is capped
- The book description sits directly beside the metadata fields, not below
  them, using the width that frees up. Clamped to roughly the metadata
  block's height with a Read more / Read less toggle, rather than letting
  a long description run on much taller than its neighbor
- the reader renders book text in black on white; the surrounding chrome stays dark

## Mobile
- Breakpoint: 768px. Below it, the persistent sidebar is replaced by a
  slim sticky top bar (brand, account) and a fixed bottom navigation bar;
  content takes the full width, no side rail
- Touch targets are at least 44px in both dimensions below the
  breakpoint — buttons, button-styled links, and form fields (inputs,
  selects, checkboxes) alike. A visual control can be smaller than that
  only if it sits inside a larger tappable row or label that itself
  reaches 44px
- Nothing essential is `:hover`-only. Any action that only reveals itself
  on hover on desktop (per-item controls on a card, for example) must be
  visible unconditionally below the breakpoint — touch has no reliable
  hover
- The reader paginates above the breakpoint and scrolls continuously
  below it; controls that only make sense for pagination (page-turn
  arrows) aren't shown in scroll mode
- Check new screens across the full width range down to 320px, not just
  at the breakpoint — some failures (a fixed `min-width` forcing an
  element wider than its container, for example) are continuous with
  viewport width and only show up well below 768px, not right at it
- Verify at an actual narrow viewport (390px or less), not by shrinking a
  desktop browser window — a resized browser window has its own minimum
  width and won't reach real phone widths or reproduce mobile layout
  behavior

## Detail page
Follow `book-detail-reference.png` for structure, this file for style.

## Rules
- No gradients, no glows, no decorative illustration
- One accent color only. No secondary accent, no status colors beyond
  a muted red for destructive actions
- Every color and spacing value is a CSS custom property at :root, so the
  React migration inherits them unchanged