import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Viewer from "./pages/Viewer";
import WordCloudModal from "./components/WordCloudModal";

export default function App() {
  return (
    <BrowserRouter>

      {/*  Modal must be here so it stays global */}
      <WordCloudModal />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/view/:filename" element={<Viewer />} />
      </Routes>

    </BrowserRouter>
  );
}
