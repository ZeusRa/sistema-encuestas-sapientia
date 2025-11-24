import axios from 'axios';

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

export default api;