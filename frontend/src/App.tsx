import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import VendorPage from "./pages/VendorPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/vendor/:name" element={<VendorPage />} />
    </Routes>
  );
}
