import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';

// Interfaz para los datos decodificados del token (Payload)
interface UsuarioDecodificado {
  sub: string; // nombre_usuario ('sub' en el estándar JWT)
  rol: string;
  debe_cambiar_clave?: boolean; // Nuevo campo opcional
  permisos?: string[]; // Lista de códigos de permisos
}

// Interfaz del Estado Global de Autenticación
interface EstadoAuth {
  token: string | null;
  usuario: UsuarioDecodificado | null;
  estaAutenticado: boolean;

  // Acciones (Métodos)
  iniciarSesion: (nuevoToken: string) => void;
  cerrarSesion: () => void;
  tienePermiso: (codigo: string) => boolean;
}

export const usarAuthStore = create<EstadoAuth>((set, get) => {
  // Intentar recuperar sesión del localStorage al inicio (Persistencia)
  const tokenGuardado = localStorage.getItem('token_acceso');
  let usuarioInicial = null;

  if (tokenGuardado) {
    try {
      // Decodificamos el token para obtener los datos del usuario sin llamar al backend
      usuarioInicial = jwtDecode<UsuarioDecodificado>(tokenGuardado);
    } catch (e) {
      // Si el token es inválido o expiró, limpiamos
      localStorage.removeItem('token_acceso');
    }
  }

  return {
    token: usuarioInicial ? tokenGuardado : null,
    usuario: usuarioInicial,
    estaAutenticado: !!usuarioInicial, // Solo autenticado si se pudo decodificar el usuario

    iniciarSesion: (nuevoToken: string) => {
      try {
        const decodificado = jwtDecode<UsuarioDecodificado>(nuevoToken);
        localStorage.setItem('token_acceso', nuevoToken);
        set({
          token: nuevoToken,
          usuario: decodificado,
          estaAutenticado: true
        });
      } catch (error) {
        console.error("Error al decodificar token durante inicio de sesión", error);
      }
    },

    cerrarSesion: () => {
      localStorage.removeItem('token_acceso');
      set({
        token: null,
        usuario: null,
        estaAutenticado: false
      });
    },

    tienePermiso: (codigo: string) => {
        const usuario = get().usuario;
        if (!usuario || !usuario.permisos) return false;
        // Administrador por defecto suele tener todo, pero aquí validamos lista estricta
        // Si el backend envía todos los permisos para admin, esto funciona igual.
        return usuario.permisos.includes(codigo);
    }
  };
});