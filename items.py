from PyQt4 import QtCore, QtGui

import utils
from lib import *
from arbol import Arbol


class ControladorGUI(object):

    def __init__(self, vista):
        super(ControladorGUI, self).__init__()
        self.archivo = None
        self.historico = False
        self.historial = utils.Historial()
        self.vista = vista
        self.inicializar()

    def inicializar(self):
        self.nuevo_arbol()
        self.scene = ErdosScene(self.vista, self)
        self.vista.setScene(self.scene)
        self.guardar_historial()
        self.reposicionar()

    def nuevo_arbol(self):
        self.contenedorGUI = ErdosBloquePrincipalItem()
        self.arbol = Arbol(self.contenedorGUI.nodo)

    def eliminar_seleccionado(self):
        items = self.selectedItems()
        if items:
            item = items[0]
            if type(item) is not ErdosVacioItem:
                item.borrar()
                self.guardar_historial()
                self.reposicionar()

    def selectedItems(self):
        return self.scene.selectedItems()

    def get_contenedor(self):
        return self.contenedorGUI

    def centrar_vista(self):
        self.scene.setSceneRect(0, 0,
            self.contenedorGUI.get_largo(),
            self.contenedorGUI.get_alto()
        )

    def agregar_sentencia(self, pos, target, texto):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosSentenciaItem(destino, texto)
        )

    def agregar_entrada(self, pos, target, variable, tipo_dato, texto):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosEntradaItem(destino, variable, tipo_dato, texto)
        )

    def agregar_salida(self, pos, target, variable, texto, prompt):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosSalidaItem(destino, variable, texto, prompt)
        )

    def agregar_if(self, pos, target, condiciones):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosIfItem(destino, condiciones)
        )

    def agregar_for(self, pos, target, n_var, r_max, r_min):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosForItem(destino, n_var, r_max, r_min)
        )

    def agregar_while(self, pos, target, condiciones):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosWhileItem(destino, condiciones)
        )

    def agregar_until(self, pos, target, condiciones):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosUntilItem(destino, condiciones)
        )

    def agregar_case(self, pos, target, n_var, r_max, r_min):
        destino = target.get_contenedor()
        return self.agregar_figura(
            pos, target, ErdosCaseItem(destino, n_var, r_max, r_min)
        )

    def agregar_figura(self, pos, target, figura):
        destino = target.get_contenedor()
        destino.insertar(figura, pos, target)
        if not self.historico:
            self.guardar_historial()
        self.reposicionar()
        return figura

    def reposicionar(self):
        self.contenedorGUI.reposicionar()
        self.centrar_vista()

    def guardar(self):
        self.archivo = utils.guardar_objeto(self.arbol, self.archivo.path)

    def guardar_como(self, path):
        self.archivo = utils.guardar_objeto(self.arbol, path)
        return self.archivo.nombre

    def abrir(self, path):
        self.archivo = utils.cargar_objeto(path)
        alerta = self.archivo.version != utils.Config.VERSION
        nombre = self.archivo.nombre
        try:
            self.regenerar(self.archivo.arbol)
        except Exception as inst:
            nombre = "FALLO"
            print inst.args
        return nombre, alerta

    def exportar(self, path):
        vista = QtGui.QGraphicsView(self.scene)
        vista.setFixedSize(
            self.contenedorGUI.get_largo() + 10,
            self.contenedorGUI.get_alto() + 10
        )
        pixMap = QtGui.QPixmap.grabWidget(vista)
        pixMap.save(path)

    def ejecutar(self):
        self.quitar_resaltado()
        return self.contenedorGUI.nodo.ejecutar()

    def guardar_historial(self):
        self.historial.guardar(self.arbol)

    def deshacer(self):
        arbol = self.historial.deshacer()
        if arbol:
            self.regenerar(arbol, True)
            self.historico = False

    def rehacer(self):
        arbol = self.historial.rehacer()
        if arbol:
            self.regenerar(arbol, True)
            self.historico = False

    def quitar_resaltado(self):
        items = self.scene.items()
        for it in items:
            if hasattr(it, 'resaltado'):
                it.resaltado = False

    def resaltar_figura(self, uid):
        items = self.scene.items()
        figura = None
        for it in items:
            if hasattr(it, 'nodo'):
                if it.nodo.uid == uid:
                    figura = it
                    break
        if figura:
            figura.resaltar()

    def regenerar(self, arbol, historico=False):
        if historico:
            # si se regenera a partir de un historico
            # no tengo que volver a historiquear sobre si mismo (yo me entiendo)
            self.historico = True
        self.scene.limpiar()
        self.nuevo_arbol()
        self.scene.addItem(self.contenedorGUI)
        self.regen(arbol.raiz, self.contenedorGUI)

    def regen(self, nodo, destino):
        # esta funcion regenera todos los items graficos a partir de un arbol
        # de manera recursiva

        clase = nodo.__class__.__name__

        if clase == 'ErdosSentencia':
            self.agregar_sentencia(1, destino, nodo.texto)
        elif clase == 'ErdosEntrada':
            self.agregar_entrada(
                1, destino, nodo.variable, nodo.tipo_dato, nodo.texto_dialogo
            )
        elif clase == 'ErdosSalida':
            self.agregar_salida(
                1, destino, nodo.variable, nodo.texto_dialogo, nodo.prompt
            )
        elif clase == 'ErdosIf':
            figura = self.agregar_if(1, destino, nodo.condiciones)
            self.regen(nodo.hijos[0], figura.lado_true)
            self.regen(nodo.hijos[1], figura.lado_false)
        elif clase == 'ErdosFor':
            figura = self.agregar_for(
                1, destino, nodo.nom_var, nodo.rango_maximo, nodo.rango_minimo
            )
            self.regen(nodo.hijos[0], figura.bucle)
        elif clase == 'ErdosWhile':
            figura = self.agregar_while(1, destino, nodo.condiciones)
            self.regen(nodo.hijos[0], figura.bucle)
        elif clase == 'ErdosUntil':
            figura = self.agregar_until(1, destino, nodo.condiciones)
            self.regen(nodo.hijos[0], figura.bucle)
        elif clase == 'ErdosCase':
            figura = self.agregar_case(
                1, destino, nodo.nom_var, nodo.rango_minimo, nodo.rango_maximo
            )
            for i in nodo.casos.keys():
                self.regen(nodo.casos[i], figura.casos[i])
            self.regen(nodo.default, figura.default)
        elif clase == 'ErdosBloquePrincipal':
            for i in nodo.hijos:
                self.regen(i, destino)
        elif clase == 'ErdosBloque':
            for i in nodo.hijos:
                self.regen(i, destino)


