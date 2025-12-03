
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import obtener_bd
from app.modelos import Permiso, RolAdmin, RolPermiso, UsuarioPermiso, UsuarioAdmin
from app.schemas import PermisoSalida, AsignacionPermisoUsuario, AsignacionPermisoRol
from app.routers.auth import obtener_usuario_actual
from app.servicios.permisos import ServicioPermisos

router = APIRouter(
    prefix="/permisos",
    tags=["Permisos"],
    dependencies=[Depends(obtener_usuario_actual)] # Todos requieren estar logueados
)

def verificar_permiso_gestion(usuario: UsuarioAdmin = Depends(obtener_usuario_actual), bd: Session = Depends(obtener_bd)):
    # Usamos el servicio para verificar si tiene el permiso "usuario:gestionar"
    # OJO: Si el admin "pierde" este permiso, nadie podría gestionar.
    # Fallback de seguridad: El rol ADMINISTRADOR siempre debería poder, pero validamos permiso formalmente.
    servicio = ServicioPermisos(bd)
    if not servicio.tiene_permiso(usuario.id_admin, usuario.rol, "usuario:gestionar") and usuario.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar accesos")
    return usuario

@router.get("/", response_model=List[PermisoSalida])
def listar_todos_los_permisos(bd: Session = Depends(obtener_bd), admin=Depends(verificar_permiso_gestion)):
    return bd.query(Permiso).all()

@router.get("/roles/{rol}", response_model=List[str])
def obtener_permisos_rol(rol: RolAdmin, bd: Session = Depends(obtener_bd), admin=Depends(verificar_permiso_gestion)):
    permisos = bd.query(Permiso.codigo).join(RolPermiso).filter(RolPermiso.id_rol == rol).all()
    return [p.codigo for p in permisos]

@router.put("/roles/{rol}", status_code=200)
def actualizar_permisos_rol(
    rol: RolAdmin,
    asignacion: AsignacionPermisoRol,
    bd: Session = Depends(obtener_bd),
    admin=Depends(verificar_permiso_gestion)
):
    # 1. Limpiar permisos actuales del rol
    bd.query(RolPermiso).filter(RolPermiso.id_rol == rol).delete()

    # 2. Insertar nuevos
    for id_p in asignacion.id_permisos:
        nuevo = RolPermiso(id_rol=rol, id_permiso=id_p)
        bd.add(nuevo)

    bd.commit()
    return {"mensaje": "Permisos del rol actualizados"}

@router.get("/usuarios/{id_usuario}", response_model=List[AsignacionPermisoUsuario])
def obtener_permisos_explicitos_usuario(
    id_usuario: int,
    bd: Session = Depends(obtener_bd),
    admin=Depends(verificar_permiso_gestion)
):
    """Devuelve solo las asignaciones explícitas (excepciones)"""
    res = bd.query(UsuarioPermiso).filter(UsuarioPermiso.id_usuario == id_usuario).all()
    # Mapear manualmente a esquema si es necesario, o pydantic lo hace
    return [AsignacionPermisoUsuario(id_permiso=p.id_permiso, tiene=p.tiene) for p in res]

@router.put("/usuarios/{id_usuario}", status_code=200)
def asignar_permiso_usuario(
    id_usuario: int,
    asignacion: AsignacionPermisoUsuario,
    bd: Session = Depends(obtener_bd),
    admin=Depends(verificar_permiso_gestion)
):
    """
    Crea o actualiza una excepción para un usuario.
    Si se quiere 'resetear' (volver al default del rol), habría que borrar la entrada.
    Aquí implementamos upsert.
    """
    existente = bd.query(UsuarioPermiso).filter(
        UsuarioPermiso.id_usuario == id_usuario,
        UsuarioPermiso.id_permiso == asignacion.id_permiso
    ).first()

    if existente:
        existente.tiene = asignacion.tiene
    else:
        nuevo = UsuarioPermiso(id_usuario=id_usuario, id_permiso=asignacion.id_permiso, tiene=asignacion.tiene)
        bd.add(nuevo)

    bd.commit()
    return {"mensaje": "Permiso de usuario actualizado"}

@router.delete("/usuarios/{id_usuario}/{id_permiso}", status_code=200)
def eliminar_permiso_usuario(
    id_usuario: int,
    id_permiso: int,
    bd: Session = Depends(obtener_bd),
    admin=Depends(verificar_permiso_gestion)
):
    """Elimina la asignación explícita, el usuario vuelve a heredar del rol"""
    bd.query(UsuarioPermiso).filter(
        UsuarioPermiso.id_usuario == id_usuario,
        UsuarioPermiso.id_permiso == id_permiso
    ).delete()
    bd.commit()
    return {"mensaje": "Excepción de permiso eliminada"}
