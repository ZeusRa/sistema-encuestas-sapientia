
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import obtener_bd
from app.modelos import PlantillaOpciones, PlantillaOpcionDetalle, UsuarioAdmin
from app.schemas import PlantillaOpcionesSalida, PlantillaOpcionesCrear
from app.routers.auth import obtener_usuario_actual

router = APIRouter(
    prefix="/plantillas",
    tags=["Plantillas de Opciones"],
    dependencies=[Depends(obtener_usuario_actual)]
)

@router.get("/", response_model=List[PlantillaOpcionesSalida])
def listar_plantillas(bd: Session = Depends(obtener_bd)):
    return bd.query(PlantillaOpciones).options(joinedload(PlantillaOpciones.detalles)).all()

@router.post("/", response_model=PlantillaOpcionesSalida, status_code=status.HTTP_201_CREATED)
def crear_plantilla(
    plantilla: PlantillaOpcionesCrear,
    bd: Session = Depends(obtener_bd)
):
    nueva = PlantillaOpciones(
        nombre=plantilla.nombre,
        descripcion=plantilla.descripcion
    )
    bd.add(nueva)
    bd.flush()

    for det in plantilla.detalles:
        detalle = PlantillaOpcionDetalle(
            id_plantilla=nueva.id,
            texto_opcion=det.texto_opcion,
            orden=det.orden
        )
        bd.add(detalle)

    bd.commit()
    bd.refresh(nueva)
    return nueva

@router.put("/{id}", response_model=PlantillaOpcionesSalida)
def actualizar_plantilla(
    id: int,
    datos: PlantillaOpcionesCrear,
    bd: Session = Depends(obtener_bd)
):
    existente = bd.query(PlantillaOpciones).filter(PlantillaOpciones.id == id).first()
    if not existente:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    existente.nombre = datos.nombre
    existente.descripcion = datos.descripcion

    # Reemplazar detalles
    bd.query(PlantillaOpcionDetalle).filter(PlantillaOpcionDetalle.id_plantilla == id).delete()

    for det in datos.detalles:
        detalle = PlantillaOpcionDetalle(
            id_plantilla=id,
            texto_opcion=det.texto_opcion,
            orden=det.orden
        )
        bd.add(detalle)

    bd.commit()
    bd.refresh(existente)
    return existente

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_plantilla(id: int, bd: Session = Depends(obtener_bd)):
    existente = bd.query(PlantillaOpciones).filter(PlantillaOpciones.id == id).first()
    if not existente:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    bd.delete(existente)
    bd.commit()
    return None
