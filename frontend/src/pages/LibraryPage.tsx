import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  DEFAULT_FILTERS,
  deleteBook,
  fetchBooks,
  fetchUsers,
  filtersFromSearchParams,
  filtersToSearchParams,
  hasActiveFilters,
  type BookFilters,
  type BookSummary,
  type UserOut,
} from "../api";
import { BookCard } from "../components/BookCard";
import { FilterBar } from "../components/FilterBar";
import styles from "./LibraryPage.module.css";

export function LibraryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = filtersFromSearchParams(searchParams);

  const [books, setBooks] = useState<BookSummary[] | null>(null);
  const [users, setUsers] = useState<UserOut[]>([]);

  function loadBooks() {
    fetchBooks(filtersFromSearchParams(searchParams)).then(setBooks);
  }

  useEffect(() => {
    fetchUsers().then(setUsers);
  }, []);

  // searchParams (from React Router) is referentially stable until the URL
  // actually changes, so this only re-fetches when a filter really changed.
  useEffect(() => {
    loadBooks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  function updateFilters(patch: Partial<BookFilters>) {
    setSearchParams(filtersToSearchParams({ ...filters, ...patch }), { replace: true });
  }

  function clearFilters() {
    setSearchParams(filtersToSearchParams(DEFAULT_FILTERS), { replace: true });
  }

  async function handleDelete(book: BookSummary) {
    const confirmed = confirm(`Delete "${book.title}"? This cannot be undone.`);
    if (!confirmed) return;
    await deleteBook(book.id);
    loadBooks();
  }

  return (
    <div className={styles.page}>
      <FilterBar filters={filters} users={users} onChange={updateFilters} onClear={clearFilters} />

      {books === null ? null : books.length === 0 ? (
        <p className={styles.emptyState}>
          {hasActiveFilters(filters) ? "No book matches these filters." : "No books yet. Upload one to get started."}
        </p>
      ) : (
        <div className={styles.grid}>
          {books.map((book) => (
            <BookCard key={book.id} book={book} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
