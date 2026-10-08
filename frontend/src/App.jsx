import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Seleccionar from "./pages/Seleccionar.jsx";
import Ranking from "./pages/Ranking.jsx";
import CandidateDetail from "./pages/CandidateDetail.jsx";
import Datasets from "./pages/Datasets.jsx";
import Torneo from "./pages/Torneo.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />

      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/seleccionar" element={<Seleccionar />} />
        <Route path="/cargar-candidatos" element={<Navigate to="/seleccionar" replace />} />
        <Route path="/ranking" element={<Ranking />} />
        <Route path="/ranking/:rolId" element={<Ranking />} />
        <Route path="/candidatos/:cvId" element={<CandidateDetail />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/torneo" element={<Torneo />} />
        <Route path="/torneo/:rolId" element={<Torneo />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
