import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ePub from "epubjs";
import type { NavItem, Rendition } from "epubjs";

import { downloadUrl, fetchBookDetail, fetchBookFile, type BookDetail } from "../api";
import styles from "./ReaderPage.module.css";

type Status = "loading" | "not-found" | "not-epub" | "ready" | "error";

const MIN_FONT_SCALE = 70;
const MAX_FONT_SCALE = 200;
const FONT_SCALE_STEP = 10;
const DEFAULT_FONT_SCALE = 100;

// The reading surface itself stays a plain black-on-white page — that's the
// content's own theme, independent of the app's dark chrome around it.
//
// Every rule needs !important: some EPUBs hardcode their own text/background
// colors (inline styles or their own stylesheet), which would otherwise win
// the cascade. "body *" (not just "body") is required too — color is
// inherited, and inheritance loses to any rule that targets an element
// directly, even a plain one with no !important. A book's own unadorned
// "p { color: black }" would otherwise still beat a themed "body" rule for
// every paragraph.
const READER_THEME = {
  "html, body": {
    background: "#ffffff !important",
    color: "#000000 !important",
  },
  "body *": {
    "background-color": "transparent !important",
    color: "#000000 !important",
    "border-color": "#cccccc !important",
  },
};

function TocList({ items, onSelect }: { items: NavItem[]; onSelect: (href: string) => void }) {
  return (
    <ul className={styles.toc}>
      {items.map((item) => (
        <li key={item.id}>
          <button type="button" onClick={() => onSelect(item.href)}>
            {item.label.trim()}
          </button>
          {item.subitems && item.subitems.length > 0 && (
            <TocList items={item.subitems} onSelect={onSelect} />
          )}
        </li>
      ))}
    </ul>
  );
}

