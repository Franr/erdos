# -*- coding: utf-8 -*-
from utils import IdHandler


class Arbol(object):

    def __init__(self, contprin):
        # raiz -> contenedor principal
        self.raiz = contprin

    def get_nodo(self, uid):
        return self.raiz.get_nodo(uid)

    def imprimir(self):
        self.raiz.imprimir()


class Nodo(object):

    def __init__(self):
        self.uid = IdHandler.get()
        self.hijos = []

    def __str__(self):
        return "Nodo " + str(self.uid) + " " + str(type(self))

    def __repr__(self):
        return "Nodo " + str(self.uid) + " " + str(type(self))

    def agregar_hijo(self, item, pos=-1):
        if pos is -1:
            self.hijos.append(item)
        else:
            self.hijos.insert(pos, item)

    def imprimir(self, nivel=0):
        print (" " * nivel * 4) + \
            str(" ".join([str(nivel), str(self)]))
        for h in self.hijos:
            h.imprimir(nivel + 1)

    def get_nodo(self, uid, nivel=0):
        ''' Devuelve una dupla con:
            [0] el nodo que contenga el uid especificado
            [1] el nivel donde dicho nodo se encuentra
            De no encontrarlo a a traves del arbol, devuelve falso.
            Se implementa a traves de una busqueda en profundidad.
        '''

        if self.uid == uid:
            return self, nivel
        else:
            for h in self.hijos:
                x, nivel_x = h.get_nodo(uid, nivel + 1)
                if x:
                    return x, nivel_x
        return False, 0
