import { useNavigate } from "react-router-dom";
import type { KeyboardEvent, MouseEvent } from "react";

import { downloadUrl, type BookSummary } from "../api";
import { Cover } from "./Cover";
import { DownloadIcon, TrashIcon } from "./icons";
import styles from "./BookCard.module.css";

interface BookCardProps {
  book: BookSummary;
  onDelete: (book: BookSummary) => void;
}

function formatRatingSummary(book: BookSummary): string {
  if (book.average_rating === null) return "Not rated yet";
  const rounded = Math.round(book.average_rating * 10) / 10;
  return `${rounded} / 5`;
}

export function BookCard({ book, onDelete }: BookCardProps) {
  const navigate = useNavigate();
  const detailUrl = `/books/${book.id}`;

  function handleCardClick() {
    navigate(detailUrl);
  }

  function handleCardKeyDown(event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      navigate(detailUrl);
    }
  }

  function handleDownloadClick(event: MouseEvent) {
    // Let the browser follow the download link normally, just don't also
    // trigger the card's own navigation to the detail page underneath it.
    event.stopPropagation();
  }

  function handleDeleteClick(event: MouseEvent) {
    event.stopPropagation();
    onDelete(book);
  }

  return (
    // A plain div, not <Link>: the download control below is a real <a>,
    // and an <a> can't validly contain another <a> (the browser silently
    // reparents the DOM when it does, which breaks click handling on the
    // controls inside).
    <div className={styles.card} role="link" tabIndex={0} onClick={handleCardClick} onKeyDown={handleCardKeyDown}>
      <div className={styles.coverWrapper}>
        <Cover book={book} />
        <div className={styles.overlay}>
          <a
            href={downloadUrl(book.id)}
            className={styles.iconButton}
            aria-label={`Download ${book.title}`}
            onClick={handleDownloadClick}
          >
            <DownloadIcon />
          </a>
          <button
            type="button"
            className={`${styles.iconButton} ${styles.deleteIconButton}`}
            aria-label={`Delete ${book.title}`}
            onClick={handleDeleteClick}
          >
            <TrashIcon />
          </button>
        </div>
      </div>
      <div className={styles.title}>{book.title}</div>
      {book.author && <div className={styles.author}>{book.author}</div>}
      <div className={styles.rating}>{formatRatingSummary(book)}</div>
    </div>
  );
}
