const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadErrors = document.getElementById("upload-errors");
const bookTable = document.getElementById("book-table");
const bookList = document.getElementById("book-list");
const emptyState = document.getElementById("empty-state");

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

function renderBooks(books) {
  bookList.innerHTML = "";

  if (books.length === 0) {
    emptyState.hidden = false;
    bookTable.hidden = true;
    return;
  }

  emptyState.hidden = true;
  bookTable.hidden = false;

  for (const book of books) {
    const row = document.createElement("tr");

    const titleCell = document.createElement("td");
    titleCell.textContent = book.original_filename;
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
  const response = await fetch("/books");
  const books = await response.json();
  renderBooks(books);
}

async function deleteBook(book) {
  const confirmed = confirm(`Delete "${book.original_filename}"? This cannot be undone.`);
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

loadBooks();
