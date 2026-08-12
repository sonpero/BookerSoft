import { StarIcon } from "./icons";
import styles from "./StarRating.module.css";

interface StarRatingProps {
  value: number;
  onChange: (value: number) => void;
}

export function StarRating({ value, onChange }: StarRatingProps) {
  return (
    <div className={styles.stars} role="radiogroup" aria-label="Your rating">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={`${n} star${n > 1 ? "s" : ""}`}
          className={`${styles.star} ${n <= value ? styles.filled : ""}`}
          onClick={() => onChange(n)}
        >
          <StarIcon filled={n <= value} />
        </button>
      ))}
    </div>
  );
}
