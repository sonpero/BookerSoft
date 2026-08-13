import { useState } from "react";

import { uploadBooks, type UploadResponse } from "../api";
import { UploadForm } from "../components/UploadForm";
import styles from "./UploadPage.module.css";

export function UploadPage() {
  const [result, setResult] = useState<UploadResponse | null>(null);

  async function handleUpload(files: File[]) {
    setResult(await uploadBooks(files));
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Upload</h1>
      <UploadForm onUpload={handleUpload} result={result} />
    </div>
  );
}
