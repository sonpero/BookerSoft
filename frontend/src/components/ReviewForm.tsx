import { useEffect, useState, type FormEvent } from "react";

import type { ReviewOut } from "../api";
import { StarRating } from "./StarRating";
import styles from "./ReviewForm.module.css";

interface ReviewFormProps {
  myReview: ReviewOut | null;
  onSave: (rating: number, reviewText: string | null) => Promise<void>;
  onDelete: () => Promise<void>;
}

export function ReviewForm({ myReview, onSave, onDelete }: ReviewFormProps) {
  const [rating, setRating] = useState(myReview?.rating ?? 0);
  const [text, setText] = useState(myReview?.review_text ?? "");

  useEffect(() => {
    setRating(myReview?.rating ?? 0);
    setText(myReview?.review_text ?? "");
  }, [myReview]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!rating) return;
    await onSave(rating, text.trim() === "" ? null : text);
  }

  async function handleDelete() {
    const confirmed = confirm("Delete your rating and review? This cannot be undone.");
    if (!confirmed) return;
    await onDelete();
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <label>
        Your rating
        <StarRating value={rating} onChange={setRating} />
      </label>

      <label>
        Your review (optional)
        <textarea rows={3} value={text} onChange={(event) => setText(event.target.value)} />
      </label>

      <div className={styles.actions}>
        <button type="submit" disabled={!rating}>
          Save rating &amp; review
        </button>
        {myReview && (
          <button type="button" className={styles.deleteButton} onClick={handleDelete}>
            Delete my review
          </button>
        )}
      </div>
    </form>
  );
}