class ErdosScene(QtGui.QGraphicsScene):

    def __init__(self, vista, controlador):
        super(ErdosScene, self).__init__(vista)
        self.vista = vista
        self.controlador = controlador
        self.limpiar()
        self.addItem(controlador.contenedorGUI)

    def limpiar(self):
        self.clear()


class ErdosBaseItem(QtGui.QGraphicsRectItem):

    def __init__(self, padre):
        super(ErdosBaseItem, self).__init__()
        self.set_padre(padre)

    def get_contenedor(self):
        return self.parentItem()

    def borrar(self):
        if hasattr(self, 'nodo'):
            self.nodo.borrar()
        self.padre.quitar(self)
        self.scene().removeItem(self)

    def set_padre(self, padre):
        self.padre = padre
        self.setParentItem(padre)


class ErdosRectItem(ErdosBaseItem):

    TXT_POS_X = 5
    TXT_POS_Y = 5
    COLOR = QtGui.QColor(255, 255, 255)
    COLOR_FOCO = QtGui.QColor(108, 160, 210)
    COLOR_RESALTADO = QtGui.QColor(255, 0, 0)

    def __init__(self, padre):
        super(ErdosRectItem, self).__init__(padre)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.resaltado = False
        self.txt = None

    def dibujar(self):
        self.setRect(QtCore.QRectF(0, 0, self.get_largo(), self.get_alto()))

    def editar(self, texto):
        # reimplementar en cada item usando su respectiva ventana de Input
        pass

    def get_size(self):
        r = self.rect()
        return r.width(), r.height()

    def get_alto(self):
        if self.txt:
            return self.txt.boundingRect().height() + 10
        return 50

    def get_largo(self):
        if self.txt:
            return self.txt.boundingRect().width() + 10
        return 50

    def get_txt_pos_x(self):
        return self.TXT_POS_X

    def get_txt_pos_y(self):
        return self.TXT_POS_Y

    def set_text(self, text):
        if self.txt:
            self.txt.scene().removeItem(self.txt)
        self.txt = QtGui.QGraphicsSimpleTextItem(text)
        self.txt.setParentItem(self)
        self.txt.setPos(self.get_txt_pos_x(), self.get_txt_pos_y())

    def get_text_size_raw(self):
        return self.txt.boundingRect()

    def get_text_size(self):
        ''' Devuelve largo y alto del texto contenido'''
        rect = self.txt.boundingRect()
        rect.adjust(0, 0, 10, 10)

        return rect

    def actualizar_largo(self, largo):
        self.setRect(QtCore.QRectF(0, 0, largo, self.get_alto()))
        self.centrar_texto()

    def centrar_texto(self):
        if self.txt:
            centro = self.rect().center() - self.get_text_size_raw().center()
            self.txt.setPos(centro)

    def paint(self, qpainter, option, widget):
        rect = self.rect()

        if self.isSelected():
            qpainter.fillRect(rect, self.COLOR_FOCO)
        elif self.resaltado:
            qpainter.fillRect(rect, self.COLOR_RESALTADO)
        else:
            qpainter.fillRect(rect, self.COLOR)

        self.paint_arreglos(qpainter, rect)

        QtGui.QGraphicsRectItem.paint(self, qpainter, option, widget)

    def paint_arreglos(self, qpainter, rect):
        # implementar donde sea necesario paintear cosas
        pass

    def get_items(self):
        return None

    def reposicionar(self, altura_inicial):
        if not type(self) == ErdosBloqueItem:
            self.setPos(self.pos().x(), altura_inicial)
        items = self.get_items()
        if items:
            max_largo = max(n.get_largo() for n in items)
            altura = 0
            for n in items:
                altura += n.reposicionar(altura)
                n.actualizar_largo(max_largo)
        return self.get_alto()

    def resaltar(self):
        self.resaltado = True


