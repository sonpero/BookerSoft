import { useEffect, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";

import { addTagToBook, fetchTags, removeTagFromBook, type TagOut } from "../api";
import { CloseIcon } from "./icons";
import tagStyles from "./Tag.module.css";
import styles from "./TagEditor.module.css";

interface TagEditorProps {
  bookId: number;
  tags: TagOut[];
  onChange: (tags: TagOut[]) => void;
}

export function TagEditor({ bookId, tags, onChange }: TagEditorProps) {
  const [allTags, setAllTags] = useState<TagOut[]>([]);
  const [input, setInput] = useState("");
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);

  useEffect(() => {
    fetchTags().then(setAllTags);
  }, []);

  async function addTag(name: string) {
    if (!name.trim()) return;
    const updated = await addTagToBook(bookId, name);
    onChange(updated);
    setInput("");
    setSuggestionsOpen(false);
  }

  async function removeTag(tag: TagOut) {
    onChange(tags.filter((t) => t.id !== tag.id));
    await removeTagFromBook(bookId, tag.id);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      addTag(input);
    } else if (event.key === "Escape") {
      setSuggestionsOpen(false);
    }
  }

  const currentNames = new Set(tags.map((tag) => tag.name));
  const query = input.trim().toLowerCase();
  const suggestions = query
    ? allTags.filter((tag) => !currentNames.has(tag.name) && tag.name.includes(query)).slice(0, 8)
    : [];

  return (
    <div className={styles.editor}>
      <h2 className={styles.heading}>Tags</h2>

      {tags.length > 0 && (
        <ul className={`${tagStyles.list} ${styles.tagList}`}>
          {tags.map((tag) => (
            <li key={tag.id} className={tagStyles.tag}>
              <Link to={`/?tags=${tag.id}`} className={styles.tagLabel}>
                {tag.name}
              </Link>
              <button
                type="button"
                className={tagStyles.removeButton}
                onClick={() => removeTag(tag)}
                aria-label={`Remove tag ${tag.name}`}
              >
                <CloseIcon />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className={styles.inputRow}>
        <input
          type="text"
          value={input}
          placeholder="Add a tag"
          onChange={(event) => {
            setInput(event.target.value);
            setSuggestionsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setSuggestionsOpen(true)}
          onBlur={() => setSuggestionsOpen(false)}
        />
        {suggestionsOpen && suggestions.length > 0 && (
          <ul className={styles.suggestions}>
            {suggestions.map((tag) => (
              <li key={tag.id}>
                <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => addTag(tag.name)}>
                  {tag.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
