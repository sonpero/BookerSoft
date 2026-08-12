import type { ReviewOut } from "../api";
import styles from "./ReviewsList.module.css";

interface ReviewsListProps {
  reviews: ReviewOut[];
}

export function ReviewsList({ reviews }: ReviewsListProps) {
  if (reviews.length === 0) {
    return <p className={styles.empty}>No reviews yet.</p>;
  }

  return (
    <ul className={styles.list}>
      {reviews.map((review) => (
        <li key={review.id} className={styles.item}>
          <strong>{review.username}</strong>
          <span className={styles.rating}>{review.rating}/5</span>
          <span className={styles.date}>{new Date(review.updated_at).toLocaleDateString()}</span>
          {review.review_text && <p className={styles.text}>{review.review_text}</p>}
        </li>
      ))}
    </ul>
  );
}
