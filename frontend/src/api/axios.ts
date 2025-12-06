import axios from 'axios';
import { usarAuthStore } from '../context/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el Token a cada petición
api.interceptors.request.use((config) => {
  // Leemos la clave que definimos en el store
  const token = localStorage.getItem('token_acceso');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar errores globales (ej: 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Si el backend dice que el token es inválido/expirado
      // Cerramos sesión en el frontend para redirigir al login
      usarAuthStore.getState().cerrarSesion();
      // Opcional: Podríamos mostrar un toast aquí si importamos toast
    }
    return Promise.reject(error);
  }
);

export default api;