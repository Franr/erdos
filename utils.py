import os
import copy
import cPickle as pickle


# Constantes de posicionamiento de figuras
AL_FINAL = 1
DEBAJO = 2
ENCIMA = 3

# Constantes de mensajes
ALERTA_VERSION = """
La version del archivo guardado difiere de la version de Erdos.
Esto podria ocasionarle problemas
"""


class Singleton(type):

    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._inst[cls]


class Config(object):

    VERSION = 1.4
    ANCHO = 350
    ALTO = 350


class Archivo(object):

    def __init__(self, path, arbol):
        self.path = path
        self.arbol = arbol
        self.version = Config.VERSION
        self.nombre = os.path.basename(path)


class IdHandler(object):

    uid = 0

    @classmethod
    def get(cls):
        cls.uid += 1
        return cls.uid


class Historial(object):

    def __init__(self):
        self.historia = []
        self._indice = -1

    def guardar(self, arbol):
        self._indice += 1
        self.historia = self.historia[:self._indice]
        self.historia.append(copy.deepcopy(arbol))

    def deshacer(self):
        if self._indice > 0:
            self._indice -= 1
            return self._get()

        return False

    def rehacer(self):
        if self._indice != len(self.historia) - 1:
            self._indice += 1
            return self._get()
        return False

    def _get(self):
        return self.historia[self._indice]


def unpack_list(lista):
    return lista[0], lista[1::]


def path_ui(archivo_ui):
    path = "gui"  # pasar a un config!
    return os.path.join(path, archivo_ui)


def guardar_objeto(obj, path):
    archivo = Archivo(path, obj)
    try:
        with open(path, 'wb') as salida:
            pickle.dump(archivo, salida, pickle.HIGHEST_PROTOCOL)
    except Exception as err:
        raise err
    return archivo


def cargar_objeto(path):
    try:
        with open(path, 'rb') as entrada:
            archivo = pickle.load(entrada)
    except Exception as err:
        raise err
    return archivo
