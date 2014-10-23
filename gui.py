import datetime
from functools import partial

from PyQt4 import QtGui, QtCore, uic

import utils


def validar_variable(var):
    # valida que var cumpla el formato de una variable
    # Aclaracion: no se checkea que sea alfanumerico para no perder
    # el soporte a arrays y objetos
    try:
        str(var)
    except UnicodeEncodeError:
        return False
    except Exception as exp:
        raise exp
    if str(var)[0].isalpha():
        return True
    return False


def dialogo(padre, filemode, namefilter, titulo, modo_aceptar=0):
    dialogo = QtGui.QFileDialog(padre, titulo)
    dialogo.setFileMode(filemode)
    dialogo.setNameFilter(namefilter)
    dialogo.setViewMode(QtGui.QFileDialog.Detail)
    dialogo.setAcceptMode(modo_aceptar)
    return dialogo


def dialogo_guardar(padre):
    return dialogo(
        padre, QtGui.QFileDialog.AnyFile, "Erdos (*.erd)", "Guardar como...", 1
    )


def dialogo_exportar(padre):
    return dialogo(
        padre, QtGui.QFileDialog.AnyFile, "Archivo PNG (*.png)", "Exportar", 1
    )


def dialogo_abrir(padre):
    return dialogo(
        padre, QtGui.QFileDialog.ExistingFile, "Erdos (*.erd)", "Abrir"
    )


class VentanaEjecuccion(QtGui.QDialog):

    def __init__(self, padre):
        super(VentanaEjecuccion, self).__init__(padre)
        uic.loadUi(utils.path_ui("salida_ejecuccion.ui"), self)
        self.btnCerrar.connect(
            self.btnCerrar, QtCore.SIGNAL("clicked()"), self.cerrar
        )
        self.btnLimpiar.connect(
            self.btnLimpiar, QtCore.SIGNAL("clicked()"), self.limpiar
        )

    def agregar_salida(self, nombre_diag, salida):
        stamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        separador = "==== Ejecutando: %s (%s) ====" % (nombre_diag, stamp)
        self.textEdit.append(separador)
        self.textEdit.append(salida)
        self.textEdit.append("")

    def limpiar(self):
        self.textEdit.clear()

    def cerrar(self):
        self.close()


class VentanaModal(QtGui.QDialog):

    def __init__(self, padre, archivo_ui):
        super(VentanaModal, self).__init__(padre)
        uic.loadUi(archivo_ui, self)
        self.res = 0

    def done(self, r):
        if r == QtGui.QDialog.Accepted:
            if self.validar():
                self.aceptar()
                QtGui.QDialog.done(self, r)  # super() aca no anda :-/
                return
            else:
                self.error()
                return
        else:
            QtGui.QDialog.done(self, r)
            return

    def error(self):
        msg = "Valores invalidos. Por favor revise el manual de usuario."
        QtGui.QMessageBox.warning(
            self, "Error", msg
        )

    def aceptar(self):
        self.res = self.ubicacion()

    def ubicacion(self):
        if self.radioButton.isChecked():
            return utils.AL_FINAL
        elif self.radioButton_2.isChecked():
            return utils.DEBAJO
        else:
            return utils.ENCIMA

    def validar(self):
        # implementar en cada clase
        pass


class SentenciaInput(VentanaModal):

    def __init__(self, padre, sent_text=None):
        super(SentenciaInput, self).__init__(
            padre, utils.path_ui("input_sentencia.ui")
        )
        if sent_text:
            self.sentencia_text.setText(sent_text)
        self.exec_()

    def validar(self):
        sent = self.sentencia_text.text()
        if sent:
            return validar_variable(sent)
        return False

    def get(self):
        return self.res, self.sentencia_text.text()


class IfInput(VentanaModal):

    def __init__(self, padre, condiciones=None):
        super(self.__class__, self).__init__(
            padre, utils.path_ui("input_cond.ui")
        )
        self.condiciones = Condiciones(self, condiciones)
        self.exec_()

    def aceptar(self):
        self.condiciones.procesar()
        super(self.__class__, self).aceptar()

    def get(self):
        return self.res, self.condiciones

    def validar(self):
        return self.condiciones.validar()


class Condiciones(object):

    def __init__(self, ventana, condiciones=None):
        self.condiciones = []
        self.pos = 1
        self.ventana = ventana
        if condiciones:
            primero = True
            for cond in condiciones.condiciones:
                self.agregar(primero, cond)
                primero = False
        else:
            self.agregar(True)

    def agregar(self, primero=False, valores=None):
        if primero:
            callback = self.agregar
        else:
            callback = self.quitar
        if valores:
            cond = Condicion(
                callback, primero, self.ventana.grilla, self.pos, *valores
            )
        else:
            cond = Condicion(callback, primero, self.ventana.grilla, self.pos)
        self.condiciones.append(cond)
        self.pos += 1

    def quitar(self, condicion):
        self.condiciones.remove(condicion)
        condicion.borrarse()
        self.ventana.adjustSize()  # no me pregunten porque pero si no lo
        self.ventana.adjustSize()  # llamo 2 veces no se achica la 1era vez

    def procesar(self):
        for c in self.condiciones:
            c.almacenar_texto()
        self.condiciones = [c.get() for c in self.condiciones]
        self.ventana = None

    def get_texto(self):
        texto = ""
        for cond in self.condiciones:
            formato = "%s %s %s"
            valores = cond[0:3]
            if cond[3] != '--':
                formato += " %s "
                valores = cond
            texto += formato % valores
        return texto

    def validar(self):
        for i in self.condiciones[:-1]:
            if not i.validar() or not i.conectado():
                return False
        ultimo = self.condiciones[-1]
        if not ultimo.validar() or ultimo.conectado():
            return False
        return True