class ErdosSentenciaItem(ErdosRectItem):

    def __init__(self, padre, texto):
        super(ErdosSentenciaItem, self).__init__(padre)
        self.nodo = ErdosSentencia(padre.nodo, texto)
        self.set_text(self.nodo.texto)

    def editar(self, texto):
        self.nodo.editar(texto)
        self.set_text(texto)


class ErdosEntradaItem(ErdosRectItem):

    def __init__(self, padre, variable, tipo_dato, texto):
        super(ErdosEntradaItem, self).__init__(padre)
        self.nodo = ErdosEntrada(padre.nodo, variable, tipo_dato, texto)
        self.set_text(self.nodo.texto_dibujo)

    def editar(self, variable, tipo_dato, texto):
        self.nodo.editar(variable, tipo_dato, texto)
        self.set_text(self.nodo.texto_dibujo)


class ErdosSalidaItem(ErdosRectItem):

    def __init__(self, padre, variable, texto, prompt):
        super(ErdosSalidaItem, self).__init__(padre)
        self.nodo = ErdosSalida(padre.nodo, variable, texto, prompt)
        self.set_text(self.nodo.texto_dibujo)

    def editar(self, variable, texto, prompt):
        self.nodo.editar(variable, texto, prompt)
        self.set_text(self.nodo.texto_dibujo)


class ErdosBloqueItem(ErdosRectItem):
    ''' Siempre hay que pasarle su nodo correspondiente a la capa de datos'''

    def __init__(self, padre, nodo_bloque):
        super(ErdosBloqueItem, self).__init__(padre)

        if padre:
            self.nodo = nodo_bloque
        else:
            self.nodo = ErdosBloque()
        self.items = []
        self.vacio_fin()
        self.dibujar()

    def vacio_fin(self):
        self._vacio = ErdosVacioItem(self)

    def insertar(self, item, pos, target):
        if self._vacio:
            self._vacio.borrar()
            self._vacio = None
            index = 0
        else:
            if pos is utils.AL_FINAL \
                or type(target) is ErdosBloquePrincipalItem \
                or type(target) is ErdosBloqueItem:
                index = len(self.items)
            elif pos is utils.DEBAJO:
                index = self.items.index(target) + 1
            elif pos is utils.ENCIMA:
                index = self.items.index(target)

        self.items.insert(index, item)
        self.nodo.agregar_hijo(item.nodo, index)

    def quitar(self, item):
        if item in self.items:
            self.items.remove(item)
        if not self.items and not self._vacio:
            self.vacio_fin()

    def dibujar(self):
        if self.items:
            self.setRect(0, 0, self.get_largo(), self.get_alto())

    def get_alto(self):
        if self._vacio:
            return self._vacio.get_alto()
        return sum([i.get_alto() for i in self.items])

    def get_largo(self):
        if self._vacio:
            return self._vacio.get_largo()
        return max([i.get_largo() for i in self.items])

    def actualizar_alto(self, alto):
        ''' Estira el contenedor de manera de quedar de la misma altura
            que el de al lado.
        '''
        rect = self.rect()
        rect.setHeight(alto)
        self.setRect(rect)

    def actualizar_largo(self, largo):
        super(self.__class__, self).actualizar_largo(largo)
        if self._vacio:
            self._vacio.actualizar_largo(largo)
        for i in self.items:
            i.actualizar_largo(largo)

    def get_contenedor(self):
        return self

    def get_items(self):
        return self.items


