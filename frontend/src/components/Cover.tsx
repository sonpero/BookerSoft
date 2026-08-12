import { coverUrl, type BookSummary } from "../api";
import styles from "./Cover.module.css";

interface CoverProps {
  book: Pick<BookSummary, "id" | "title" | "has_cover">;
  size?: "grid" | "detail";
}

export function Cover({ book, size = "grid" }: CoverProps) {
  const sizeClass = size === "detail" ? styles.detail : styles.grid;

  if (book.has_cover) {
    return <img src={coverUrl(book.id)} alt="" className={`${styles.cover} ${sizeClass}`} />;
  }

  return (
    <div className={`${styles.cover} ${styles.placeholder} ${sizeClass}`}>
      <span>{book.title}</span>
    </div>
  );
}
