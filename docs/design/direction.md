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
- Book list: cover on the left, metadata to its right, one book per row.
  Not a pure grid — scanning for a specific title matters more here than
  browsing visually
- Covers have soft rounded corners (6px) and a subtle drop shadow, as if
  resting on the surface
- Books without a cover get a typographic placeholder: title set in the
  serif on --surface-hi, never a broken-image icon
- Generous whitespace. Content column max ~1100px, centered

## Detail page
Follow `book-detail-reference.png` for structure, this file for style.

## Rules
- No gradients, no glows, no decorative illustration
- One accent color only. No secondary accent, no status colors beyond
  a muted red for destructive actions
- Every color and spacing value is a CSS custom property at :root, so the
  React migration inherits them unchanged