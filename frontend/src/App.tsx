import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { BookDetailPage } from "./pages/BookDetailPage";
import { LibraryPage } from "./pages/LibraryPage";
import { ReaderPage } from "./pages/ReaderPage";
import { UploadPage } from "./pages/UploadPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/books/:id" element={<BookDetailPage />} />
      </Route>
      {/* Outside Layout: the reader is full-screen, no persistent sidebar. */}
      <Route path="/books/:id/read" element={<ReaderPage />} />
    </Routes>
  );
}
