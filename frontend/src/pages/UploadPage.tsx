import { useState } from "react";

import { uploadBooks, type RejectedFile } from "../api";
import { UploadForm } from "../components/UploadForm";
import styles from "./UploadPage.module.css";

export function UploadPage() {
  const [errors, setErrors] = useState<RejectedFile[]>([]);

  async function handleUpload(files: File[]) {
    const result = await uploadBooks(files);
    setErrors(result.rejected);
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Upload</h1>
      <UploadForm onUpload={handleUpload} errors={errors} />
    </div>
  );
}
