import { useEffect } from "react";

import { CloseIcon } from "./icons";
import styles from "./CoverOverlay.module.css";

interface CoverOverlayProps {
  src: string;
  alt: string;
  onClose: () => void;
}

export function CoverOverlay({ src, alt, onClose }: CoverOverlayProps) {
  // Body scroll is locked, not just the overlay's own — the overlay sits on
  // top of the whole page, but without this the page underneath still
  // scrolls with it (a touchmove drag "leaks" through to the body).
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className={styles.scrim} onClick={onClose}>
      <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close">
        <CloseIcon />
      </button>
      <img src={src} alt={alt} className={styles.image} onClick={(event) => event.stopPropagation()} />
    </div>
  );
}
