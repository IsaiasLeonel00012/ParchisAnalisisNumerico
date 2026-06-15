#Cálculo de diferencias divididas para interpolación de Newton.

def diferencias_divididas(x, y):

    n = len(x)
    tabla = [[0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        tabla[i][0] = y[i]

    for j in range(1, n):
        for i in range(n - j):

            tabla[i][j] = (
                tabla[i + 1][j - 1] - tabla[i][j - 1]
            ) / (x[i + j] - x[i])

    return tabla


def derivada_newton(x, y, punto):
    #usa la tabla de diferencias divididas para calcular la derivada.
    tabla = diferencias_divididas(x, y)
    coeficientes = tabla[0]
    derivada = 0.0

    for grado in range(1, len(coeficientes)):
        suma_productos = 0.0

        for omitido in range(grado):
            producto = 1.0

            for indice in range(grado):
                if indice != omitido:
                    producto *= punto - x[indice]

            suma_productos += producto

        derivada += coeficientes[grado] * suma_productos

    return derivada, tabla