class ErdosBloquePrincipalItem(ErdosBloqueItem):
    ''' No se dibuja. Se usa para mantener la logica que todo Item debe
    estar dentro de un contenedor.
    '''

    def __init__(self):
        super(ErdosBloquePrincipalItem, self).__init__(None, None)
        self.nodo = ErdosBloquePrincipal()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.dibujar()

    def parentItem(self):
        return self

    def reposicionar(self, altura_inicial=0):
        super(self.__class__, self).reposicionar(altura_inicial)


class ErdosVacioItem(ErdosRectItem):

    def __init__(self, padre):
        super(ErdosVacioItem, self).__init__(padre)
        self.set_text('.....')
        self.setRect(self.get_text_size())


class ErdosDecisionItem(ErdosRectItem):

    COLOR = QtGui.QColor(253, 125, 77)

    def __init__(self, padre):
        super(ErdosDecisionItem, self).__init__(padre)

    def paint_arreglos(self, qpainter, rect):
        # cuadrado
        qpainter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
        # divido a la mitad
        qpainter.drawLine(
            rect.x(), rect.y() + (rect.height() / 2),
            rect.x() + rect.width(), rect.y() + (rect.height() / 2)
        )
        # separadores
        self.paint_separadores(qpainter, rect)

    def dibujar(self):
        self.setRect(
            QtCore.QRectF(0, 0, self.get_largo(), self._get_alto_header())
        )

    def centrar_texto(self):
        if self.txt:
            rect = self.rect()
            rect.setHeight(self.rect().height() / 2)
            centro = rect.center() - self.get_text_size_raw().center()
            self.txt.setPos(centro)


class ErdosIfItem(ErdosDecisionItem):

    MARGEN_LBL_X = 5
    MARGEN_LBL_Y = 20

    def __init__(self, padre, condiciones):
        super(ErdosIfItem, self).__init__(padre)
        self.nodo = ErdosIf(self.padre.nodo, condiciones)
        self.set_text(self.nodo.texto)

        self.lado_true = ErdosBloqueItem(self, self.nodo.lado_true)
        self.lado_false = ErdosBloqueItem(self, self.nodo.lado_false)

        self.dibujar()
        self.dibujar_texto()
        self.posicionar()

    def posicionar(self):
        sw, sh = self.get_size()
        self.lado_true.setPos(0, sh)
        self.lado_false.setPos(sw / 2, sh)

    def dibujar_texto(self):
        r = self.rect()

        posY = r.height() - self.MARGEN_LBL_Y
        # letra V(erdadero)
        textV = QtGui.QGraphicsSimpleTextItem('V')
        textV.setParentItem(self)
        textV.setPos(self.MARGEN_LBL_X, posY)
        # letra F(also)
        self.textF = QtGui.QGraphicsSimpleTextItem('F')
        self.textF.setParentItem(self)
        self.textF.setPos(r.width() - self.MARGEN_LBL_X - 3, posY)

    def _get_alto_header(self):
        rect = self.get_text_size()
        return rect.height() * 2

    def get_alto(self):
        lt = self.lado_true.get_alto()
        lf = self.lado_false.get_alto()
        return self._get_alto_header() + max([lt, lf])

    def get_largo(self):
        largo_texto = self.get_text_size().width() + 10
        largo_bloques = self.lado_true.get_largo() + self.lado_false.get_largo()
        return max((largo_texto, largo_bloques))

    def actualizar_alto(self):
        alto = max((self.lado_true.get_alto(), self.lado_false.get_alto()))
        self.lado_true.actualizar_alto(alto)
        self.lado_false.actualizar_alto(alto)

    def actualizar_largo(self, largo):
        # ajustamos el largo del IF
        r = self.rect()
        r.setWidth(largo)
        self.setRect(r)

        # el largo del lado True siempre esta dado por si mismo
        self.lado_true.actualizar_largo(self.lado_true.get_largo())  # subclass?

        # reacomodamos el bloque False
        largo_lado_true = self.lado_true.get_largo()
        self.lado_false.setX(largo_lado_true)
        self.lado_false.actualizar_largo(largo - largo_lado_true)

        # reacomodamos la letra "F"
        self.textF.setX(r.width() - self.MARGEN_LBL_X - 3)

        self.actualizar_alto()

        self.centrar_texto()

    def paint_separadores(self, qpainter, rect):
        # dibujo el separador
        qpainter.drawLine(
            self.lado_true.get_largo(), rect.y() + (rect.height() / 2),
            self.lado_true.get_largo(), rect.y() + rect.height()
        )

    def get_items(self):
        return [self.lado_true, self.lado_false]

    def editar(self, condiciones):
        self.nodo.editar(condiciones)
        self.set_text(self.nodo.texto)


