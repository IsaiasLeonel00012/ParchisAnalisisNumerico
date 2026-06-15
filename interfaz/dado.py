import random

#simula un dado de seis caras para el juego.
class Dado:

    def lanzar(self):
        return random.randint(1, 6)