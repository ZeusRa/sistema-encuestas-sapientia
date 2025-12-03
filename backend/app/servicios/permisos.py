
from sqlalchemy.orm import Session
from app.modelos import UsuarioAdmin, Permiso, RolPermiso, UsuarioPermiso

class ServicioPermisos:
    def __init__(self, bd: Session):
        self.bd = bd

    def obtener_permisos_usuario(self, id_usuario: int, rol: str) -> list[str]:
        """
        Calcula la lista efectiva de códigos de permisos para un usuario.
        Lógica:
        1. Obtener permisos base del ROL.
        2. Aplicar sobreescrituras (explicitas) del USUARIO.
           - Si usuario_permiso.tiene = True -> Se agrega (si no estaba).
           - Si usuario_permiso.tiene = False -> Se quita (si estaba).
        """
        # 1. Permisos del Rol
        permisos_rol = (
            self.bd.query(Permiso.codigo)
            .join(RolPermiso, RolPermiso.id_permiso == Permiso.id_permiso)
            .filter(RolPermiso.id_rol == rol)
            .all()
        )
        codigos_efectivos = {p.codigo for p in permisos_rol}

        # 2. Permisos Específicos del Usuario
        permisos_usuario = (
            self.bd.query(Permiso.codigo, UsuarioPermiso.tiene)
            .join(UsuarioPermiso, UsuarioPermiso.id_permiso == Permiso.id_permiso)
            .filter(UsuarioPermiso.id_usuario == id_usuario)
            .all()
        )

        for codigo, tiene in permisos_usuario:
            if tiene:
                codigos_efectivos.add(codigo)
            elif codigo in codigos_efectivos:
                codigos_efectivos.remove(codigo) # Denegación explícita

        return list(codigos_efectivos)

    def tiene_permiso(self, id_usuario: int, rol: str, codigo_permiso: str) -> bool:
        permisos = self.obtener_permisos_usuario(id_usuario, rol)
        return codigo_permiso in permisos