class ErdosCaseItem(ErdosDecisionItem):

    def __init__(self, padre, n_var, r_min, r_max):
        super(ErdosCaseItem, self).__init__(padre)
        self.nodo = ErdosCase(self.padre.nodo, n_var, r_min, r_max)
        self.casos = {}
        self.etiquetas = []

        for i in range(self.nodo.rango_minimo, self.nodo.rango_maximo + 1):
            self.casos[i] = ErdosBloqueItem(self, self.nodo.casos[i])
        # default
        self.default = ErdosBloqueItem(self, self.nodo.default)

        self.set_text(self.nodo.texto)
        self.dibujar_texto()
        self.dibujar()

    def posicionar(self):
        sw, sh = self.get_size()
        x = 0
        for i in range(self.nodo.rango_minimo, self.nodo.rango_maximo + 1):
            if i is not self.nodo.rango_minimo:
                x += self.casos[i - 1].get_largo()
            self.casos[i].setPos(x, sh)
        self.default.setPos(self.get_largo_cases(), sh)

    def get_largo(self):
        return self.get_largo_cases() + self.default.get_largo()

    def _get_alto_header(self):
        alto_titulo = self.get_text_size().height()
        alto_etiquetas = self.etiquetas[-1].boundingRect().height()
        return alto_titulo + alto_etiquetas

    def get_alto(self):
        return self._get_alto_header() + self.get_alto_cases()

    def get_alto_cases(self):
        altos = [i.get_alto() for i in self.casos.values() + [self.default]]
        return max(altos)

    def get_largo_cases(self):
        '''Devuelve la suma de los largos de cada uno de los cases
        (excepto el default)'''
        return sum([i.get_largo() for i in self.casos.values()])

    def actualizar_alto(self):
        alto = self.get_alto_cases()
        for i in self.casos.values():
            i.actualizar_alto(alto)
        self.default.actualizar_alto(alto)

    def actualizar_largo(self, largo):
        # ajustamos el largo del case
        r = self.rect()
        r.setWidth(largo)
        self.setRect(r)

        # el largo de los cases siempre esta dado por si mismo
        for i in self.casos.values():
            i.actualizar_largo(i.get_largo())
        self.posicionar()

        # reacomodamos el bloque Default
        largo_cases = self.get_largo_cases()
        self.default.setX(largo_cases)
        self.default.actualizar_largo(largo - largo_cases)

        # reacomodamos las etiquetas
        self.dibujar_texto()

        self.actualizar_alto()

        self.centrar_texto()

    def centrar_texto(self):
        if self.txt:
            rect = self.rect()
            rect.setHeight(self.rect().height() / 2)
            centro = rect.center() - self.get_text_size_raw().center()
            self.txt.setPos(centro)

    def dibujar_texto(self):
        for etq in self.etiquetas:
            etq.scene().removeItem(etq)
        self.etiquetas = []

        posx = 0
        for i in range(self.nodo.rango_minimo, self.nodo.rango_maximo + 1):
            self._dibujar_nro(str(i), posx)
            posx += self.casos[i].get_largo()
        self._dibujar_nro('otro', posx)

    def _dibujar_nro(self, texto, posx):
        r = self.rect()
        nro = QtGui.QGraphicsSimpleTextItem(texto)
        self.etiquetas.append(nro)
        nro.setParentItem(self)
        posy = r.height() - nro.boundingRect().height()
        nro.setPos(posx + 2, posy)

    def paint_separadores(self, qpainter, rect):
        # dibujo los separadores
        posx = 0
        for i in range(self.nodo.rango_minimo, self.nodo.rango_maximo + 1):
            posx += self.casos[i].get_largo()
            qpainter.drawLine(
                posx, rect.y() + (rect.height() / 2),
                posx, rect.y() + rect.height()
            )

    def get_items(self):
        return self.casos.values()  # <- OJO con el orden aca!

    def editar(self, nom_var, r_max, r_min):
        self.nodo.editar(nom_var, r_min, r_max)
        self.set_text(self.nodo.texto)

        for caso in self.casos.values():
            caso.scene().removeItem(caso)
        self.casos = {}
        # el default se conserva, el resto hay que volver a crearlos
        for i in range(self.nodo.rango_minimo, self.nodo.rango_maximo + 1):
            self.casos[i] = ErdosBloqueItem(self, self.nodo.casos[i])

        self.dibujar_texto()


