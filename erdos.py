#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import threading
import copy
import subprocess
import os

from PyQt4 import QtGui, uic

import lib
import utils
import gui
import items

MARCA_CAMBIO = "* "


class Erdos(QtGui.QMainWindow):

    def __init__(self):
        super(Erdos, self).__init__()
        self.paginas = {}
        self.nodo_copiado = None
        self.ventana_ejec = gui.VentanaEjecuccion(self)

        uic.loadUi(utils.path_ui("principal.ui"), self)
        self.agregar_tab()

        # Menu Archivo
        self.actionNuevo.triggered.connect(self.agregar_tab)
        self.actionAbrir.triggered.connect(self.abrir)
        self.actionGuardar.triggered.connect(self.guardar)
        self.actionGuardar_como.triggered.connect(self.guardar_como)
        self.actionCerrar.triggered.connect(self.cerrar)
        self.actionSalir.triggered.connect(self.close)

        # Menu Edicion
        self.actionCopiar.triggered.connect(self.copiar)
        self.actionPegar.triggered.connect(self.pegar)
        self.actionEliminar.triggered.connect(self.eliminar)
        self.actionEditar.triggered.connect(self.editar)
        self.actionDeshacer.triggered.connect(self.deshacer)
        self.actionRehacer.triggered.connect(self.rehacer)

        # Panel figuras
        self.actionSentencia.triggered.connect(self.agregar_sentencia)
        self.actionEntrada.triggered.connect(self.agregar_entrada)
        self.actionSalida.triggered.connect(self.agregar_salida)
        self.actionSi.triggered.connect(self.agregar_if)
        self.actionPara.triggered.connect(self.agregar_for)
        self.actionMientras.triggered.connect(self.agregar_while)
        self.actionHasta.triggered.connect(self.agregar_until)
        self.actionCaso.triggered.connect(self.agregar_case)

        # Panel Debug
        self.actionReload.triggered.connect(self.reload)

        # Menu herramientas
        self.actionEjecutar.triggered.connect(self.ejecutar)
        self.actionExportar.triggered.connect(self.exportar)
        self.actionMostrar_salida.triggered.connect(self.abrir_ventana_ejec)

        # Menu de ayuda
        self.actionManual_de_usuario.triggered.connect(self.manual)
        self.actionAcerca_de_Erdos.triggered.connect(self.acerca_de)
        self.actionAcerca_de_Qt.triggered.connect(self.acerca_de_qt)

        self.show()

    def controlador(self):
        # devuelve el controlador del diagrama actual
        return self.paginas.get(self.tabWidget.currentWidget())

    def abrir(self):
        dialogo = gui.dialogo_abrir(self)
        if dialogo.exec_():
            path = str(dialogo.selectedFiles()[0])
            tab_index, controlador = self.agregar_tab()
            nombre_archivo, alerta = controlador.abrir(path)
            if alerta:
                QtGui.QMessageBox.warning(
                    self, "Atencion", utils.ALERTA_VERSION
                )
            self.set_texto_tab(tab_index, nombre_archivo)

    def guardar(self):
        if self.controlador().archivo:
            self.controlador().guardar()
            self.quitar_marca_cambio()
        else:
            self.guardar_como()

    def guardar_como(self):
        dialogo = gui.dialogo_guardar(self)
        if dialogo.exec_():
            path = str(dialogo.selectedFiles()[0])
            if not path.endswith(".erd"):
                path += ".erd"
            nombre_archivo = self.controlador().guardar_como(path)
            tab_index = self.tabWidget.currentIndex()
            self.set_texto_tab(tab_index, nombre_archivo)

    def exportar(self):
        dialogo = gui.dialogo_exportar(self)
        if dialogo.exec_():
            path = str(dialogo.selectedFiles()[0])
            if not path.endswith(".png"):
                path += ".png"
            self.controlador().exportar(path)

    def cerrar(self):
        self.paginas.pop(self.tabWidget.currentWidget())
        tab_index = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(tab_index)
        if not len(self.paginas):
            self.agregar_tab()

    def eliminar(self):
        self.controlador().eliminar_seleccionado()

    def copiar(self):
        figura = self.get_seleccionado()
        if hasattr(figura, 'nodo'):
            if figura.nodo != self.controlador().arbol.raiz:
                self.nodo_copiado = copy.deepcopy(figura.nodo)

    def pegar(self):
        if self.nodo_copiado:
            destino = self.get_seleccionado()
            self.controlador().regen(self.nodo_copiado, destino)

    def editar(self):
        figura = self.get_seleccionado()

        if type(figura) == items.ErdosSentenciaItem:
            texto = figura.nodo.texto
            pos, datos = utils.unpack_list(
                gui.SentenciaInput(self, texto).get()
            )

        elif type(figura) == items.ErdosEntradaItem:
            variable = figura.nodo.variable
            tipo_dato = figura.nodo.tipo_dato
            texto = figura.nodo.texto_dialogo
            pos, datos = utils.unpack_list(
                gui.EntradaInput(self, variable, texto, tipo_dato).get()
            )

        elif type(figura) == items.ErdosSalidaItem:
            variable = figura.nodo.variable
            texto = figura.nodo.texto_dialogo
            prompt = figura.nodo.prompt
            pos, datos = utils.unpack_list(
                gui.SalidaInput(self, variable, texto, prompt).get()
            )

        elif type(figura) == items.ErdosIfItem:
            condiciones = figura.nodo.condiciones
            pos, datos = utils.unpack_list(
                gui.IfInput(self, condiciones).get()
            )

        elif type(figura) == items.ErdosCaseItem:
            n_var = figura.nodo.nom_var
            r_min = figura.nodo.rango_minimo
            r_max = figura.nodo.rango_maximo
            pos, datos = utils.unpack_list(
                gui.ForInput(self, True, n_var, r_min, r_max).get()
            )

        elif type(figura) == items.ErdosForItem:
            n_var = figura.nodo.nom_var
            r_min = figura.nodo.rango_minimo
            r_max = figura.nodo.rango_maximo
            pos, datos = utils.unpack_list(
                gui.ForInput(self, False, n_var, r_min, r_max).get()
            )

        elif type(figura) == items.ErdosWhileItem:
            condiciones = figura.nodo.condiciones
            pos, datos = utils.unpack_list(
                gui.IfInput(self, condiciones).get()
            )

        elif type(figura) == items.ErdosUntilItem:
            condiciones = figura.nodo.condiciones
            pos, datos = utils.unpack_list(
                gui.IfInput(self, condiciones).get()
            )

        else:
            pos = 0

        if pos:
            figura.editar(*datos)
            self.controlador().guardar_historial()
            self.controlador().reposicionar()
            self.agregar_marca_cambio()

    def deshacer(self):
        self.controlador().deshacer()
        self.agregar_marca_cambio()

    def rehacer(self):
        self.controlador().rehacer()
        self.agregar_marca_cambio()

    def agregar_tab(self):
        vista = QtGui.QGraphicsView()
        controlador = items.ControladorGUI(vista)
        self.paginas[vista] = controlador
        index = self.tabWidget.addTab(vista, "Nuevo " + str(len(self.paginas)))
        self.tabWidget.setCurrentIndex(index)
        return index, controlador

    def set_texto_tab(self, index, nombre_archivo):
        self.tabWidget.setTabText(index, nombre_archivo)

    def reload(self):
        rel = reload(lib)
        reg = reload(gui)
        rei = reload(items)
        reu = reload(utils)
        print "Modulos re-cargados: ", rel, reg, rei, reu

    def get_seleccionado(self):
        selected = self.controlador().selectedItems()
        if selected:
            return selected[0]
        return self.controlador().contenedorGUI

    def agregar_sentencia(self):
        destino = self.get_seleccionado()
        pos, sentencia = gui.SentenciaInput(self).get()
        if pos:
            self.controlador().agregar_sentencia(pos, destino, sentencia)
            self.agregar_marca_cambio()

    def agregar_entrada(self):
        destino = self.get_seleccionado()
        pos, var, tipodt, texto = gui.EntradaInput(self).get()
        if pos:
            self.controlador().agregar_entrada(pos, destino, var, tipodt, texto)
            self.agregar_marca_cambio()

    def agregar_salida(self):
        destino = self.get_seleccionado()
        pos, var, texto, prompt = gui.SalidaInput(self).get()
        if pos:
            self.controlador().agregar_salida(pos, destino, var, texto, prompt)
            self.agregar_marca_cambio()

    def agregar_if(self):
        destino = self.get_seleccionado()
        pos, condiciones = gui.IfInput(self).get()
        if pos:
            self.controlador().agregar_if(pos, destino, condiciones)
            self.agregar_marca_cambio()

    def agregar_for(self):
        destino = self.get_seleccionado()
        pos, n_var, r_max, r_min = gui.ForInput(self).get()
        if pos:
            self.controlador().agregar_for(pos, destino, n_var, r_max, r_min)
            self.agregar_marca_cambio()

    def agregar_while(self):
        destino = self.get_seleccionado()
        pos, condiciones = gui.IfInput(self).get()
        if pos:
            self.controlador().agregar_while(pos, destino, condiciones)
            self.agregar_marca_cambio()

    def agregar_until(self):
        destino = self.get_seleccionado()
        pos, condiciones = gui.IfInput(self).get()
        if pos:
            self.controlador().agregar_until(pos, destino, condiciones)
            self.agregar_marca_cambio()

    def agregar_case(self):
        destino = self.get_seleccionado()
        pos, n_var, r_max, r_min = gui.ForInput(self, True).get()
        if pos:
            self.controlador().agregar_case(pos, destino, n_var, r_min, r_max)
            self.agregar_marca_cambio()

    def agregar_marca_cambio(self):
        index = self.tabWidget.currentIndex()
        nombre = self.tabWidget.tabText(index)
        if not str(nombre).startswith(MARCA_CAMBIO):
            self.tabWidget.setTabText(index, MARCA_CAMBIO + nombre)

    def quitar_marca_cambio(self):
        index = self.tabWidget.currentIndex()
        nombre = self.tabWidget.tabText(index)
        if str(nombre).startswith(MARCA_CAMBIO):
            nombre = nombre[2:]
            self.tabWidget.setTabText(index, nombre)

    def ejecutar(self):
        salida, fallo = self.controlador().ejecutar()
        if fallo:
            self.controlador().resaltar_figura(fallo)

        nombre_diag = self.tabWidget.tabText(self.tabWidget.currentIndex())
        self.ventana_ejec.agregar_salida(nombre_diag, salida.getvalue())
        self.abrir_ventana_ejec()

    def abrir_ventana_ejec(self):
        self.ventana_ejec.exec_()

    def manual(self):
        manual = "manual_erdos.pdf"
        if sys.platform.startswith('linux'):
            subprocess.call(["xdg-open", manual])
        else:
            os.startfile(manual)

    def acerca_de(self):
        texto = """
- Erdos -

Version %s
Erdos es una herramienta para crear y ejecutar diagramas Nassi-Schneiderman.

Integrantes:
* Forconi, Geronimo
* Rivera, Francisco
* Virga, Andres

Proyecto Final - UTN Facultad Regional Rosario - 2013
"""
        QtGui.QMessageBox.about(self, "Erdos", texto % utils.Config.VERSION)

    def acerca_de_qt(self):
        QtGui.QMessageBox.aboutQt(self)


class Run(threading.Thread):

    def __init__(self):
        super(Run, self).__init__()
        self.start()

    def run(self):
        app = QtGui.QApplication(sys.argv)
        self.ex = Erdos()
        sys.exit(app.exec_())


if __name__ == '__main__':
    Run()