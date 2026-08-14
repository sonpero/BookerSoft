import { useEffect, useState, type KeyboardEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  coverUrl,
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
  type TagOut,
} from "../api";
import { Cover } from "../components/Cover";
import { CoverOverlay } from "../components/CoverOverlay";
import { MetadataField } from "../components/MetadataField";
import { ReviewForm } from "../components/ReviewForm";
import { ReviewsList } from "../components/ReviewsList";
import { TagEditor } from "../components/TagEditor";
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
  const [coverOverlayOpen, setCoverOverlayOpen] = useState(false);
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

  function openCoverOverlay() {
    if (book?.has_cover) setCoverOverlayOpen(true);
  }

  function handleCoverKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openCoverOverlay();
    }
  }

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

  function handleTagsChange(tags: TagOut[]) {
    setBook((current) => (current ? { ...current, tags } : current));
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
        <div
          className={`${styles.coverWrapper} ${book.has_cover ? styles.coverClickable : ""}`}
          onClick={openCoverOverlay}
          onKeyDown={book.has_cover ? handleCoverKeyDown : undefined}
          role={book.has_cover ? "button" : undefined}
          tabIndex={book.has_cover ? 0 : undefined}
          aria-label={book.has_cover ? `View cover of ${book.title} full size` : undefined}
        >
          <Cover book={book} size="detail" />
        </div>
        {coverOverlayOpen && book.has_cover && (
          <CoverOverlay src={coverUrl(book.id)} alt={book.title ?? ""} onClose={() => setCoverOverlayOpen(false)} />
        )}

        <div className={styles.info}>
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
              {book.format === "epub" && (
                <Link to={`/books/${book.id}/read`} className={styles.downloadLink}>
                  Read
                </Link>
              )}
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

          <TagEditor bookId={book.id} tags={book.tags} onChange={handleTagsChange} />
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
