import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CargarCandidatos from "./pages/CargarCandidatos.jsx";
import Ranking from "./pages/Ranking.jsx";
import CandidateDetail from "./pages/CandidateDetail.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />

      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/cargar-candidatos" element={<CargarCandidatos />} />
        <Route path="/ranking/:rolId" element={<Ranking />} />
        <Route path="/candidatos/:candidatoId" element={<CandidateDetail />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
