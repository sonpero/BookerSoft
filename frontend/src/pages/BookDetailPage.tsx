import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteBook,
  deleteMyReview,
  downloadUrl,
  fetchBookDetail,
  fetchMyReview,
  fetchReviews,
  formatRatingSummary,
  reExtractBook,
  saveMyReview,
  updateBookMetadata,
  type BookDetail,
  type BookUpdate,
  type ReviewOut,
} from "../api";
import { Cover } from "../components/Cover";
import { MetadataField } from "../components/MetadataField";
import { ReviewForm } from "../components/ReviewForm";
import { ReviewsList } from "../components/ReviewsList";
import styles from "./BookDetailPage.module.css";

interface Drafts {
  title: string;
  author: string;
  language: string;
  publication_year: string;
  publisher: string;
  isbn: string;
  description: string;
}

// Used only until the ResizeObserver below reports the real height of the
// content column, so the cover doesn't flash at 0 height on first render.
const DEFAULT_COVER_HEIGHT = 272;

function draftsFromBook(book: BookDetail): Drafts {
  return {
    title: book.title ?? "",
    author: book.author ?? "",
    language: book.language ?? "",
    publication_year: book.publication_year !== null ? String(book.publication_year) : "",
    publisher: book.publisher ?? "",
    isbn: book.isbn ?? "",
    description: book.description ?? "",
  };
}

