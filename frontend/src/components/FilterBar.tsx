import { useEffect, useRef, useState } from "react";

import { hasActiveFilters, type BookFilters, type BookFormat, type SortOption, type TagOut, type UserOut } from "../api";
import styles from "./FilterBar.module.css";
import tagStyles from "./Tag.module.css";

interface FilterBarProps {
  filters: BookFilters;
  users: UserOut[];
  tags: TagOut[];
  onChange: (patch: Partial<BookFilters>) => void;
  onClear: () => void;
}

const SEARCH_DEBOUNCE_MS = 250;

export function FilterBar({ filters, users, tags, onChange, onClear }: FilterBarProps) {
  const [searchText, setSearchText] = useState(filters.q);
  const debounceRef = useRef<number | undefined>(undefined);

  // Stay in sync when filters change from outside typing (Clear filters,
  // or navigating straight to a bookmarked URL).
  useEffect(() => {
    setSearchText(filters.q);
  }, [filters.q]);

  function handleSearchInput(value: string) {
    setSearchText(value);
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => onChange({ q: value }), SEARCH_DEBOUNCE_MS);
  }

  function toggleTag(tagId: number) {
    const nextTags = filters.tags.includes(tagId)
      ? filters.tags.filter((id) => id !== tagId)
      : [...filters.tags, tagId];
    onChange({ tags: nextTags });
  }

  return (
    <div className={styles.bar}>
      <input
        type="search"
        className={styles.search}
        placeholder="Search by title or author"
        aria-label="Search"
        value={searchText}
        onChange={(event) => handleSearchInput(event.target.value)}
      />

      <div className={styles.filterRow}>
        <div className={styles.filterGroup}>
          <label className={styles.field}>
            Format
            <select
              value={filters.format}
              onChange={(event) => onChange({ format: event.target.value as BookFormat | "" })}
            >
              <option value="">All</option>
              <option value="epub">EPUB</option>
              <option value="pdf">PDF</option>
            </select>
          </label>

          <label className={styles.field}>
            Min. rating
            <select value={filters.min_rating} onChange={(event) => onChange({ min_rating: event.target.value })}>
              <option value="">Any</option>
              <option value="1">1+</option>
              <option value="2">2+</option>
              <option value="3">3+</option>
              <option value="4">4+</option>
              <option value="5">5</option>
            </select>
          </label>

          <label className={styles.field}>
            Uploaded by
            <select value={filters.uploaded_by} onChange={(event) => onChange({ uploaded_by: event.target.value })}>
              <option value="">Everyone</option>
              {users.map((user) => (
                <option key={user.id} value={String(user.id)}>
                  {user.username}
                </option>
              ))}
            </select>
          </label>

          <div className={styles.field}>
            Tags
            <details className={styles.tagsField}>
              <summary className={styles.tagsSummary}>
                {filters.tags.length > 0 ? `${filters.tags.length} selected` : "All"}
              </summary>
              <div className={styles.tagsPanel}>
                {tags.length === 0 ? (
                  <p className={styles.noTags}>No tags yet</p>
                ) : (
                  <div className={tagStyles.list}>
                    {tags.map((tag) => (
                      <button
                        key={tag.id}
                        type="button"
                        className={`${tagStyles.tag} ${filters.tags.includes(tag.id) ? tagStyles.selected : ""}`}
                        onClick={() => toggleTag(tag.id)}
                      >
                        {tag.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </details>
          </div>

          <label className={styles.field}>
            Sort by
            <select value={filters.sort} onChange={(event) => onChange({ sort: event.target.value as SortOption })}>
              <option value="recent">Recently added</option>
              <option value="title">Title</option>
              <option value="author">Author</option>
              <option value="rating">Average rating</option>
            </select>
          </label>

          {hasActiveFilters(filters) && (
            <button type="button" className={styles.clearButton} onClick={onClear}>
              Clear filters
            </button>
          )}
        </div>

        <label className={styles.checkboxField}>
          <input
            type="checkbox"
            checked={filters.needs_attention}
            onChange={(event) => onChange({ needs_attention: event.target.checked })}
          />
          Needs attention only
        </label>
      </div>
    </div>
  );
}
