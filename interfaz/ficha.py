class Ficha:

    def __init__(self):
        # pasos == None means the ficha is en casa
        # pasos == PASOS_META means the ficha reached la meta
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