import type { ChangeEvent } from "react";

import styles from "./MetadataField.module.css";

interface MetadataFieldProps {
  label: string;
  value: string | number | null;
  editing: boolean;
  draftValue: string;
  onDraftChange: (value: string) => void;
  type?: "text" | "number";
}

export function MetadataField({ label, value, editing, draftValue, onDraftChange, type = "text" }: MetadataFieldProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    onDraftChange(event.target.value);
  }

  return (
    <>
      <dt className={styles.label}>{label}</dt>
      <dd className={styles.value}>
        {editing ? (
          <input className={styles.input} type={type === "number" ? "number" : "text"} value={draftValue} onChange={handleChange} />
        ) : (
          <span>{value ?? "—"}</span>
        )}
      </dd>
    </>
  );
}
