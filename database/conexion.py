import sqlite3


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
    return sqlite3.connect("parchis.db")


def crear_tabla():
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
