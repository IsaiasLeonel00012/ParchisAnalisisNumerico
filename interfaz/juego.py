import math
import os
import random
import sys

import arcade

RUTA_PROYECTO = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(RUTA_PROYECTO)

from database.conexion import (
    crear_tabla,
    guardar_resultado,
    obtener_errores_por_metodo,
    obtener_h_optimos,
)
from logica.coordenadas import CASILLAS, METAS_COLORES
from logica.metodos.diferencias import adelante, atras, centrada, segunda_derivada
from logica.metodos.newton import derivada_newton
from logica.tablero import Tablero


ANCHO = 1280
ALTO = 800
ANCHO_PANEL = 330
MARGEN = 20
TABLERO_REFERENCIA_X = 500
TABLERO_REFERENCIA_LADO = 900
ULTIMA_CASILLA = 68
PASOS_META = 63

CONFIGURACION_JUGADORES = (
    {
        "nombre": "Amarillo",
        "color_nombre": "amarillo",
        "salida": 5,
        "color": arcade.color.YELLOW,
        "funcion_nombre": "f(x) = x^2",
        "funcion": lambda x: x**2,
        "derivada": lambda x: 2 * x,
        "segunda": lambda x: 2.0,
        "x": 2.0,
    },
    {
        "nombre": "Azul",
        "color_nombre": "azul",
        "salida": 22,
        "color": arcade.color.BLUE,
        "funcion_nombre": "f(x) = sen(x)",
        "funcion": math.sin,
        "derivada": math.cos,
        "segunda": lambda x: -math.sin(x),
        "x": 1.0,
    },
    {
        "nombre": "Rojo",
        "color_nombre": "rojo",
        "salida": 39,
        "color": arcade.color.RED,
        "funcion_nombre": "f(x) = exp(x)",
        "funcion": math.exp,
        "derivada": math.exp,
        "segunda": math.exp,
        "x": 1.0,
    },
    {
        "nombre": "Verde",
        "color_nombre": "verde",
        "salida": 56,
        "color": arcade.color.GREEN,
        "funcion_nombre": "f(x) = x^3",
        "funcion": lambda x: x**3,
        "derivada": lambda x: 3 * x**2,
        "segunda": lambda x: 6 * x,
        "x": 2.0,
    },
)

NOMBRES_METODOS = {
    "adelante": "Diferencia hacia adelante",
    "atras": "Diferencia hacia atras",
    "centrada": "Diferencia centrada",
    "newton": "Diferencias divididas de Newton",
    "segunda": "Segunda derivada centrada",
}


def crear_ruta(salida):
    return (
        list(range(salida, ULTIMA_CASILLA + 1))
        + list(range(1, salida))
    )


