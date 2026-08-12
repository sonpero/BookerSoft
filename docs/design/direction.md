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

## Detail page
Follow `book-detail-reference.png` for structure, this file for style.

## Rules
- No gradients, no glows, no decorative illustration
- One accent color only. No secondary accent, no status colors beyond
  a muted red for destructive actions
- Every color and spacing value is a CSS custom property at :root, so the
  React migration inherits them unchanged