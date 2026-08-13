import { useRef, useState, type FormEvent } from "react";

import type { UploadResponse } from "../api";
import styles from "./UploadForm.module.css";

interface UploadFormProps {
  onUpload: (files: File[]) => Promise<void>;
  result: UploadResponse | null;
}

export function UploadForm({ onUpload, result }: UploadFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const files = fileInputRef.current?.files;
    if (!files || files.length === 0) return;

    setPending(true);
    await onUpload(Array.from(files));
    setPending(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const addedCount = result?.uploaded.filter((book) => !book.duplicate).length ?? 0;
  const problems = result
    ? [
        ...result.uploaded
          .filter((book) => book.duplicate)
          .map((book) => ({ filename: book.original_filename, reason: "duplicate of an existing book" })),
        ...result.rejected,
      ]
    : [];

  return (
    <div>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input ref={fileInputRef} type="file" multiple accept=".epub,.pdf" />
        <button type="submit" disabled={pending}>
          Upload
        </button>
      </form>
      {result && (
        <p className={styles.summary}>
          {addedCount === 1 ? "1 book added." : `${addedCount} books added.`}
        </p>
      )}
      {problems.length > 0 && (
        <ul className={styles.errors}>
          {problems.map((problem, index) => (
            <li key={`${problem.filename}-${index}`}>
              {problem.filename}: {problem.reason}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