class Condicion(object):

    TIPOS_CONDICIONES = ['==', '!=', '<=', '>=', '<', '>']
    TIPOS_CONECTORES = ['--', 'and', 'or']

    def __init__(self, callback, primero, grilla, posicion,
        var=None, cond=None, valor=None, conector=None):
        super(self.__class__, self).__init__()

        self.grilla = grilla
        self.posicion = posicion
        self.callback = callback
        self.construir(primero, var, cond, valor, conector)

    def construir(self, primero, var, cond, valor, conector):
        self.variable = QtGui.QLineEdit()
        self.grilla.addWidget(self.variable, self.posicion, 0)
        if primero:
            self.variable.setFocus()
        if var:
            self.variable.setText(var)

        self.condicion = QtGui.QComboBox()
        self.grilla.addWidget(self.condicion, self.posicion, 1)
        self.condicion.insertItems(0, self.TIPOS_CONDICIONES)
        if cond:
            index = self.TIPOS_CONDICIONES.index(cond)
            self.condicion.setCurrentIndex(index)

        self.valor = QtGui.QLineEdit()
        self.grilla.addWidget(self.valor, self.posicion, 2)
        if valor:
            self.valor.setText(valor)

        self.conector = QtGui.QComboBox()
        self.grilla.addWidget(self.conector, self.posicion, 3)
        self.conector.insertItems(0, self.TIPOS_CONECTORES)
        if conector:
            index = self.TIPOS_CONECTORES.index(conector)
            self.conector.setCurrentIndex(index)

        if primero:
            texto = '+'
        else:
            texto = '-'
            self.callback = partial(self.callback, self)
        self.accion = QtGui.QPushButton(texto)
        self.grilla.addWidget(self.accion, self.posicion, 4)
        self.accion.connect(
            self.accion, QtCore.SIGNAL("clicked()"), self.callback
        )

    def borrarse(self):
        for item in [self.variable, self.condicion, self.valor, self.conector,
            self.accion]:
            self.grilla.removeWidget(item)
            item.deleteLater()
            del item

    def almacenar_texto(self):
        # Los valores de los textos se guardan aca porque
        # si se cierra el dialog, ya no se puede acceder (cosas de Qt...)
        self.variable_text = self.variable.text()
        self.condicion_text = self.condicion.currentText()
        self.valor_text = self.valor.text()
        self.conector_text = self.conector.currentText()

    def get(self):
        return (self.variable_text, self.condicion_text, self.valor_text,
            self.conector_text)

    def validar(self):
        var = str(self.variable.text())
        val = str(self.valor.text())
        if var and val:
            if validar_variable(var):
                return True
        return False

    def conectado(self):
        conector = str(self.conector.currentText())
        if conector != '--':
            return True
        return False


class ForInput(VentanaModal):

    def __init__(self, padre, case=False, n_var=None, r_min=None, r_max=None):
        super(self.__class__, self).__init__(
            padre, utils.path_ui("input_for.ui")
        )
        self.case = case
        if self.case:
            self.lbl_var.setText("Variable de decision")
        if n_var:
            self.n_var.setText(str(n_var))
        if r_min:
            self.r_min.setText(str(r_min))
        if r_max:
            self.r_max.setText(str(r_max))
        self.exec_()

    def validar(self):
        var = str(self.n_var.text())
        r_max = str(self.r_max.text())
        r_min = str(self.r_min.text())

        if not var or not r_max or not r_min:
            return False
        if not validar_variable(var):
            return False
        if self.case:
            if not r_max.isdigit() or not r_min.isdigit():
                return False
            if not int(r_max) > int(r_min):
                return False
        else:
            if r_max.isdigit() and r_min.isdigit():
                if not int(r_max) > int(r_min):
                    return False
        return True

    def get(self):
        r_max = self.r_max.text()
        r_min = self.r_min.text()
        return self.res, self.n_var.text(), r_max, r_min


class ESInput(VentanaModal):

    def __init__(self, padre, archivo_ui, variable, texto, prompt):
        super(ESInput, self).__init__(padre, utils.path_ui(archivo_ui))
        if variable:
            self.variable_text.setText(variable)
        if texto:
            self.texto_text.setText(texto)
        self.variable_text.setFocus()

    def validar(self):
        var = self.variable_text.text()
        texto = self.texto_text.text()
        if var:
            if not validar_variable(var):
                return False
        if var or texto:
            return True
        return False

    def get(self):
        return self.res, self.variable_text.text(), self.texto_text.text()


class EntradaInput(ESInput):

    TIPOS = ["Texto", "Numerico", "Booleano"]

    def __init__(self, padre, variable=None, texto=None, tipo_dato=None):
        super(self.__class__, self).__init__(
            padre, "input_entrada.ui", variable, texto, False
        )
        for tipo in self.TIPOS:
            self.comboBox.addItem(tipo)
        if tipo_dato:
            self.comboBox.setCurrentIndex(self.TIPOS.index(tipo_dato))
        self.exec_()

    def validar(self):
        if not self.variable_text.text():
            return False
        return super(self.__class__, self).validar()

    def get(self):
        return self.res, self.variable_text.text(), \
            self.comboBox.currentText(), self.texto_text.text()


class SalidaInput(ESInput):

    def __init__(self, padre, variable=None, texto=None, prompt=False):
        super(self.__class__, self).__init__(
            padre, "input_salida.ui", variable, texto, prompt
        )
        self.prompt = prompt
        if prompt:
            self.checkBox.setCheckState(2)
        self.exec_()

    def get(self):
        return super(self.__class__, self).get() + (self.checkBox.isChecked(),)
