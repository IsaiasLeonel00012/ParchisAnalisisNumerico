#Representa una ficha del parchis y su estado de avance.
class Ficha:

    def __init__(self):
        #pasos == None significa que la ficha está en casa.
        #pasos == PASOS_META significa que la ficha llegó a la meta.
        self.pasos = None

    def esta_en_casa(self):
        return self.pasos is None

    def esta_en_meta(self, pasos_meta):
        return self.pasos == pasos_meta

    def mover(self, pasos):
        if self.pasos is None:
            self.pasos = 0
        else:
            self.pasos += pasos