def adelante(f, x, h):
    return (f(x + h) - f(x)) / h


def atras(f, x, h):
    return (f(x) - f(x - h)) / h


def centrada(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)


def segunda_derivada(f, x, h):
    return (f(x + h) - 2 * f(x) + f(x - h)) / (h**2)
