import { ThemeProvider, CssBaseline } from "@mui/material";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import theme from "./theme";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Páginas
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import LayoutDashboard from "./layout/LayoutDashboard";
import RutaProtegida from "./components/RutaProtegida";
import Encuestas from "./pages/Encuestas";
import CrearEncuesta from "./pages/CrearEncuesta";
import CambiarClave from "./pages/CambiarClave";
import GestionUsuarios from "./pages/admin/Usuarios";
import GestionPermisos from "./pages/admin/GestionPermisos";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ToastContainer position="top-right" autoClose={3000} />
      
      <BrowserRouter>
        <Routes>
          {/* Ruta pública */}
          <Route path="/login" element={<Login />} />

          {/* Rutas Protegidas */}
          <Route element={<RutaProtegida />}>
            <Route element={<LayoutDashboard />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              
              {/* Rutas de Encuestas */}
              <Route path="/encuestas" element={<Encuestas />} />
              <Route path="/encuestas/crear" element={<CrearEncuesta />} /> {/* Nueva Ruta */}
              
              {/* Ruta de Cambio de Clave */}
              <Route path="/cambiar-clave" element={<CambiarClave />} />

              {/* Rutas de Administración */}
              <Route path="/admin/usuarios" element={<GestionUsuarios />} />
              <Route path="/admin/permisos" element={<GestionPermisos />} />

            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}


export default App;