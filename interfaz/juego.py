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
from logica.coordenadas import (
    CASAS_COLORES,
    CASILLAS,
    METAS_COLORES,
)
from logica.metodos.diferencias import adelante, atras, centrada, segunda_derivada
from logica.metodos.newton import derivada_newton
from logica.tablero import Tablero


#configuración de ventana, tablero y reglas básicas del juego.
ANCHO = 1280
ALTO = 800
ANCHO_PANEL = 330
MARGEN = 20
TABLERO_REFERENCIA_X = 500
TABLERO_REFERENCIA_LADO = 900
ULTIMA_CASILLA = 68
PASOS_META = 63
EN_CASA = -1
CASILLAS_SEGURAS = {12, 17, 29, 34, 46, 51, 63, 68}

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
            jugador["fichas"] = [
                {"pasos": EN_CASA}
                for _ in range(4)
            ]
            jugador["seises_consecutivos"] = 0
            jugador["ultima_ficha"] = None
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
        self.movimiento_pendiente = None
        self.fichas_validas = []
        self.repetir_al_terminar = False
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

    def obtener_casilla_ficha(self, jugador, ficha):
        if ficha["pasos"] in (EN_CASA, PASOS_META):
            return None
        if ficha["pasos"] < 0 or ficha["pasos"] >= len(jugador["ruta"]):
            return None
        return jugador["ruta"][ficha["pasos"]]

    def obtener_coordenada_ficha(self, jugador, ficha, indice):
        if ficha["pasos"] == EN_CASA:
            referencia = CASAS_COLORES[jugador["color_nombre"]][indice]
        elif ficha["pasos"] == PASOS_META:
            referencia = METAS_COLORES[jugador["color_nombre"]]
        else:
            casilla = self.obtener_casilla_ficha(jugador, ficha)
            referencia = CASILLAS[casilla]

        return self.transformar_coordenada(referencia)

    def fichas_en_casilla(self, casilla):
        fichas = []
        for jugador in self.jugadores:
            for indice, ficha in enumerate(jugador["fichas"]):
                if self.obtener_casilla_ficha(jugador, ficha) == casilla:
                    fichas.append((jugador, indice, ficha))
        return fichas

    def es_barrera(self, casilla):
        colores = {}
        for jugador, _, _ in self.fichas_en_casilla(casilla):
            color = jugador["color_nombre"]
            colores[color] = colores.get(color, 0) + 1
        return any(cantidad >= 2 for cantidad in colores.values())

    def puede_salir(self, jugador):
        ocupantes = self.fichas_en_casilla(jugador["salida"])
        return len(ocupantes) < 2

    def puede_mover_ficha(self, jugador, indice, pasos):
        ficha = jugador["fichas"][indice]
        if ficha["pasos"] in (EN_CASA, PASOS_META):
            return False

        destino = ficha["pasos"] + pasos
        if destino > PASOS_META:
            return False

        for posicion in range(ficha["pasos"] + 1, destino + 1):
            if posicion < PASOS_META:
                casilla = jugador["ruta"][posicion]
                if self.es_barrera(casilla):
                    return False

        if destino < PASOS_META:
            casilla_destino = jugador["ruta"][destino]
            ocupantes = self.fichas_en_casilla(casilla_destino)
            propias = sum(
                ocupante is jugador
                for ocupante, _, _ in ocupantes
            )
            if propias >= 2:
                return False
            if casilla_destino in CASILLAS_SEGURAS and len(ocupantes) >= 2:
                return False

        return True

    def fichas_de_barrera(self, jugador):
        por_casilla = {}
        for indice, ficha in enumerate(jugador["fichas"]):
            casilla = self.obtener_casilla_ficha(jugador, ficha)
            if casilla is not None:
                por_casilla.setdefault(casilla, []).append(indice)
        return {
            indice
            for indices in por_casilla.values()
            if len(indices) >= 2
            for indice in indices
        }

    def obtener_fichas_validas(self, jugador, pasos, romper_barrera=False):
        validas = [
            indice
            for indice in range(len(jugador["fichas"]))
            if self.puede_mover_ficha(jugador, indice, pasos)
        ]
        if romper_barrera:
            fichas_barrera = self.fichas_de_barrera(jugador)
            if fichas_barrera:
                validas = [
                    indice for indice in validas
                    if indice in fichas_barrera
                ]
        return validas

    def calcular_fichas_validas_pendientes(self):
        if self.movimiento_pendiente is None:
            return []

        jugador = self.jugadores[self.turno]
        pasos = self.movimiento_pendiente["pasos"]
        tipo = self.movimiento_pendiente["tipo"]
        excluir_indice = self.movimiento_pendiente.get("excluir_indice")
        romper_barrera = tipo == "dado" and self.dado == 6
        validas = self.obtener_fichas_validas(jugador, pasos, romper_barrera)

        if excluir_indice is not None:
            validas = [
                indice
                for indice in validas
                if indice != excluir_indice
            ]

        return validas

    def todas_fuera_de_casa(self, jugador):
        return all(
            ficha["pasos"] != EN_CASA
            for ficha in jugador["fichas"]
        )

    def iniciar_seleccion(self, pasos, tipo, excluir_indice=None):
        jugador = self.jugadores[self.turno]
        self.movimiento_pendiente = {
            "pasos": pasos,
            "tipo": tipo,
            "excluir_indice": excluir_indice,
        }
        self.fichas_validas = self.calcular_fichas_validas_pendientes()

        if not self.fichas_validas:
            if tipo == "bono_meta":
                self.mensaje = (
                    f"{jugador['nombre']} no puede usar el bono de 10"
                )
            elif tipo == "bono_captura":
                self.mensaje = (
                    f"{jugador['nombre']} no puede usar el bono de 20"
                )
            else:
                self.mensaje = f"{jugador['nombre']} no tiene movimiento valido"
            self.finalizar_movimiento()
            return

        opciones = ", ".join(str(indice + 1) for indice in self.fichas_validas)
        self.mensaje = f"Elige ficha {opciones} para avanzar {pasos}"

    def lanzar_dado(self):
        jugador = self.jugadores[self.turno]
        self.dado = random.randint(1, 6)
        self.repetir_al_terminar = self.dado == 6

        if self.dado == 6:
            jugador["seises_consecutivos"] += 1
        else:
            jugador["seises_consecutivos"] = 0

        if jugador["seises_consecutivos"] == 3:
            ultima = jugador["ultima_ficha"]
            if ultima is not None:
                jugador["fichas"][ultima]["pasos"] = EN_CASA
                self.mensaje = (
                    "Tres seises seguidos: "
                    f"la ficha {ultima + 1} vuelve a casa"
                )
            else:
                self.mensaje = "Tres seises seguidos: pierde el turno"
            jugador["seises_consecutivos"] = 0
            self.repetir_al_terminar = False
            self.finalizar_movimiento()
            return

        if self.dado == 6:
            todas_fuera = self.todas_fuera_de_casa(jugador)
            if self.fichas_de_barrera(jugador) or todas_fuera:
                pasos = 7 if todas_fuera else 6
                self.iniciar_seleccion(pasos, "dado")
                return
            self.mensaje = f"{jugador['nombre']} saco 6: repite turno sin mover"
            self.finalizar_movimiento()
            return

        fichas_en_casa = [
            indice
            for indice, ficha in enumerate(jugador["fichas"])
            if ficha["pasos"] == EN_CASA
        ]
        if self.dado == 5 and fichas_en_casa:
            if self.puede_salir(jugador):
                self.sacar_ficha(jugador, fichas_en_casa[0])
            else:
                self.mensaje = (
                    f"{jugador['nombre']} saco 5, pero la salida esta bloqueada"
                )
                self.finalizar_movimiento()
            return

        self.iniciar_seleccion(self.dado, "dado")

    def sacar_ficha(self, jugador, indice):
        jugador["fichas"][indice]["pasos"] = 0
        jugador["ultima_ficha"] = indice
        self.mensaje = f"{jugador['nombre']} saco la ficha {indice + 1}"
        self.ultimo_resultado = self.calcular_evento_numerico(
            jugador,
            jugador["salida"]
        )
        self.finalizar_movimiento()

    def capturar_en_casilla(self, jugador, casilla):

        #Depuración: mostrar información sobre la casilla y ocupantes

        ocupantes = [ (r['nombre'], idx) for r, idx, _ in self.fichas_en_casilla(casilla) ]
        print(f"[DEBUG] capturar_en_casilla casilla={casilla} segura={casilla in CASILLAS_SEGURAS} ocupantes={ocupantes}")

        if casilla in CASILLAS_SEGURAS:
            return False

        capturo = False
        for rival, _, ficha in self.fichas_en_casilla(casilla):
            if rival is not jugador:
                ficha["pasos"] = EN_CASA
                capturo = True
        return capturo

    def mover_ficha(self, indice):
        jugador = self.jugadores[self.turno]
        self.fichas_validas = self.calcular_fichas_validas_pendientes()
        if indice not in self.fichas_validas:
            opciones = ", ".join(
                str(indice_valido + 1)
                for indice_valido in self.fichas_validas
            )
            if opciones:
                self.mensaje = f"Opciones disponibles: {opciones}"
            else:
                self.mensaje = "No hay fichas que puedan moverse"
            return

        ficha = jugador["fichas"][indice]
        pasos = self.movimiento_pendiente["pasos"]
        ficha["pasos"] += pasos
        jugador["ultima_ficha"] = indice
        self.movimiento_pendiente = None
        self.fichas_validas = []

        if ficha["pasos"] == PASOS_META:
            if all(f["pasos"] == PASOS_META for f in jugador["fichas"]):
                self.ganador = jugador
                self.mensaje = f"GANO {jugador['nombre'].upper()}!"
                return
            self.mensaje = (
                f"Ficha {indice + 1} llego a meta: bono de 10 con otra ficha"
            )
            self.iniciar_seleccion(10, "bono_meta", excluir_indice=indice)
            return

        casilla = self.obtener_casilla_ficha(jugador, ficha)
        self.ultimo_resultado = self.calcular_evento_numerico(jugador, casilla)
        if self.capturar_en_casilla(jugador, casilla):
            self.mensaje = f"Ficha {indice + 1} capturo: bono de 20"
            self.iniciar_seleccion(20, "bono_captura")
            return

        self.mensaje = f"{jugador['nombre']} movio la ficha {indice + 1}"
        self.finalizar_movimiento()

    def finalizar_movimiento(self):
        self.movimiento_pendiente = None
        self.fichas_validas = []
        if self.repetir_al_terminar and self.ganador is None:
            self.repetir_al_terminar = False
            self.mensaje += ". Lanza otra vez"
            return

        self.repetir_al_terminar = False
        self.turno = (self.turno + 1) % len(self.jugadores)

    def calcular_evento_numerico(self, jugador, casilla):
        # Calcula la derivada aproximada según la casilla del tablero.
        # El método y el paso h se eligen automáticamente.
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
        x = 15
        y = self.height - 30
        jugador_actual = self.jugadores[self.turno]

        arcade.draw_text(
            "PARCHIS DE ANALISIS NUMERICO",
            x,
            y,
            arcade.color.WHITE,
            17,
            width=ANCHO_PANEL - 30
        )
        y -= 35

        arcade.draw_text(
            "TURNO ACTUAL",
            x,
            y,
            arcade.color.LIGHT_GRAY,
            13
        )
        y -= 20
        arcade.draw_text(
            jugador_actual["nombre"],
            x,
            y,
            jugador_actual["color"],
            20
        )
        y -= 28

        arcade.draw_text(
            f"Dado: {self.dado if self.dado > 0 else '?'}",
            x,
            y,
            arcade.color.WHITE,
            14
        )
        self.dibujar_dado(ANCHO_PANEL - 85, self.height - 140, 70)
        y -= 22

        arcade.draw_text(
            f"Seises: {jugador_actual['seises_consecutivos']}",
            x,
            y,
            arcade.color.LIGHT_YELLOW,
            12
        )
        y -= 25

        arcade.draw_text(
            "MENSAJE",
            x,
            y,
            arcade.color.LIGHT_GRAY,
            13
        )
        y -= 18
        arcade.draw_text(
            self.mensaje,
            x,
            y,
            arcade.color.WHITE,
            12,
            width=ANCHO_PANEL - 30
        )
        y -= 50

        arcade.draw_text(
            "TUS FICHAS",
            x,
            y,
            arcade.color.LIGHT_GRAY,
            13
        )
        y -= 18

        for indice, ficha in enumerate(jugador_actual["fichas"]):
            if ficha["pasos"] == EN_CASA:
                estado = "En Casa"
                color = arcade.color.GRAY
            elif ficha["pasos"] == PASOS_META:
                estado = "En Meta!"
                color = arcade.color.LIGHT_GREEN
            else:
                faltantes = PASOS_META - ficha["pasos"]
                estado = f"{faltantes} casillas"
                color = arcade.color.WHITE

            arcade.draw_text(
                f"Ficha {indice + 1}: {estado}",
                x + 10,
                y,
                color,
                12
            )
            y -= 18

        y -= 8

        if self.movimiento_pendiente is not None:
            opciones = ", ".join(
                str(i + 1) for i in self.fichas_validas
            ) or "ninguna"
            arcade.draw_text(
                "MOVIMIENTO",
                x,
                y,
                arcade.color.YELLOW,
                13
            )
            y -= 18
            arcade.draw_text(
                f"Avanza: {self.movimiento_pendiente['pasos']} pasos",
                x + 10,
                y,
                arcade.color.WHITE,
                12
            )
            y -= 18
            arcade.draw_text(
                f"Fichas: {opciones}",
                x + 10,
                y,
                arcade.color.WHITE,
                12,
                width=ANCHO_PANEL - 30
            )
            y -= 25
        else:
            arcade.draw_text(
                "PRÓXIMA ACCIÓN",
                x,
                y,
                arcade.color.LIGHT_GRAY,
                13
            )
            y -= 18
            arcade.draw_text(
                "Presiona ESPACIO",
                x + 10,
                y,
                arcade.color.WHITE,
                12
            )
            y -= 18
            arcade.draw_text(
                "para lanzar dado",
                x + 10,
                y,
                arcade.color.WHITE,
                12
            )
            y -= 25

        arcade.draw_text(
            "OTROS JUGADORES ",
            x,
            y,
            arcade.color.LIGHT_GRAY,
            13
        )
        y -= 18

        for jugador in self.jugadores:
            if jugador is jugador_actual:
                continue
            en_casa = sum(
                f["pasos"] == EN_CASA
                for f in jugador["fichas"]
            )
            en_meta = sum(
                f["pasos"] == PASOS_META
                for f in jugador["fichas"]
            )
            arcade.draw_text(
                f"{jugador['nombre']}: meta {en_meta}/4",
                x + 10,
                y,
                jugador["color"],
                12
            )
            y -= 16

        y -= 8

        if self.mostrar_resumen:
            self.dibujar_resumen(y - 10)
        elif self.metodo_comparacion is not None:
            self.dibujar_comparacion(y - 10)
        elif self.ultimo_resultado:
            self.dibujar_resultado(y - 10)

        arcade.draw_text(
            "=== CONTROLES ===",
            x,
            50,
            arcade.color.LIGHT_GRAY,
            12
        )
        arcade.draw_text(
            "ESPACIO: lanzar   1-4: ficha",
            x + 10,
            32,
            arcade.color.WHITE,
            11
        )
        arcade.draw_text(
            "C: comparar   R: reiniciar",
            x + 10,
            18,
            arcade.color.WHITE,
            11
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

        radio = max(12, 18 * lado_tablero / TABLERO_REFERENCIA_LADO)
        grupos = {}
        for jugador in self.jugadores:
            for indice, ficha in enumerate(jugador["fichas"]):
                casilla = self.obtener_casilla_ficha(jugador, ficha)
                if ficha["pasos"] == EN_CASA:
                    clave = ("casa", jugador["color_nombre"], indice)
                elif ficha["pasos"] == PASOS_META:
                    clave = ("meta", jugador["color_nombre"])
                else:
                    clave = ("casilla", casilla)
                grupos.setdefault(clave, []).append((jugador, indice, ficha))

        for jugadores_casilla in grupos.values():
            separacion = radio * 0.75
            if len(jugadores_casilla) == 1:
                desplazamientos = ((0, 0),)
            elif len(jugadores_casilla) == 2:
                desplazamientos = (
                    (-separacion, 0),
                    (separacion, 0),
                )
            elif len(jugadores_casilla) <= 4:
                desplazamientos = (
                    (-separacion, separacion),
                    (separacion, separacion),
                    (-separacion, -separacion),
                    (separacion, -separacion),
                )
            else:
                desplazamientos = tuple(
                    (
                        math.cos(indice * 2 * math.pi / len(jugadores_casilla))
                        * separacion,
                        math.sin(indice * 2 * math.pi / len(jugadores_casilla))
                        * separacion,
                    )
                    for indice in range(len(jugadores_casilla))
                )

            for (jugador, indice, ficha), (dx, dy) in zip(
                jugadores_casilla,
                desplazamientos
            ):
                x, y = self.obtener_coordenada_ficha(jugador, ficha, indice)
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
                arcade.draw_text(
                    str(indice + 1),
                    x + dx,
                    y + dy,
                    arcade.color.BLACK,
                    max(8, int(radio)),
                    anchor_x="center",
                    anchor_y="center",
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

        teclas_fichas = {
            arcade.key.KEY_1: 0,
            arcade.key.KEY_2: 1,
            arcade.key.KEY_3: 2,
            arcade.key.KEY_4: 3,
        }
        if symbol in teclas_fichas and self.movimiento_pendiente is not None:
            self.mover_ficha(teclas_fichas[symbol])
            return

        if symbol != arcade.key.SPACE or self.ganador is not None:
            return

        if self.movimiento_pendiente is not None:
            validas = self.calcular_fichas_validas_pendientes()
            opciones = ", ".join(str(i + 1) for i in validas)
            if opciones:
                self.mensaje = f"Primero elige una ficha: {opciones}"
            else:
                self.mensaje = "No hay fichas que puedan moverse"
            return

        self.mostrar_resumen = False
        self.metodo_comparacion = None
        self.lanzar_dado()


def main():
    Juego()
    arcade.run()


if __name__ == "__main__":
    main()
