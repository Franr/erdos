#!/usr/bin/python

# este script se usa solo para pruebas de desarrollo
# no compilar desde aca
# chino no comer eso cosa, nunca!

from IPython import embed

from erdos import Run


def lanzar():
    r = Run()

    ## funciones para DEBUG
    def p():
        r.ex.controlador().arbol.imprimir()

    def g(x):
        return r.ex.controlador().arbol.get_nodo(x)

    def s():
        return r.ex.controlador().selectedItems()[0]

    def a():
        from PyQt4 import Qt
        return Qt.QApplication.activeModalWidget()

    def o():
        return r.ex.controlador().historial

    def c():
        return r.ex.controlador()

    embed()


if __name__ == '__main__':
    lanzar()
