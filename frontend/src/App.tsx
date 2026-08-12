import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { BookDetailPage } from "./pages/BookDetailPage";
import { LibraryPage } from "./pages/LibraryPage";
import { UploadPage } from "./pages/UploadPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/books/:id" element={<BookDetailPage />} />
      </Route>
    </Routes>
  );
}
