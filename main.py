from fastapi import FastAPI, HTTPException, Depends
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from schemas import ActividadPost, ActividadUpdate

app = FastAPI()

def get_db():
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las direcciones
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los encabezados
)



#############################################################################################
#                               ACTIVIDADES                                                 #
#############################################################################################

#Obtener las actividades
@app.get("/actividades")
async def read_actividades(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM actividades")
        actividades = cursor.fetchall()
        if not actividades:
            raise HTTPException(status_code=404, detail="No hay actividades disponibles")
        return actividades
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las actividades: {e}")
    finally:
        cursor.close()

#Agregar Actividad
@app.post("/actividades")
async def create_actividad(actividad: ActividadPost, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        query = """
        INSERT INTO actividades (nombre, descripcion, costo)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (actividad.nombre, actividad.descripcion, actividad.costo))
        db.commit() 

        id_actividad = cursor.lastrowid
        return {"id_actividad": id_actividad, "nombre": actividad.nombre, "descripcion": actividad.descripcion, "costo": actividad.costo}
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error al crear la actividad: {e}")
    finally:
        cursor.close()


#Eliminar actividad
@app.delete("/actividades/{id_actividad}")
async def delete_actividad(id_actividad: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        query = "DELETE FROM actividades WHERE id_actividad = %s"
        cursor.execute(query, (id_actividad,))
        db.commit() 

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        return {"detail": f"Actividad con id {id_actividad} eliminada exitosamente"}
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error al eliminar la actividad: {e}")
    finally:
        cursor.close()


#Editar una actividad
@app.put("/actividades/{id_actividad}")
async def update_actividad(id_actividad: int, actividad: ActividadUpdate, db=Depends(get_db)):
    cursor = db.cursor()
    update_values = []
    update_fields = []

    if actividad.nombre is not None:
        update_fields.append("nombre = %s")
        update_values.append(actividad.nombre)
    
    if actividad.descripcion is not None:
        update_fields.append("descripcion = %s")
        update_values.append(actividad.descripcion)
    
    if actividad.costo is not None:
        update_fields.append("costo = %s")
        update_values.append(actividad.costo)

    if not update_fields:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un campo para actualizar.")

    update_values.append(id_actividad)

    query = f"UPDATE actividades SET {', '.join(update_fields)} WHERE id_actividad = %s"
    
    try:
        cursor.execute(query, tuple(update_values))
        db.commit()  

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        return {"detail": f"Actividad con id {id_actividad} actualizada exitosamente"}
    
    except Exception as e:
        db.rollback()  
        raise HTTPException(status_code=500, detail=f"Error al actualizar la actividad: {e}")
    
    finally:
        cursor.close()


#############################################################################################
#                               TURNOS                                                      #
#############################################################################################