class ErdosBucleItem(ErdosRectItem):
    '''
    Clase abstracta que siempre se hereda.
    No existen instancias puras de esta.
    '''

    MARGEN_BUCLE = 20
    COLOR = QtGui.QColor(53, 175, 120)

    def __init__(self, padre, nodo_bucle):
        super(ErdosBucleItem, self).__init__(padre)
        self.bucle = ErdosBloqueItem(self, nodo_bucle)
        self.inicializar()

    def inicializar(self):
        self.bucle.setPos(self.MARGEN_BUCLE, self.get_text_size().height())
        self.dibujar()

    def get_alto(self):
        alto_bloque = self.bucle.get_alto()
        alto_texto = self.get_text_size().height()

        return alto_bloque + alto_texto

    def get_largo(self):
        largo_texto = self.get_text_size().width()
        largo_bloque = self.bucle.get_largo()

        return max((largo_texto, largo_bloque)) + self.MARGEN_BUCLE

    def actualizar_largo(self, largo):
        # ajustamos el largo del FOR
        r = self.rect()
        r.setWidth(largo)
        self.setRect(r)

        # reacomodamos el largo del bucle
        self.bucle.actualizar_largo(largo - self.MARGEN_BUCLE)

        self.actualizar_alto()

    def actualizar_alto(self):
        alto = self.get_alto()
        rect = self.rect()
        rect.setHeight(alto)
        self.setRect(rect)

    def get_items(self):
        return [self.bucle]


class ErdosForItem(ErdosBucleItem):

    def __init__(self, padre, nom_var, r_max, r_min=1):
        self.nodo = ErdosFor(padre.nodo, nom_var, r_max, r_min)
        super(ErdosForItem, self).__init__(padre, self.nodo.bucle)

    def dibujar(self):
        self.setRect(
            QtCore.QRectF(0, 0, self.get_largo() + self.MARGEN_BUCLE,
                                self.get_alto())
        )

    def inicializar(self):
        self.set_text(self.nodo.texto)
        super(ErdosForItem, self).inicializar()

    def editar(self, nom_var, r_max, r_min):
        self.nodo.editar(nom_var, r_max, r_min)
        self.set_text(self.nodo.texto)


class ErdosWhileItem(ErdosBucleItem):

    def __init__(self, padre, condiciones):
        self.nodo = ErdosWhile(padre.nodo, condiciones)
        super(ErdosWhileItem, self).__init__(padre, self.nodo.bucle)

    def inicializar(self):
        self.set_text(self.nodo.texto)
        super(ErdosWhileItem, self).inicializar()

    def editar(self, condiciones):
        self.nodo.editar(condiciones)
        self.set_text(self.nodo.texto)


class ErdosUntilItem(ErdosBucleItem):

    def __init__(self, padre, condiciones):
        self.nodo = ErdosUntil(padre.nodo, condiciones)
        super(ErdosUntilItem, self).__init__(padre, self.nodo.bucle)

    def inicializar(self):
        self.set_text(self.nodo.texto)
        self.bucle.setPos(self.MARGEN_BUCLE, 0)
        self.dibujar()

    def get_txt_pos_y(self):
        return self.bucle.get_alto() + 5

    def actualizar_alto(self):
        super(self.__class__, self).actualizar_alto()
        super(self.__class__, self).set_text(self.nodo.texto)

    def editar(self, condiciones):
        self.nodo.editar(condiciones)
        self.set_text(self.nodo.texto)
