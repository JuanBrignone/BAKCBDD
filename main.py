from fastapi import FastAPI, HTTPException, Depends
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from schemas import ActividadPost, ActividadUpdate, TurnoPost, AlumnoPost

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
    cursor = db.cursor(dictionary=True) #es para que la respuesta te la devuelva con el nombre de las columnas
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

#Obtener turnos
@app.get("/turnos")
async def get_turnos(db=Depends(get_db)):
    cursor = db.cursor()
    try:
        query = "SELECT id_turno, hora_inicio, hora_fin FROM turnos"
        cursor.execute(query)
        turnos = cursor.fetchall()

        if not turnos:
            raise HTTPException(status_code=404, detail="No se encontraron turnos")

        def format_time(timedelta):
            total_seconds = int(timedelta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:02}" #setea los turnos con 2 digitos, si es 9 pasa a ser 09
        
        turnos_list = []
        for turno in turnos:
            turnos_list.append({
                "id_turno": turno[0],
                "hora_inicio": format_time(turno[1]),
                "hora_fin": format_time(turno[2]),
            })
        return turnos_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los turnos: {e}")
    finally:
        cursor.close()


#Agregar turnos
@app.post("/turnos")
async def create_turno(turno: TurnoPost, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        query = """
        INSERT INTO turnos (hora_inicio, hora_fin)
        VALUES (%s, %s)
        """
        cursor.execute(query, (turno.hora_inicio, turno.hora_fin))
        db.commit() 

        nuevo_id = cursor.lastrowid

        return {"id_turno": nuevo_id, "hora_inicio": turno.hora_inicio, "hora_fin": turno.hora_fin}

    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error al crear el turno: {e}")
    
    finally:
        cursor.close()


#Eliminar turno
@app.delete("/turnos/{id_turno}")
async def delete_turno(id_turno: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        query = "DELETE FROM turnos WHERE id_turno = %s"
        cursor.execute(query, (id_turno,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        
        db.commit() 
        return {"message": f"Turno con id {id_turno} eliminado con éxito"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar el turno: {e}")
    
    finally:
        cursor.close()


#############################################################################################
#                               ALUMNOS                                                     #
#############################################################################################

#Obtener alumnos
@app.get("/alumnos")
async def get_alumnos(db=Depends(get_db)):
    try:
        cursor = db.cursor(dictionary=True)        
        cursor.execute("SELECT * FROM alumnos")
        alumnos = cursor.fetchall()

        if not alumnos:
            raise HTTPException(status_code=404, detail="No hay alumnos disponibles.")
        
        cursor.close()
        db.close()

        return alumnos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los turnos: {e}")
    finally:
        cursor.close()



#Agregar alumno
@app.post("/alumnos")
async def create_alumno(alumno: AlumnoPost, db=Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM alumnos WHERE ci_alumno = %s", (alumno.ci_alumno,))
        existing_alumno = cursor.fetchone()

        if existing_alumno:
            raise HTTPException(status_code=400, detail="El alumno ya existe en la base de datos.")

        query = """
            INSERT INTO alumnos (ci_alumno, nombre, apellido, fecha_nacimiento, telefono, correo, contraseña)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (alumno.ci_alumno, alumno.nombre, alumno.apellido, alumno.fecha_nacimiento, alumno.telefono, alumno.correo, alumno.contraseña)

        cursor.execute(query, values)
        db.commit()  

        cursor.close()
        db.close()

        return {"message": "Alumno creado exitosamente", "ci_alumno": alumno.ci_alumno}

    except Exception as e:
        db.rollback()  
        raise HTTPException(status_code=500, detail=f"Error al crear el alumno: {e}")
    finally:
        cursor.close()


#Eliminar alumno
@app.delete("/alumnos/{ci_alumno}")
async def delete_alumno(ci_alumno: int, db=Depends(get_db)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT * FROM alumnos WHERE ci_alumno = %s", (ci_alumno,))
        alumno = cursor.fetchone()

        if not alumno:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        query = "DELETE FROM alumnos WHERE ci_alumno = %s"
        cursor.execute(query, (ci_alumno,))

        db.commit()  

        cursor.close()
        db.close()

        return {"message": "Alumno eliminado exitosamente", "ci_alumno": ci_alumno}

    except Exception as e:
        db.rollback()  
        raise HTTPException(status_code=500, detail=f"Error al eliminar el alumno: {e}")
    finally:
        cursor.close()  


#############################################################################################
#                               INSTRUCTORES                                                #
#############################################################################################

#Obtener los instructores
@app.get("/instructores")
async def get_alumnos(db=Depends(get_db)):
    try:
        cursor = db.cursor(dictionary=True)        
        cursor.execute("SELECT * FROM instructores")
        instructores = cursor.fetchall()

        if not instructores:
            raise HTTPException(status_code=404, detail="No hay instructores disponibles.")
        
        cursor.close()
        db.close()

        return instructores

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los instructores: {e}")
    finally:
        cursor.close()