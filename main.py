from fastapi import FastAPI, HTTPException, Depends
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from schemas import ActividadPost, InstructorPost, ClasePost, ActividadUpdate, ActividadCantidad, AlumnoUpdate, TurnoPost, AlumnoPost, AlumnoResponse, ClaseResponse, AlumnoClaseRequest, LoginRequest, LoginResponse
import datetime

app = FastAPI()

def get_db():
    connection = get_db_connection()
    try:
        yield connection
    finally:
        connection.close()


def format_time(timedelta):
            total_seconds = int(timedelta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:02}" #setea los turnos con 2 digitos, si es 9 pasa a ser 09

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
    query_delete_clases = "DELETE FROM clase WHERE id_actividad = %s"
    cursor.execute(query_delete_clases, (id_actividad,)) #elimina todas las clases de esa actividad
    db.commit()
    query = "DELETE FROM actividades WHERE id_actividad = %s"
    cursor.execute(query, (id_actividad,))
    db.commit() 
    cursor.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    return {"detail": f"Actividad con id {id_actividad} eliminada exitosamente"}
        


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


#Obtener las actividades con la cantidad de alumnos inscriptos
@app.get("/actividades/populares", response_model=list[ActividadCantidad])
async def get_actividades_populares(db=Depends(get_db)):
    try:
        cursor = db.cursor(dictionary=True)
        
        query = """
        SELECT
            a.nombre AS actividad,
            COUNT(ac.ci_alumno) AS cantidad_alumnos
        FROM
            actividades a
        JOIN
            clase c ON a.id_actividad = c.id_actividad
        JOIN
            alumno_clase ac ON c.id_clase = ac.id_clase
        GROUP BY
            a.id_actividad
        ORDER BY
            cantidad_alumnos DESC;
        """
        
        cursor.execute(query)
        resultados = cursor.fetchall()

        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos: {e}")
    finally:
        cursor.close()
        db.close()



#############################################################################################
#                               TURNOS                                                      #
#############################################################################################

#Obtener turnos
@app.get("/turnos")
async def get_turnos(db=Depends(get_db)):
    cursor = db.cursor()
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
        return f"{hours:02}:{minutes:02}:{seconds:02}" 
    turnos_list = []
    for turno in turnos:
        turnos_list.append({
            "id_turno": turno[0],
            "hora_inicio": format_time(turno[1]),
            "hora_fin": format_time(turno[2]),
        })
    cursor.close()
    return turnos_list



#Agregar turnos
@app.post("/turnos")
async def create_turno(turno: TurnoPost, db=Depends(get_db)):
    cursor = db.cursor()
    query = """
    INSERT INTO turnos (hora_inicio, hora_fin)
    VALUES (%s, %s)
    """
    cursor.execute(query, (turno.hora_inicio, turno.hora_fin))
    db.commit() 
    cursor.close()

    nuevo_id = cursor.lastrowid

    return {"id_turno": nuevo_id, "hora_inicio": turno.hora_inicio, "hora_fin": turno.hora_fin}

#Eliminar turno
@app.delete("/turnos/{id_turno}")
async def delete_turno(id_turno: int, db=Depends(get_db)):
    cursor = db.cursor()
    query = "DELETE FROM turnos WHERE id_turno = %s"
    cursor.execute(query, (id_turno,))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    db.commit() 
    cursor.close()
    return {"message": f"Turno con id {id_turno} eliminado con éxito"}