export function ReaderPage() {
  const { id } = useParams();
  const bookId = Number(id);
  const navigate = useNavigate();

  const [book, setBook] = useState<BookDetail | null | undefined>(undefined);
  const [status, setStatus] = useState<Status>("loading");
  const [toc, setToc] = useState<NavItem[]>([]);
  const [tocOpen, setTocOpen] = useState(false);
  const [fontScale, setFontScale] = useState(DEFAULT_FONT_SCALE);
  const containerRef = useRef<HTMLDivElement>(null);
  const renditionRef = useRef<Rendition | null>(null);

  function exit() {
    navigate(`/books/${bookId}`);
  }

  function handleKey(event: KeyboardEvent) {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      renditionRef.current?.prev();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      renditionRef.current?.next();
    } else if (event.key === "Escape") {
      event.preventDefault();
      exit();
    }
  }

  // Fetches the book's metadata first, only to decide whether there's
  // anything to render (unknown id, or a PDF, which has no in-browser
  // reader). The heavier EPUB file itself is fetched by the effect below,
  // once this confirms it's worth fetching at all.
  useEffect(() => {
    let cancelled = false;
    setStatus("loading");

    fetchBookDetail(bookId).then((detail) => {
      if (cancelled) return;
      setBook(detail);
      if (detail === null) setStatus("not-found");
      else if (detail.format !== "epub") setStatus("not-epub");
    });

    return () => {
      cancelled = true;
    };
  }, [bookId]);

  // epub.js owns everything under containerRef once it starts: it injects
  // its own iframe and manages it directly, outside React's reconciliation.
  // React never touches that div's children (there are none in the JSX
  // below), so nothing here fights epub.js for control of the DOM.
  //
  // The `cancelled` flag guards the async gap between starting the fetch
  // and epub.js actually touching the DOM. That gap is exactly what Strict
  // Mode's mount-cleanup-mount cycle exploits: the first pass's effect
  // starts the fetch and is torn down before it resolves, so `cancelled`
  // is already true by the time it would call renderTo — it bails out
  // instead, leaving the second pass as the only one that ever renders.
  // `rendition`/`epubBook` live only in this closure (not in a ref shared
  // across effect runs), and cleanup destroys them synchronously, so by
  // the time the next pass's effect body runs, the container is guaranteed
  // empty.
  useEffect(() => {
    if (!book || book.format !== "epub") return;

    const container = containerRef.current;
    if (!container) return;

    let cancelled = false;
    let epubBook: ReturnType<typeof ePub> | undefined;
    let rendition: Rendition | undefined;

    fetchBookFile(bookId)
      .then((buffer) => {
        if (cancelled) return;

        epubBook = ePub(buffer);
        epubBook.loaded.navigation.then((navigation) => {
          if (!cancelled) setToc(navigation.toc);
        });

        rendition = epubBook.renderTo(container, {
          width: "100%",
          height: "100%",
          flow: "paginated",
        });
        renditionRef.current = rendition;

        rendition.themes.register("light", READER_THEME);
        rendition.themes.select("light");
        rendition.themes.fontSize(`${DEFAULT_FONT_SCALE}%`);
        // epub.js loads each spine item into a fresh iframe document as you
        // turn pages. Its theme system re-injects the selected theme's
        // stylesheet into new content automatically, but re-selecting here
        // on every "rendered" event is a cheap belt-and-suspenders: it
        // guarantees the theme is (re)applied for every section, rather
        // than relying solely on that internal wiring.
        rendition.on("rendered", () => {
          rendition?.themes.select("light");
        });

        // Arrow keys and Escape while focus is inside the book's iframe:
        // epub.js's Contents forwards DOM keyboard events from inside each
        // section's document onto the rendition itself, which the outer
        // window never sees on its own.
        rendition.on("keyup", handleKey);

        return rendition.display();
      })
      .then(() => {
        if (!cancelled) setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
      renditionRef.current = null;
      rendition?.destroy();
      epubBook?.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [book, bookId]);

  // Same three keys, for when focus is on the outer page (the toolbar, or
  // right after load before anything inside the iframe has focus) rather
  // than inside the book's iframe.
  useEffect(() => {
    window.addEventListener("keyup", handleKey);
    return () => window.removeEventListener("keyup", handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  function goPrev() {
    renditionRef.current?.prev();
  }

  function goNext() {
    renditionRef.current?.next();
  }

  function goToTocItem(href: string) {
    renditionRef.current?.display(href);
    setTocOpen(false);
  }

  function changeFontScale(delta: number) {
    const next = Math.min(MAX_FONT_SCALE, Math.max(MIN_FONT_SCALE, fontScale + delta));
    setFontScale(next);
    renditionRef.current?.themes.fontSize(`${next}%`);
  }

  if (status === "not-found") {
    return (
      <div className={styles.message}>
        <p>Book not found.</p>
        <button type="button" onClick={() => navigate("/")}>
          Back to library
        </button>
      </div>
    );
  }

  if (status === "not-epub" && book) {
    return (
      <div className={styles.message}>
        <p>There's no in-browser reader for PDF files.</p>
        <a href={downloadUrl(book.id)}>Download {book.title}</a>
        <button type="button" onClick={exit}>
          Back to book
        </button>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={styles.message}>
        <p>Couldn't open this book.</p>
        <button type="button" onClick={exit}>
          Back to book
        </button>
      </div>
    );
  }

  return (
    <div className={styles.reader}>
      <header className={styles.bar}>
        <div className={styles.barLeft}>
          <button
            type="button"
            onClick={() => setTocOpen((open) => !open)}
            disabled={toc.length === 0}
            aria-label="Table of contents"
            aria-expanded={tocOpen}
          >
            Contents
          </button>
        </div>
        <span className={styles.title}>{book?.title}</span>
        <div className={styles.barRight}>
          <div className={styles.fontControl}>
            <button
              type="button"
              onClick={() => changeFontScale(-FONT_SCALE_STEP)}
              disabled={fontScale <= MIN_FONT_SCALE}
              aria-label="Decrease font size"
            >
              A−
            </button>
            <button
              type="button"
              onClick={() => changeFontScale(FONT_SCALE_STEP)}
              disabled={fontScale >= MAX_FONT_SCALE}
              aria-label="Increase font size"
            >
              A+
            </button>
          </div>
          <button type="button" onClick={exit} aria-label="Exit reader">
            Close
          </button>
        </div>
      </header>
      <div className={styles.viewport}>
        {tocOpen && (
          <nav className={styles.tocPanel} aria-label="Table of contents">
            <TocList items={toc} onSelect={goToTocItem} />
          </nav>
        )}
        <button type="button" className={styles.navButton} onClick={goPrev} aria-label="Previous page">
          &lsaquo;
        </button>
        <div ref={containerRef} className={styles.viewer} />
        <button type="button" className={styles.navButton} onClick={goNext} aria-label="Next page">
          &rsaquo;
        </button>
      </div>
    </div>
  );
}
