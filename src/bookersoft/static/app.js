const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadErrors = document.getElementById("upload-errors");
const bookTable = document.getElementById("book-table");
const bookList = document.getElementById("book-list");
const emptyState = document.getElementById("empty-state");
const noMatchState = document.getElementById("no-match-state");
const attentionFilter = document.getElementById("attention-filter");

const uploadSection = document.getElementById("upload-section");
const librarySection = document.getElementById("library-section");
const detailSection = document.getElementById("detail-section");
const detailNotFound = document.getElementById("detail-not-found");
const detailContent = document.getElementById("detail-content");

const EDITABLE_FIELDS = [
  { key: "title", label: "Title" },
  { key: "author", label: "Author" },
  { key: "language", label: "Language" },
  { key: "publication_year", label: "Year", type: "number" },
  { key: "publisher", label: "Publisher" },
  { key: "isbn", label: "ISBN" },
];

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = -1;
  do {
    value /= 1024;
    unitIndex += 1;
  } while (value >= 1024 && unitIndex < units.length - 1);
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleString();
}

function coverElement(book) {
  if (book.has_cover) {
    const img = document.createElement("img");
    img.src = `/books/${book.id}/cover`;
    img.alt = "";
    img.className = "cover-thumb";
    return img;
  }
  const placeholder = document.createElement("div");
  placeholder.className = "cover-placeholder";
  placeholder.textContent = "\u{1F4D6}";
  return placeholder;
}

function renderBooks(books) {
  bookList.innerHTML = "";

  if (books.length === 0) {
    const filtered = attentionFilter.checked;
    emptyState.hidden = filtered;
    noMatchState.hidden = !filtered;
    bookTable.hidden = true;
    return;
  }

  emptyState.hidden = true;
  noMatchState.hidden = true;
  bookTable.hidden = false;

  for (const book of books) {
    const row = document.createElement("tr");

    const coverCell = document.createElement("td");
    coverCell.appendChild(coverElement(book));
    row.appendChild(coverCell);

    const titleCell = document.createElement("td");
    const titleLink = document.createElement("a");
    titleLink.href = `/books/${book.id}`;
    titleLink.textContent = book.title;
    titleCell.appendChild(titleLink);
    if (book.needs_attention) {
      const badge = document.createElement("span");
      badge.className = "attention-badge";
      badge.textContent = "Needs attention";
      titleCell.appendChild(badge);
    }
    row.appendChild(titleCell);

    const formatCell = document.createElement("td");
    formatCell.textContent = book.format.toUpperCase();
    row.appendChild(formatCell);

    const sizeCell = document.createElement("td");
    sizeCell.textContent = formatSize(book.size_bytes);
    row.appendChild(sizeCell);

    const dateCell = document.createElement("td");
    dateCell.textContent = formatDate(book.uploaded_at);
    row.appendChild(dateCell);

    const downloadCell = document.createElement("td");
    const downloadLink = document.createElement("a");
    downloadLink.href = `/books/${book.id}/file`;
    downloadLink.textContent = "Download";
    downloadCell.appendChild(downloadLink);
    row.appendChild(downloadCell);

    const deleteCell = document.createElement("td");
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteBook(book));
    deleteCell.appendChild(deleteButton);
    row.appendChild(deleteCell);

    bookList.appendChild(row);
  }
}

async function loadBooks() {
  const query = attentionFilter.checked ? "?needs_attention=true" : "";
  const response = await fetch(`/books${query}`);
  const books = await response.json();
  renderBooks(books);
}

async function deleteBook(book) {
  const confirmed = confirm(`Delete "${book.title}"? This cannot be undone.`);
  if (!confirmed) return;

  await fetch(`/books/${book.id}`, { method: "DELETE" });
  await loadBooks();
}

function renderUploadErrors(rejected) {
  uploadErrors.innerHTML = "";

  if (rejected.length === 0) {
    uploadErrors.hidden = true;
    return;
  }

  uploadErrors.hidden = false;
  for (const item of rejected) {
    const li = document.createElement("li");
    li.textContent = `${item.filename}: ${item.reason}`;
    uploadErrors.appendChild(li);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (fileInput.files.length === 0) return;

  const formData = new FormData();
  for (const file of fileInput.files) {
    formData.append("files", file);
  }

  const response = await fetch("/books", { method: "POST", body: formData });
  const result = await response.json();

  renderUploadErrors(result.rejected);
  form.reset();
  await loadBooks();
});

