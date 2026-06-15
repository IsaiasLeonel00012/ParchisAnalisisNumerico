H_VALORES = (
    1.0,
    0.1,
    0.01,
    0.001,
    0.0001,
    0.000001,
    0.00000001,
    0.0000000001,
)


class Tablero:

    def tipo_casilla(self, posicion):
        #selecciona el método numérico según la posición de la casilla.
        if posicion % 11 == 0:
            return "segunda"
        if posicion % 7 == 0:
            return "newton"
        if posicion % 5 == 0:
            return "centrada"
        if posicion % 3 == 0:
            return "atras"
        return "adelante"

    def h_para_casilla(self, posicion):
        #devuelve un valor de h diferente según la casilla.
        return H_VALORES[(posicion - 1) % len(H_VALORES)]
