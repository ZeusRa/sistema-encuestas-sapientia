import { Navigate, Outlet } from 'react-router-dom';
import { usarAuthStore } from '../context/authStore';

const RutaProtegida = () => {
  const estaAutenticado = usarAuthStore(state => state.estaAutenticado);

  // Si no está autenticado, redirigir al login
  if (!estaAutenticado) {
    return <Navigate to="/login" replace />;
  }

  // Si está autenticado, renderizar las rutas hijas (Outlet)
  return <Outlet />;
};

export default RutaProtegida;