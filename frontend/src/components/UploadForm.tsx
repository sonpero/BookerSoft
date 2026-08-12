import { useRef, useState, type FormEvent } from "react";

import type { RejectedFile } from "../api";
import styles from "./UploadForm.module.css";

interface UploadFormProps {
  onUpload: (files: File[]) => Promise<void>;
  errors: RejectedFile[];
}

export function UploadForm({ onUpload, errors }: UploadFormProps) {
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

  return (
    <div>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input ref={fileInputRef} type="file" multiple accept=".epub,.pdf" />
        <button type="submit" disabled={pending}>
          Upload
        </button>
      </form>
      {errors.length > 0 && (
        <ul className={styles.errors}>
          {errors.map((error) => (
            <li key={error.filename}>
              {error.filename}: {error.reason}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