#Obtener turnos con la cantidad de clases que se dictan
@app.get("/turnos/clases")
async def get_turnos_clases(db=Depends(get_db)):
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT
            CONCAT(DATE_FORMAT(t.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(t.hora_fin, '%H:%i')) AS turno,
            COUNT(c.id_clase) AS clases_dictadas
        FROM
            turnos t
        JOIN
            clase c ON t.id_turno = c.id_turno
        GROUP BY
            t.id_turno
        ORDER BY
            clases_dictadas DESC;
        """
        cursor.execute(query)
        turnos_clases = cursor.fetchall()
        cursor.close()
        return turnos_clases

#############################################################################################
#                               ALUMNOS                                                     #
#############################################################################################

#Obtener alumnos
@app.get("/alumnos")
async def get_alumnos(db=Depends(get_db)):
        cursor = db.cursor(dictionary=True)        
        cursor.execute("SELECT * FROM alumnos")
        alumnos = cursor.fetchall()

        if not alumnos:
            raise HTTPException(status_code=404, detail="No hay alumnos disponibles.")
        
        cursor.close()
        db.close()

        return alumnos

#Agregar alumno
@app.post("/alumnos")
async def create_alumno(alumno: AlumnoPost, db=Depends(get_db)):
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


#Eliminar alumno
@app.delete("/alumnos/{ci_alumno}")
async def delete_alumno(ci_alumno: int, db=Depends(get_db)):
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


#Modificar datos de alumno
@app.put("/alumnos/{ci_alumno}")
async def update_alumno(ci_alumno: int, alumno: AlumnoUpdate, db=Depends(get_db)):
        cursor = db.cursor()

        cursor.execute("SELECT * FROM alumnos WHERE ci_alumno = %s", (ci_alumno,))
        existe_alumno = cursor.fetchone()

        if not existe_alumno:
            raise HTTPException(status_code=404, detail="Alumno no encontrado.")

        update_fields = []
        values = []

        if alumno.nombre:
            update_fields.append("nombre = %s")
            values.append(alumno.nombre)

        if alumno.apellido:
            update_fields.append("apellido = %s")
            values.append(alumno.apellido)

        if alumno.fecha_nacimiento:
            update_fields.append("fecha_nacimiento = %s")
            values.append(alumno.fecha_nacimiento)

        if alumno.telefono:
            update_fields.append("telefono = %s")
            values.append(alumno.telefono)

        if alumno.correo:
            update_fields.append("correo = %s")
            values.append(alumno.correo)

        if alumno.contraseña:
            update_fields.append("contraseña = %s")
            values.append(alumno.contraseña)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

        values.append(ci_alumno)

        query = f"UPDATE alumnos SET {', '.join(update_fields)} WHERE ci_alumno = %s"
        cursor.execute(query, tuple(values))
        db.commit()  
        cursor.close()
        db.close()
        return {"message": "Alumno actualizado exitosamente", "ci_alumno": ci_alumno}


#############################################################################################
#                               INSTRUCTORES                                                #
#############################################################################################

#Obtener los instructores
@app.get("/instructores")
async def get_alumnos(db=Depends(get_db)):
        cursor = db.cursor(dictionary=True)        
        cursor.execute("SELECT * FROM instructores")
        instructores = cursor.fetchall()

        if not instructores:
            raise HTTPException(status_code=404, detail="No hay instructores disponibles.")
        
        cursor.close()
        db.close()

        return instructores

@app.post("/instructores")
async def create_instructor(instructor: InstructorPost, db=Depends(get_db)):
    cursor = db.cursor()

    cursor.execute("SELECT ci_instructor FROM instructores WHERE ci_instructor = %s", (instructor.ci_instructor,))
    existing_instructor = cursor.fetchone()

    if existing_instructor:
        raise HTTPException(status_code=400, detail="El instructor ya existe con ese CI.")

    query = """
        INSERT INTO instructores (ci_instructor, nombre, apellido)
        VALUES (%s, %s, %s);
    """
    cursor.execute(query, (instructor.ci_instructor, instructor.nombre, instructor.apellido))
    db.commit()
    cursor.close()

    return {
        "ci_instructor": instructor.ci_instructor,
        "nombre": instructor.nombre,
        "apellido": instructor.apellido
    }
        

#############################################################################################
#                               REGISTRO                                                    #
#############################################################################################

#Registra un alumno y guarda la cedula, correo y contraseña en la tabla login
@app.post("/register", response_model=AlumnoResponse)
async def register_alumno(alumno: AlumnoPost, db = Depends(get_db)):
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

    query = """
        INSERT INTO login (correo, contraseña, ci_alumno)
        VALUES (%s, %s, %s)
    """
    values = (alumno.correo, alumno.contraseña, alumno.ci_alumno)

    cursor.execute(query, values)
    db.commit()

    cursor.close()
    db.close()

    return AlumnoResponse(
            ci_alumno=alumno.ci_alumno,
            nombre=alumno.nombre,
            apellido=alumno.apellido,
            fecha_nacimiento=alumno.fecha_nacimiento,
            telefono=alumno.telefono,
            correo=alumno.correo,
            contraseña=alumno.contraseña,
        )


#############################################################################################
#                              ELIMINAR DE TABLA LOGIN                                      #
#############################################################################################

@app.delete("/login/{ci_alumno}")
async def delete_alumno(ci_alumno: int, db=Depends(get_db)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT * FROM login WHERE ci_alumno = %s", (ci_alumno,))
        alumno = cursor.fetchone()

        if not alumno:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        query = "DELETE FROM login WHERE ci_alumno = %s"
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
#                               LOGIN                                                       #
#############################################################################################

@app.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db=Depends(get_db)):

    cursor = db.cursor()

    cursor.execute("SELECT * FROM alumnos WHERE correo = %s AND contraseña = %s", (login_data.correo, login_data.contraseña, ))
    db_usuario = cursor.fetchone()

    if not db_usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {"message": "Inicio de sesión exitoso"}

#############################################################################################
#                               CLASES                                                      #
#############################################################################################


#Mostrar clases
@app.get("/clases", response_model=list[ClaseResponse])
def get_clases(db = Depends(get_db)):
    
    cursor = db.cursor()

    cursor.execute("""
        SELECT 
            c.id_clase,
            c.id_actividad,
            a.nombre AS nombre_actividad,
            a.costo AS costo_actividad,
            i.nombre AS nombre_instructor,
            t.hora_inicio AS hora_inicio,
            t.hora_fin AS hora_fin
        FROM 
            clase c
        JOIN 
            actividades a ON c.id_actividad = a.id_actividad
        JOIN 
            instructores i ON c.ci_instructor = i.ci_instructor
        JOIN 
            turnos t ON c.id_turno = t.id_turno;
    """)
    clases = cursor.fetchall()

    response = []
    for clase in clases:
        response.append(ClaseResponse(
            id_clase=clase[0],
            id_actividad = clase[1],
            nombre_actividad=clase[2],
            nombre_instructor=clase[4],
            hora_inicio=format_time(clase[5]),
            hora_fin=format_time(clase[6]),
            costo_actividad=clase[3]
        ))

    return response


#Poder inscribirse a una clase
@app.post("/inscribir_alumno")
async def inscribir_alumno(alumno_clase: AlumnoClaseRequest, db = Depends(get_db)):
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM alumno_clase WHERE id_clase = %s AND ci_alumno = %s",
            (alumno_clase.id_clase, alumno_clase.ci_alumno),
        )
        existe = cursor.fetchone()

        if existe:
            raise HTTPException(status_code=400, detail="El alumno ya está inscrito en esta clase.")

        if alumno_clase.id_equipamiento is not None:
            query = """
                INSERT INTO alumno_clase (id_clase, ci_alumno, id_equipamiento)
                VALUES (%s, %s, %s)
            """
            values = (alumno_clase.id_clase, alumno_clase.ci_alumno, alumno_clase.id_equipamiento)
        else:
            query = """
                INSERT INTO alumno_clase (id_clase, ci_alumno)
                VALUES (%s, %s)
            """
            values = (alumno_clase.id_clase, alumno_clase.ci_alumno)
        cursor.execute(query, values)

        db.commit()

        return {"message": "Alumno inscrito correctamente.", "data": alumno_clase}


#Eliminar alumno de clase
@app.delete("/desinscribir_alumno/{id_clase}/{ci_alumno}")
def desinscribir_alumno(ci_alumno: int, id_clase: int, db=Depends(get_db)):
    cursor=db.cursor()

    cursor.execute("SELECT * FROM alumno_clase WHERE ci_alumno = %s AND id_clase = %s",
            (ci_alumno, id_clase),)
     
    inscripcion = cursor.fetchone()
    if not inscripcion:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró la inscripción del alumno {ci_alumno} en la clase {id_clase}.",
        )
     
    cursor.execute("DELETE FROM alumno_clase WHERE ci_alumno = %s AND id_clase = %s",
        (ci_alumno, id_clase),)
    db.commit()
     
    return {
        "message": "Alumno desinscrito correctamente.",
        "ci_alumno": ci_alumno,
        "id_clase": id_clase,
    }


#Obtener las clases inscriptas de un alumno
@app.get("/clases_alumno/{ci_alumno}")
def get_clases_alumno(ci_alumno: int, db=Depends(get_db)):
    cursor = db.cursor()
    query = """
            SELECT 
                ac.id_clase,
                a.nombre AS nombre_actividad,
                i.nombre AS nombre_instructor,
                t.hora_inicio,
                t.hora_fin
            FROM 
                alumno_clase ac
            JOIN 
                clase c ON ac.id_clase = c.id_clase
            JOIN 
                actividades a ON c.id_actividad = a.id_actividad
            JOIN 
                instructores i ON c.ci_instructor = i.ci_instructor
            JOIN 
                turnos t ON c.id_turno = t.id_turno
            WHERE 
                ac.ci_alumno = %s
        """
    cursor.execute(query, (ci_alumno,))
    clases = cursor.fetchall()

    if not clases:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron clases para el alumno con CI {ci_alumno}.",
    )

    result = [
            {
                "id_clase": clase[0],
                "nombre_actividad": clase[1],
                "nombre_instructor": clase[2],
                "hora_inicio": format_time(clase[3]),
                "hora_fin": format_time(clase[4]),
            }
            for clase in clases
        ]

    return {"ci_alumno": ci_alumno, "clases_inscriptas": result}

#Crear una clase
@app.post("/clases")
async def create_clase(clase: ClasePost, db=Depends(get_db)):
    cursor = db.cursor()

    cursor.execute("SELECT id_actividad FROM actividades WHERE nombre = %s", (clase.nombre_actividad,))
    actividad = cursor.fetchone()

    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    id_actividad = actividad[0]

    query = """
        INSERT INTO clase (ci_instructor, id_actividad, id_turno, dictada)
        VALUES (%s, %s, %s, %s);
    """
    cursor.execute(query, (clase.ci_instructor, id_actividad, clase.id_turno, clase.dictada))
    db.commit()
    cursor.close()

    id_clase = cursor.lastrowid

    return {
        "id_clase": id_clase,
        "ci_instructor": clase.ci_instructor,
        "nombre_actividad": clase.nombre_actividad,
        "id_turno": clase.id_turno,
        "dictada": clase.dictada
    }

#############################################################################################
#                               EQUIPAMIENTO                                                #
#############################################################################################

#Obtener equipamiento
@app.get("/equipamiento")
async def get_alumnos(db=Depends(get_db)):
        cursor = db.cursor(dictionary=True)        
        cursor.execute("SELECT * FROM equipamiento")
        equipamiento = cursor.fetchall()

        if not equipamiento:
            raise HTTPException(status_code=404, detail="No hay equipamiento disponibles.")
        
        cursor.close()
        db.close()

        return equipamiento