class Juego(arcade.Window):

    def __init__(self):
        super().__init__(
            ANCHO,
            ALTO,
            "Parchis de Analisis Numerico",
            resizable=True
        )
        self.fondo = arcade.load_texture(
            os.path.join(RUTA_PROYECTO, "recursos", "imagenes", "fondo.png")
        )
        self.tablero = Tablero()
        crear_tabla()
        self.reiniciar()

    def reiniciar(self):
        self.jugadores = []

        for configuracion in CONFIGURACION_JUGADORES:
            jugador = dict(configuracion)
            jugador["ruta"] = crear_ruta(jugador["salida"])
            jugador["pasos"] = 0
            self.jugadores.append(jugador)

        self.turno = 0
        self.dado = 0
        self.ganador = None
        self.ultimo_resultado = None
        self.mostrar_resumen = False
        self.resumen = []
        self.indice_comparacion = -1
        self.metodo_comparacion = None
        self.comparacion = []
        self.mensaje = "Presiona ESPACIO para lanzar el dado"

    def obtener_tablero(self):
        espacio_ancho = self.width - ANCHO_PANEL - (MARGEN * 2)
        espacio_alto = self.height - (MARGEN * 2)
        lado = max(1, min(espacio_ancho, espacio_alto))
        x = ANCHO_PANEL + MARGEN + (espacio_ancho - lado) / 2
        y = MARGEN + (espacio_alto - lado) / 2
        return x, y, lado

    def transformar_coordenada(self, referencia):
        referencia_x, referencia_y = referencia
        tablero_x, tablero_y, lado = self.obtener_tablero()
        escala = lado / TABLERO_REFERENCIA_LADO
        x = tablero_x + (referencia_x - TABLERO_REFERENCIA_X) * escala
        y = tablero_y + referencia_y * escala
        return x, y

    def obtener_casilla_jugador(self, jugador):
        if jugador["pasos"] == PASOS_META:
            return None
        return jugador["ruta"][jugador["pasos"]]

    def obtener_coordenada_jugador(self, jugador):
        casilla = self.obtener_casilla_jugador(jugador)

        if casilla is None:
            referencia = METAS_COLORES[jugador["color_nombre"]]
        else:
            referencia = CASILLAS[casilla]

        return self.transformar_coordenada(referencia)

    def calcular_evento_numerico(self, jugador, casilla):
        metodo = self.tablero.tipo_casilla(casilla)
        h = self.tablero.h_para_casilla(casilla)
        funcion = jugador["funcion"]
        x = jugador["x"]
        orden = 1
        tabla_newton = None

        if metodo == "adelante":
            aproximado = adelante(funcion, x, h)
        elif metodo == "atras":
            aproximado = atras(funcion, x, h)
        elif metodo == "centrada":
            aproximado = centrada(funcion, x, h)
        elif metodo == "newton":
            nodos = [x - h, x, x + h]
            valores = [funcion(nodo) for nodo in nodos]
            aproximado, tabla_newton = derivada_newton(
                nodos,
                valores,
                x
            )
        else:
            orden = 2
            aproximado = segunda_derivada(funcion, x, h)

        if orden == 1:
            exacto = jugador["derivada"](x)
        else:
            exacto = jugador["segunda"](x)

        resultado = {
            "jugador": jugador["nombre"],
            "funcion": jugador["funcion_nombre"],
            "casilla": casilla,
            "metodo": metodo,
            "metodo_nombre": NOMBRES_METODOS[metodo],
            "x": x,
            "h": h,
            "aproximado": aproximado,
            "exacto": exacto,
            "error": abs(exacto - aproximado),
            "orden": orden,
            "tabla_newton": tabla_newton,
        }
        if h >= 0.1:
            resultado["tipo_error"] = (
                "h es grande: la formula pierde precision."
            )
        elif h <= 0.00000001:
            resultado["tipo_error"] = (
                "h es muy pequeno: puede aparecer redondeo."
            )
        else:
            resultado["tipo_error"] = (
                "h tiene un tamano equilibrado."
            )

        guardar_resultado(
            metodo=metodo,
            error=resultado["error"],
            posicion=casilla,
            jugador=jugador["nombre"],
            funcion=jugador["funcion_nombre"],
            x=x,
            h=h,
            resultado=aproximado,
            exacto=exacto,
            orden_derivada=orden,
        )
        return resultado

    def dibujar_panel(self):
        texto_superior = self.height - 45
        jugador_actual = self.jugadores[self.turno]

        arcade.draw_text(
            "PARCHIS DE ANALISIS NUMERICO",
            15,
            texto_superior,
            arcade.color.WHITE,
            17,
            width=ANCHO_PANEL - 30
        )
        arcade.draw_text(
            f"Turno: {jugador_actual['nombre']}   Dado: {self.dado}",
            15,
            texto_superior - 45,
            jugador_actual["color"],
            18
        )
        arcade.draw_text(
            self.mensaje,
            15,
            texto_superior - 82,
            arcade.color.WHITE,
            13,
            width=ANCHO_PANEL - 105
        )
        self.dibujar_dado(250, texto_superior - 120, 60)

        y = texto_superior - 135
        for jugador in self.jugadores:
            casilla = self.obtener_casilla_jugador(jugador)
            ubicacion = "META" if casilla is None else f"casilla {casilla}"
            arcade.draw_text(
                (
                    f"{jugador['nombre']}: {ubicacion} "
                    f"({jugador['pasos']}/{PASOS_META})"
                ),
                15,
                y,
                jugador["color"],
                12
            )
            y -= 25

        if self.mostrar_resumen:
            self.dibujar_resumen(y - 10)
        elif self.metodo_comparacion is not None:
            self.dibujar_comparacion(y - 10)
        elif self.ultimo_resultado:
            self.dibujar_resultado(y - 10)

        arcade.draw_text(
            "ESPACIO: lanzar   A: h optimo",
            15,
            42,
            arcade.color.WHITE,
            12
        )
        arcade.draw_text(
            "C: comparar errores   R: reiniciar",
            15,
            22,
            arcade.color.WHITE,
            12
        )

    def dibujar_dado(self, x, y, lado):
        arcade.draw_rect_filled(
            arcade.LBWH(x, y, lado, lado),
            arcade.color.WHITE
        )
        arcade.draw_rect_outline(
            arcade.LBWH(x, y, lado, lado),
            arcade.color.BLACK,
            3
        )

        puntos = {
            1: ((0.5, 0.5),),
            2: ((0.25, 0.75), (0.75, 0.25)),
            3: ((0.25, 0.75), (0.5, 0.5), (0.75, 0.25)),
            4: (
                (0.25, 0.75), (0.75, 0.75),
                (0.25, 0.25), (0.75, 0.25),
            ),
            5: (
                (0.25, 0.75), (0.75, 0.75), (0.5, 0.5),
                (0.25, 0.25), (0.75, 0.25),
            ),
            6: (
                (0.25, 0.75), (0.75, 0.75),
                (0.25, 0.5), (0.75, 0.5),
                (0.25, 0.25), (0.75, 0.25),
            ),
        }

        if self.dado == 0:
            arcade.draw_text(
                "?",
                x + lado / 2,
                y + lado / 2,
                arcade.color.BLACK,
                28,
                anchor_x="center",
                anchor_y="center",
            )
            return

        for punto_x, punto_y in puntos[self.dado]:
            arcade.draw_circle_filled(
                x + punto_x * lado,
                y + punto_y * lado,
                lado * 0.08,
                arcade.color.BLACK
            )

    def dibujar_lineas(self, lineas, y, tamano=12, espacio=20):
        for linea in lineas:
            arcade.draw_text(
                linea,
                15,
                y,
                arcade.color.WHITE,
                tamano,
                width=ANCHO_PANEL - 30
            )
            y -= espacio

    def dibujar_resultado(self, y):
        resultado = self.ultimo_resultado
        lineas = [
            f"RESULTADO DE LA CASILLA {resultado['casilla']}",
            f"Jugador: {resultado['jugador']}",
            f"Funcion: {resultado['funcion']}",
            f"Formula usada: {resultado['metodo_nombre']}",
            "",
            f"La formula calculo: {resultado['aproximado']:.6g}",
            f"El valor correcto es: {resultado['exacto']:.6g}",
            f"Se equivoco por: {resultado['error']:.3e}",
            "",
            f"Paso h utilizado: {resultado['h']:.1e}",
            resultado["tipo_error"],
        ]
        if resultado["tabla_newton"] is not None:
            coeficientes = resultado["tabla_newton"][0]
            lineas.append(
                "DD: "
                + ", ".join(f"{valor:.3g}" for valor in coeficientes)
            )

        self.dibujar_lineas(lineas, y, tamano=11, espacio=18)

    def dibujar_comparacion(self, y):
        lineas = [
            "ERROR SEGUN h",
            NOMBRES_METODOS[self.metodo_comparacion],
        ]

        if not self.comparacion:
            lineas.append("Aun no hay datos para este metodo.")
        else:
            for h, error in self.comparacion:
                lineas.append(f"h={h:.1e}  error={error:.2e}")

        self.dibujar_lineas(lineas, y, tamano=11, espacio=18)

    def dibujar_resumen(self, y):
        lineas = ["MEJOR h OBSERVADO"]

        if not self.resumen:
            lineas.append("Aun no hay resultados.")
        else:
            for metodo, h, error in self.resumen:
                lineas.append(
                    f"{metodo}: h={h:.1e}, error={error:.2e}"
                )

        self.dibujar_lineas(lineas, y, tamano=11, espacio=18)

    def on_draw(self):
        self.clear()
        tablero_x, tablero_y, lado_tablero = self.obtener_tablero()
        arcade.draw_texture_rect(
            self.fondo,
            arcade.LBWH(
                tablero_x,
                tablero_y,
                lado_tablero,
                lado_tablero
            )
        )
        self.dibujar_panel()

        radio = max(7, 11 * lado_tablero / TABLERO_REFERENCIA_LADO)
        grupos = {}
        for jugador in self.jugadores:
            casilla = self.obtener_casilla_jugador(jugador)
            clave = (
                jugador["color_nombre"]
                if casilla is None
                else casilla
            )
            grupos.setdefault(clave, []).append(jugador)

        for jugadores_casilla in grupos.values():
            separacion = radio * 0.75
            if len(jugadores_casilla) == 1:
                desplazamientos = ((0, 0),)
            elif len(jugadores_casilla) == 2:
                desplazamientos = (
                    (-separacion, 0),
                    (separacion, 0),
                )
            else:
                desplazamientos = (
                    (-separacion, separacion),
                    (separacion, separacion),
                    (-separacion, -separacion),
                    (separacion, -separacion),
                )

            for jugador, (dx, dy) in zip(
                jugadores_casilla,
                desplazamientos
            ):
                x, y = self.obtener_coordenada_jugador(jugador)
                arcade.draw_circle_filled(
                    x + dx,
                    y + dy,
                    radio,
                    jugador["color"]
                )
                arcade.draw_circle_outline(
                    x + dx,
                    y + dy,
                    radio,
                    arcade.color.BLACK,
                    2
                )

        if self.ganador is not None:
            arcade.draw_text(
                f"GANO {self.ganador['nombre'].upper()}!",
                15,
                55,
                self.ganador["color"],
                22
            )

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
            return

        if symbol == arcade.key.R:
            self.reiniciar()
            return

        if symbol == arcade.key.A:
            self.mostrar_resumen = not self.mostrar_resumen
            self.metodo_comparacion = None
            self.resumen = obtener_h_optimos()
            return

        if symbol == arcade.key.C:
            metodos = list(NOMBRES_METODOS)
            self.indice_comparacion = (
                self.indice_comparacion + 1
            ) % len(metodos)
            self.metodo_comparacion = metodos[self.indice_comparacion]
            self.comparacion = obtener_errores_por_metodo(
                self.metodo_comparacion
            )
            self.mostrar_resumen = False
            return

        if symbol != arcade.key.SPACE or self.ganador is not None:
            return

        self.mostrar_resumen = False
        self.metodo_comparacion = None
        jugador = self.jugadores[self.turno]
        self.dado = random.randint(1, 6)
        nueva_posicion = jugador["pasos"] + self.dado

        if nueva_posicion <= PASOS_META:
            jugador["pasos"] = nueva_posicion
            self.mensaje = (
                f"{jugador['nombre']} avanzo {self.dado} casillas"
            )

        else:
            faltan = PASOS_META - jugador["pasos"]
            self.mensaje = (
                f"{jugador['nombre']} necesita exactamente {faltan}"
            )
            self.turno = (self.turno + 1) % len(self.jugadores)
            return

        casilla = self.obtener_casilla_jugador(jugador)
        if casilla is None:
            self.ganador = jugador
            self.mensaje = f"GANO {jugador['nombre'].upper()}!"
            return

        self.ultimo_resultado = self.calcular_evento_numerico(
            jugador,
            casilla
        )

        self.turno = (self.turno + 1) % len(self.jugadores)


def main():
    Juego()
    arcade.run()


if __name__ == "__main__":
    main()