attentionFilter.addEventListener("change", loadBooks);

// --- Book detail page ---

function fieldValueDisplay(value) {
  return value === null || value === undefined || value === "" ? "—" : value;
}

function currentDetailBookId() {
  const match = window.location.pathname.match(/^\/books\/(\d+)$/);
  return match ? Number(match[1]) : null;
}

function fieldValueRow(book, field) {
  const dd = document.createElement("dd");

  const valueSpan = document.createElement("span");
  valueSpan.textContent = fieldValueDisplay(book[field.key]);
  dd.appendChild(valueSpan);

  const sourceSpan = document.createElement("span");
  sourceSpan.className = "field-source";
  sourceSpan.textContent =
    book[`${field.key}_source`] === "manual" ? "(manually set)" : "(extracted)";
  dd.appendChild(sourceSpan);

  const editButton = document.createElement("button");
  editButton.type = "button";
  editButton.className = "field-edit-button";
  editButton.textContent = "Edit";
  editButton.addEventListener("click", () => startFieldEdit(book, field, dd));
  dd.appendChild(editButton);

  return dd;
}

function startFieldEdit(book, field, dd) {
  dd.innerHTML = "";

  const input = document.createElement("input");
  input.type = field.type === "number" ? "number" : "text";
  input.value = book[field.key] ?? "";
  dd.appendChild(input);

  const saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.textContent = "Save";
  saveButton.addEventListener("click", () => saveField(book.id, field, input.value));
  dd.appendChild(saveButton);

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = "Cancel";
  cancelButton.addEventListener("click", () => loadDetail(book.id));
  dd.appendChild(cancelButton);

  input.focus();
}

async function saveField(bookId, field, rawValue) {
  let value = rawValue.trim() === "" ? null : rawValue;
  if (field.type === "number" && value !== null) {
    value = Number(value);
  }

  await fetch(`/books/${bookId}/metadata`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ [field.key]: value }),
  });
  await loadDetail(bookId);
}

function renderDetail(book) {
  detailNotFound.hidden = true;
  detailContent.hidden = false;

  const coverContainer = document.getElementById("detail-cover");
  coverContainer.innerHTML = "";
  coverContainer.appendChild(coverElement(book));

  document.getElementById("detail-title").textContent = book.title;
  document.getElementById("detail-author").textContent = book.author || "Unknown author";

  const attention = document.getElementById("detail-attention");
  if (book.needs_attention) {
    attention.hidden = false;
    attention.textContent = book.extraction_failed
      ? "Metadata extraction failed for this file. Edit the fields below manually, or try re-extracting."
      : "Title or author is missing. Fill them in below.";
  } else {
    attention.hidden = true;
  }

  document.getElementById("detail-download").href = `/books/${book.id}/file`;

  const fieldsList = document.getElementById("detail-fields");
  fieldsList.innerHTML = "";
  for (const field of EDITABLE_FIELDS) {
    const dt = document.createElement("dt");
    dt.textContent = field.label;
    fieldsList.appendChild(dt);
    fieldsList.appendChild(fieldValueRow(book, field));
  }
}

async function loadDetail(bookId) {
  const response = await fetch(`/books/${bookId}/metadata`);

  if (response.status === 404) {
    detailNotFound.hidden = false;
    detailContent.hidden = true;
    return;
  }

  const book = await response.json();
  renderDetail(book);
}

document.getElementById("detail-reextract").addEventListener("click", async () => {
  const bookId = currentDetailBookId();
  await fetch(`/books/${bookId}/re-extract`, { method: "POST" });
  await loadDetail(bookId);
});

document.getElementById("detail-delete").addEventListener("click", async () => {
  const bookId = currentDetailBookId();
  const title = document.getElementById("detail-title").textContent;
  const confirmed = confirm(`Delete "${title}"? This cannot be undone.`);
  if (!confirmed) return;

  await fetch(`/books/${bookId}`, { method: "DELETE" });
  window.location.href = "/";
});

// --- Routing ---

function route() {
  const bookId = currentDetailBookId();

  if (bookId !== null) {
    uploadSection.hidden = true;
    librarySection.hidden = true;
    detailSection.hidden = false;
    loadDetail(bookId);
    return;
  }

  uploadSection.hidden = false;
  librarySection.hidden = false;
  detailSection.hidden = true;
  loadBooks();
}

route();