export function BookDetailPage() {
  const { id } = useParams();
  const bookId = Number(id);
  const navigate = useNavigate();

  const [book, setBook] = useState<BookDetail | null | undefined>(undefined);
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [myReview, setMyReview] = useState<ReviewOut | null>(null);

  const [editingMetadata, setEditingMetadata] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [drafts, setDrafts] = useState<Drafts>({
    title: "",
    author: "",
    language: "",
    publication_year: "",
    publisher: "",
    isbn: "",
    description: "",
  });
  const [saving, setSaving] = useState(false);

  // A state-backed callback ref, not useRef: while the book is still
  // loading this component returns null (see below), so the .info div
  // doesn't exist on the first mount — a plain useRef + effect with an
  // empty dependency array would run before it exists and never attach.
  // Using state for the node means the effect re-runs exactly when the
  // node actually appears.
  const [infoNode, setInfoNode] = useState<HTMLDivElement | null>(null);
  const [coverHeight, setCoverHeight] = useState(DEFAULT_COVER_HEIGHT);

  // The cover's height follows the content column's actual rendered height
  // (title, actions, metadata and description together), not the other way
  // around: the column's own width is never affected by the cover, which is
  // what keeps this from becoming a circular layout.
  useEffect(() => {
    if (!infoNode) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setCoverHeight(entry.contentRect.height);
    });
    observer.observe(infoNode);
    return () => observer.disconnect();
  }, [infoNode]);

  async function loadBook() {
    setBook(await fetchBookDetail(bookId));
  }

  async function loadReviews() {
    setReviews(await fetchReviews(bookId));
  }

  async function loadMyReview() {
    setMyReview(await fetchMyReview(bookId));
  }

  useEffect(() => {
    loadBook();
    loadReviews();
    loadMyReview();
    setDescriptionExpanded(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  function startEditingMetadata() {
    if (!book) return;
    setDrafts(draftsFromBook(book));
    setEditingMetadata(true);
  }

  function cancelEditingMetadata() {
    setEditingMetadata(false);
  }

  async function saveEditingMetadata() {
    if (!book) return;

    const update: BookUpdate = {};

    const title = drafts.title.trim() || null;
    if (title !== (book.title ?? null)) update.title = title;

    const author = drafts.author.trim() || null;
    if (author !== (book.author ?? null)) update.author = author;

    const language = drafts.language.trim() || null;
    if (language !== (book.language ?? null)) update.language = language;

    const yearRaw = drafts.publication_year.trim();
    const publicationYear = yearRaw === "" ? null : Number(yearRaw);
    if (publicationYear !== (book.publication_year ?? null)) update.publication_year = publicationYear;

    const publisher = drafts.publisher.trim() || null;
    if (publisher !== (book.publisher ?? null)) update.publisher = publisher;

    const isbn = drafts.isbn.trim() || null;
    if (isbn !== (book.isbn ?? null)) update.isbn = isbn;

    const description = drafts.description.trim() || null;
    if (description !== (book.description ?? null)) update.description = description;

    setSaving(true);
    if (Object.keys(update).length > 0) {
      setBook(await updateBookMetadata(bookId, update));
    }
    setSaving(false);
    setEditingMetadata(false);
  }

  async function handleReExtract() {
    setBook(await reExtractBook(bookId));
  }

  async function handleDelete() {
    if (!book) return;
    const confirmed = confirm(`Delete "${book.title}"? This cannot be undone.`);
    if (!confirmed) return;

    const response = await deleteBook(bookId);
    if (response.ok) {
      navigate("/");
    } else {
      alert("You don't have permission to delete this book.");
    }
  }

  async function handleReviewSave(rating: number, reviewText: string | null) {
    await saveMyReview(bookId, { rating, review_text: reviewText });
    await Promise.all([loadMyReview(), loadReviews(), loadBook()]);
  }

  async function handleReviewDelete() {
    await deleteMyReview(bookId);
    await Promise.all([loadMyReview(), loadReviews(), loadBook()]);
  }

  if (book === undefined) return null;

  if (book === null) {
    return (
      <div className={styles.page}>
        <Link to="/" className={styles.back}>
          &larr; Library
        </Link>
        <p>Book not found.</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link to="/" className={styles.back}>
        &larr; Library
      </Link>

      <div className={styles.layout}>
        <div className={styles.coverWrapper} style={{ height: `${coverHeight}px` }}>
          <Cover book={book} size="detail" />
        </div>

        <div className={styles.info} ref={setInfoNode}>
          <h1 className={styles.title}>{book.title}</h1>
          <p className={styles.author}>{book.author || "Unknown author"}</p>
          <p className={styles.ratingSummary}>{formatRatingSummary(book)}</p>

          {book.needs_attention && (
            <p className={styles.attentionBanner}>
              {book.extraction_failed
                ? "Metadata extraction failed for this file. Edit the fields below manually, or try re-extracting."
                : "Title or author is missing. Fill them in below."}
            </p>
          )}

          <div className={styles.actions}>
            <div className={styles.actionsLeft}>
              {editingMetadata ? (
                <>
                  <button type="button" className={styles.primaryButton} onClick={saveEditingMetadata} disabled={saving}>
                    Save
                  </button>
                  <button type="button" onClick={cancelEditingMetadata} disabled={saving}>
                    Cancel
                  </button>
                </>
              ) : (
                <button type="button" className={styles.primaryButton} onClick={startEditingMetadata}>
                  Edit metadata
                </button>
              )}
              <button type="button" onClick={handleReExtract}>
                Re-extract metadata
              </button>
            </div>
            <div className={styles.actionsRight}>
              <a href={downloadUrl(book.id)} className={styles.downloadLink}>
                Download
              </a>
              <button type="button" className={styles.deleteButton} onClick={handleDelete}>
                Delete
              </button>
            </div>
          </div>

          <div className={styles.metaRow}>
            <dl className={styles.fields}>
              <MetadataField
                label="Title"
                value={book.title}
                editing={editingMetadata}
                draftValue={drafts.title}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, title: value }))}
              />
              <MetadataField
                label="Author"
                value={book.author}
                editing={editingMetadata}
                draftValue={drafts.author}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, author: value }))}
              />
              <MetadataField
                label="Language"
                value={book.language}
                editing={editingMetadata}
                draftValue={drafts.language}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, language: value }))}
              />
              <MetadataField
                label="Year"
                value={book.publication_year}
                type="number"
                editing={editingMetadata}
                draftValue={drafts.publication_year}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, publication_year: value }))}
              />
              <MetadataField
                label="Publisher"
                value={book.publisher}
                editing={editingMetadata}
                draftValue={drafts.publisher}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, publisher: value }))}
              />
              <MetadataField
                label="ISBN"
                value={book.isbn}
                editing={editingMetadata}
                draftValue={drafts.isbn}
                onDraftChange={(value) => setDrafts((d) => ({ ...d, isbn: value }))}
              />
            </dl>

            <div className={styles.description}>
              {editingMetadata ? (
                <textarea
                  className={styles.descriptionTextarea}
                  rows={10}
                  value={drafts.description}
                  onChange={(event) => setDrafts((d) => ({ ...d, description: event.target.value }))}
                />
              ) : (
                <>
                  <p className={descriptionExpanded ? styles.descriptionText : styles.descriptionTextClamped}>
                    {book.description ?? "—"}
                  </p>
                  {book.description && (
                    <button
                      type="button"
                      className={styles.readMoreButton}
                      onClick={() => setDescriptionExpanded((expanded) => !expanded)}
                    >
                      {descriptionExpanded ? "Read less" : "Read more"}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <section className={styles.reviewsSection}>
        <h2 className={styles.reviewsHeading}>Ratings &amp; reviews</h2>
        <ReviewForm myReview={myReview} onSave={handleReviewSave} onDelete={handleReviewDelete} />
        <ReviewsList reviews={reviews} />
      </section>
    </div>
  );
}
