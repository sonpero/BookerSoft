export type BookFormat = "epub" | "pdf";
export type MetadataSource = "auto" | "manual";
export type SortOption = "recent" | "title" | "author" | "rating";

export interface BookSummary {
  id: number;
  original_filename: string;
  title: string;
  author: string | null;
  format: BookFormat;
  size_bytes: number;
  uploaded_at: string;
  has_cover: boolean;
  needs_attention: boolean;
  average_rating: number | null;
  rating_count: number;
}

export interface UploadedBook extends BookSummary {
  duplicate: boolean;
}

export interface RejectedFile {
  filename: string;
  reason: string;
}

export interface UploadResponse {
  uploaded: UploadedBook[];
  rejected: RejectedFile[];
}

export interface BookDetail {
  id: number;
  original_filename: string;
  format: BookFormat;
  size_bytes: number;
  uploaded_at: string;
  title: string;
  title_source: MetadataSource;
  author: string | null;
  author_source: MetadataSource;
  language: string | null;
  language_source: MetadataSource;
  publication_year: number | null;
  publication_year_source: MetadataSource;
  publisher: string | null;
  publisher_source: MetadataSource;
  isbn: string | null;
  isbn_source: MetadataSource;
  description: string | null;
  description_source: MetadataSource;
  has_cover: boolean;
  needs_attention: boolean;
  extraction_failed: boolean;
  average_rating: number | null;
  rating_count: number;
}

export interface BookUpdate {
  title?: string | null;
  author?: string | null;
  language?: string | null;
  publication_year?: number | null;
  publisher?: string | null;
  isbn?: string | null;
  description?: string | null;
}

export interface ReviewOut {
  id: number;
  book_id: number;
  user_id: number;
  username: string;
  rating: number;
  review_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewIn {
  rating: number;
  review_text?: string | null;
}

export interface UserOut {
  id: number;
  username: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  is_owner: boolean;
}

// Wraps fetch() to redirect to /login on 401: the server already redirects
// unauthenticated page loads itself (see Layout's session check), so this
// only ever fires for a session that expires while the app is open.
async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, init);
  if (response.status === 401) {
    window.location.href = "/login";
  }
  return response;
}

export interface BookFilters {
  q: string;
  format: BookFormat | "";
  min_rating: string;
  uploaded_by: string;
  sort: SortOption;
  needs_attention: boolean;
}

export const DEFAULT_FILTERS: BookFilters = {
  q: "",
  format: "",
  min_rating: "",
  uploaded_by: "",
  sort: "recent",
  needs_attention: false,
};

export function filtersToSearchParams(filters: BookFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.format) params.set("format", filters.format);
  if (filters.min_rating) params.set("min_rating", filters.min_rating);
  if (filters.uploaded_by) params.set("uploaded_by", filters.uploaded_by);
  if (filters.sort !== "recent") params.set("sort", filters.sort);
  if (filters.needs_attention) params.set("needs_attention", "true");
  return params;
}

export function filtersFromSearchParams(params: URLSearchParams): BookFilters {
  return {
    q: params.get("q") ?? "",
    format: (params.get("format") as BookFormat | null) ?? "",
    min_rating: params.get("min_rating") ?? "",
    uploaded_by: params.get("uploaded_by") ?? "",
    sort: (params.get("sort") as SortOption | null) ?? "recent",
    needs_attention: params.get("needs_attention") === "true",
  };
}

export function hasActiveFilters(filters: BookFilters): boolean {
  return Boolean(
    filters.q ||
      filters.format ||
      filters.min_rating ||
      filters.uploaded_by ||
      filters.needs_attention ||
      filters.sort !== "recent",
  );
}

export async function fetchBooks(filters: BookFilters): Promise<BookSummary[]> {
  const query = filtersToSearchParams(filters).toString();
  const response = await apiFetch(`/books${query ? `?${query}` : ""}`);
  return response.json();
}

export async function fetchUsers(): Promise<UserOut[]> {
  const response = await apiFetch("/users");
  return response.json();
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  const response = await apiFetch("/me");
  if (!response.ok) return null;
  return response.json();
}

export async function logout(): Promise<void> {
  await fetch("/logout", { method: "POST" });
}

export async function uploadBooks(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  for (const file of files) formData.append("files", file);
  const response = await apiFetch("/books", { method: "POST", body: formData });
  return response.json();
}

export async function deleteBook(id: number): Promise<Response> {
  return apiFetch(`/books/${id}`, { method: "DELETE" });
}

export async function fetchBookDetail(id: number): Promise<BookDetail | null> {
  const response = await apiFetch(`/books/${id}/metadata`);
  if (response.status === 404) return null;
  return response.json();
}

export async function updateBookMetadata(id: number, update: BookUpdate): Promise<BookDetail> {
  const response = await apiFetch(`/books/${id}/metadata`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  return response.json();
}

export async function reExtractBook(id: number): Promise<BookDetail> {
  const response = await apiFetch(`/books/${id}/re-extract`, { method: "POST" });
  return response.json();
}

export async function fetchReviews(bookId: number): Promise<ReviewOut[]> {
  const response = await apiFetch(`/books/${bookId}/reviews`);
  return response.json();
}

export async function fetchMyReview(bookId: number): Promise<ReviewOut | null> {
  const response = await apiFetch(`/books/${bookId}/review`);
  if (response.status === 404) return null;
  return response.json();
}

export async function saveMyReview(bookId: number, review: ReviewIn): Promise<ReviewOut> {
  const response = await apiFetch(`/books/${bookId}/review`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
  return response.json();
}

export async function deleteMyReview(bookId: number): Promise<Response> {
  return apiFetch(`/books/${bookId}/review`, { method: "DELETE" });
}

export function coverUrl(bookId: number): string {
  return `/books/${bookId}/cover`;
}

export function downloadUrl(bookId: number): string {
  return `/books/${bookId}/file`;
}

// Fetched as bytes, not passed as a URL to the EPUB renderer: the file only
// ever leaves the server through this authenticated request, never as a
// static asset the browser (or a rendering library) could fetch on its own.
export async function fetchBookFile(id: number): Promise<ArrayBuffer> {
  const response = await apiFetch(downloadUrl(id));
  return response.arrayBuffer();
}

export function formatRatingSummary(book: {
  average_rating: number | null;
  rating_count: number;
}): string {
  if (book.average_rating === null) return "Not rated yet";
  const rounded = Math.round(book.average_rating * 10) / 10;
  const suffix = book.rating_count === 1 ? "rating" : "ratings";
  return `${rounded} / 5 (${book.rating_count} ${suffix})`;
}
