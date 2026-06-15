import os
import sqlite3

#ubicación del archivo de base de datos SQLite dentro del proyecto.
RUTA_BASE_DATOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "parchis.db"
)

COLUMNAS = {
    "jugador": "TEXT",
    "funcion": "TEXT",
    "x": "REAL",
    "h": "REAL",
    "resultado": "REAL",
    "exacto": "REAL",
    "orden_derivada": "INTEGER",
    "fecha": "TEXT",
}


def conectar():
    return sqlite3.connect(RUTA_BASE_DATOS)


def crear_tabla():
    #crea la tabla de resultados si no existe y agrega columnas nuevas.
    with conectar() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS partidas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metodo TEXT,
                error REAL,
                posicion INTEGER
            )
        """)

        existentes = {
            fila[1]
            for fila in conexion.execute("PRAGMA table_info(partidas)")
        }
        for nombre, definicion in COLUMNAS.items():
            if nombre not in existentes:
                conexion.execute(
                    f"ALTER TABLE partidas ADD COLUMN {nombre} {definicion}"
                )


def guardar_resultado(
    metodo,
    error,
    posicion,
    jugador=None,
    funcion=None,
    x=None,
    h=None,
    resultado=None,
    exacto=None,
    orden_derivada=1,
):
    crear_tabla()

    with conectar() as conexion:
        conexion.execute("""
            INSERT INTO partidas(
                metodo,
                error,
                posicion,
                jugador,
                funcion,
                x,
                h,
                resultado,
                exacto,
                orden_derivada,
                fecha
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            metodo,
            error,
            posicion,
            jugador,
            funcion,
            x,
            h,
            resultado,
            exacto,
            orden_derivada,
        ))


def obtener_h_optimos():
    #obtiene el mejor valor de h para cada método según el menor error registrado.
    crear_tabla()

    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT metodo, h, MIN(error)
            FROM partidas
            WHERE h IS NOT NULL
            GROUP BY metodo
            ORDER BY metodo
        """).fetchall()

    return filas


def obtener_errores_por_metodo(metodo):
    #devuelve el error mínimo observado para cada h del método elegido.
    crear_tabla()

    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT h, MIN(error)
            FROM partidas
            WHERE metodo = ? AND h IS NOT NULL
            GROUP BY h
            ORDER BY h DESC
        """, (metodo,)).fetchall()

    return filas
