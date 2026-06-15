

def adelante(f, x, h):
    #diferencia hacia adelante: usa f(x+h) y f(x).
    return (f(x + h) - f(x)) / h


def atras(f, x, h):
    #diferencia hacia atrás: usa f(x) y f(x-h).
    return (f(x) - f(x - h)) / h


def centrada(f, x, h):
    #diferencia centrada: usa puntos a cada lado de x.
    return (f(x + h) - f(x - h)) / (2 * h)


def segunda_derivada(f, x, h):
    #segunda derivada centrada: combina tres valores de f.
    return (f(x + h) - 2 * f(x) + f(x - h)) / (h**2)
