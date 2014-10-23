import sys
import re
from StringIO import StringIO

from arbol import Arbol, Nodo

## Constantes

TAB = '    '


## Funciones

def nivelar(nivel, texto):
    texto = texto.replace('\n', '\n' + TAB * nivel)
    return "%s%s\n" % (TAB * nivel, texto)


## Clases

class Controlador(object):

    def __init__(self):
        super(Controlador, self).__init__()
        self.contenedor = ErdosBloquePrincipal()
        self.arbol = Arbol(self.contenedor)

    def agregar_sentencia(self, target, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosSentencia(destino, texto))

    def agregar_entrada(self, target, variable, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosEntrada(destino, variable, texto))

    def agregar_salida(self, target, variable, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosSalida(destino, variable, texto))

    def agregar_if(self, target, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosIf(destino, texto))

    def agregar_for(self, target, n_var, r_max, r_min):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosFor(destino, n_var, r_max, r_min))

    def agregar_while(self, target, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosWhile(destino, texto))

    def agregar_until(self, target, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosUntil(destino, texto))

    def agregar_case(self, target, texto):
        destino = target.get_contenedor()
        self.agregar_figura(destino, ErdosCase(destino, texto))

    def agregar_figura(self, destino, figura):
        destino.insertar(figura)


class ErdosBase(Nodo):

    def __init__(self, padre=None):
        super(ErdosBase, self).__init__()
        self.padre = padre

    def get_uid(self):
        return self.uid

    def get_contenedor(self):
        return self.padre.get_contenedor()

    def borrar(self):
        if self.padre:
            self.padre.hijos.remove(self)

    def gen_cod(self, nivel=0):
        return nivelar(nivel, ("id_ultimo = %s;" % self.uid) + self.texto)

    def ejecutar(self):
        self.codigo = """
from __future__ import division
import sys
from PyQt4 import QtGui

id_ultimo = 0
"""
        self.codigo += self.gen_cod()
        salida = StringIO()
        sys.stdout = salida

        fallo = 0
        self.locales = {}
        self.globales = {}
        try:
            exec(self.codigo, self.globales, self.locales)
        except SystemExit:
            print "salida forzada..."
        except Exception as inst:
            tipo = type(inst)
            if tipo is SyntaxError:
                print "Error de sintaxis."
                matcheo = re.match(
                    "(.+)id_ultimo = (\d+);(.+)", str(inst.args[1])
                )
                if matcheo:
                    fallo = int(matcheo.groups()[1])
            elif tipo is TypeError:
                print "Error de tipos."
            elif tipo is NameError:
                print "Error de nombres."
            elif tipo is IndexError:
                print "Error de indices."
            elif tipo is ZeroDivisionError:
                print "Error de division por cero."
            print inst.args
            if not fallo:
                fallo = self.locales.get('id_ultimo') or \
                    self.globales.get('id_ultimo')

        # restauramos el stdout original
        sys.stdout = sys.__stdout__

        # los hacemos None por la serializacion
        print self.locales
        print self.globales
        self.locales = None
        self.globales = None

        return salida, fallo


class ErdosRect(ErdosBase):

    def __init__(self, padre):
        super(ErdosRect, self).__init__(padre)

    def set_texto(self, texto):
        self.texto = texto or \
            self.__class__.__name__ + ":" + str(self.get_uid())


class ErdosSentencia(ErdosRect):

    def __init__(self, padre, texto):
        super(ErdosSentencia, self).__init__(padre)
        self.editar(texto)

    def editar(self, texto):
        self.set_texto(texto)


class ErdosEntrada(ErdosRect):

    def __init__(self, padre, variable, tipo_dato, texto_dialogo=None):
        super(ErdosEntrada, self).__init__(padre)
        self.editar(variable, tipo_dato, texto_dialogo)

    def editar(self, variable, tipo_dato, texto_dialogo=None):
        self.variable = variable
        self.tipo_dato = tipo_dato
        self.texto_dialogo = texto_dialogo or "Ingrese el valor de " + variable
        self.texto_dibujo = '%s <-- "%s"' % (variable, self.texto_dialogo)
        self.set_texto(self.texto_dibujo)

    def gen_cod(self, nivel=0):
        formato = """var, ok = QtGui.QInputDialog.getText(None, 'Erdos', '%s')
tipo_dato = '%s'
if tipo_dato == "Numerico":
    var = float(var)
elif tipo_dato == "Booleano":
    var = bool(var)
else:
    var = str(var)
%s = var;
if not ok:
    raise SystemExit"""

        return nivelar(nivel,
            formato % (
                self.texto_dialogo, self.tipo_dato, self.variable
            )
        )


class ErdosSalida(ErdosRect):

    FORMATO_PROMPT = "\nQtGui.QMessageBox.information(None, 'Erdos',"

    def __init__(self, padre, variable, texto_dialogo=None, prompt=False):
        super(ErdosSalida, self).__init__(padre)
        self.editar(variable, texto_dialogo, prompt)

    def editar(self, variable, texto_dialogo=None, prompt=False):
        self.variable = variable or None
        self.texto_dialogo = texto_dialogo or "Valor de %s:" % variable
        if self.variable:
            formato = '"%s" --> %s'
            valores = (self.texto_dialogo, self.variable)
        else:
            formato = '"%s" -->'
            valores = self.texto_dialogo
        self.texto_dibujo = formato % valores
        self.prompt = prompt
        self.set_texto(self.texto_dibujo)

    def gen_cod(self, nivel=0):
        if self.variable:
            formato = """id_ultimo = %s; print "%s", %s"""
            valores = self.uid, self.texto_dialogo, self.variable
            if self.prompt:
                valores.extend((self.texto_dialogo, self.variable))
                formato += self.FORMATO_PROMPT + """"%s " + str(%s))"""
        else:
            valores = self.uid, self.texto_dialogo
            formato = """id_ultimo = %s; print "%s" """
            if self.prompt:
                valores.append(self.texto_dialogo)
                formato += self.FORMATO_PROMPT + "'%s')"

        return nivelar(nivel, formato % tuple(valores))


class ErdosBloque(ErdosRect):

    def __init__(self, padre=None):
        super(ErdosBloque, self).__init__(padre)

    def get_contenedor(self):
        return self

    def gen_cod(self, nivel=0):
        codigo = ""
        if not self.hijos:
            codigo = nivelar(nivel + 1, "pass")
        for i in self.hijos:
            codigo += i.gen_cod(nivel + 1)
        return codigo


class ErdosBloquePrincipal(ErdosBloque):

    def __init__(self):
        super(ErdosBloquePrincipal, self).__init__(None)
        self.uid = 1

    def parentItem(self):  # no sirve mas?
        return self.item.parentItem()

    def get_uid(self):
        return 1

    def gen_cod(self):
        codigo = ""
        for i in self.hijos:
            codigo += i.gen_cod(0)
        return codigo


class ErdosIf(ErdosRect):

    def __init__(self, padre, condiciones):
        super(ErdosIf, self).__init__(padre)
        self.editar(condiciones)
        self.inicializar()

    def editar(self, condiciones):
        self.condiciones = condiciones
        self.set_texto(self.gen_texto())

    def gen_texto(self):
        return "Si (%s)" % self.condiciones.get_texto()

    def inicializar(self):
        self.lado_true = ErdosBloque(self)
        self.lado_false = ErdosBloque(self)
        self.agregar_hijo(self.lado_true)
        self.agregar_hijo(self.lado_false)

    def gen_cod(self, nivel=0):
        codigo = nivelar(nivel,
            "id_ultimo = %s\nif %s:" % (self.uid, self.condiciones.get_texto())
        )
        codigo += self.lado_true.gen_cod(nivel)
        codigo += nivelar(nivel, "else:")
        codigo += self.lado_false.gen_cod(nivel)
        return codigo


class ErdosBucle(ErdosRect):

    def __init__(self, padre):
        super(ErdosBucle, self).__init__(padre)
        self.bucle = ErdosBloque(self)
        self.agregar_hijo(self.bucle)


class ErdosFor(ErdosBucle):

    FORMATO_COD = "for %s in range(int(%s), int(%s)):"

    def __init__(self, padre, nom_var, r_max, r_min=1):
        super(ErdosFor, self).__init__(padre)
        self.editar(nom_var, r_max, r_min)

    def editar(self, nom_var, r_max, r_min):
        self.nom_var = nom_var
        self.rango_minimo = r_min
        self.rango_maximo = r_max
        self.set_texto(self.gen_text())

    def gen_text(self):
        return "Para %s <- de %s a %s hacer" % (
            self.nom_var, self.rango_minimo, self.rango_maximo
        )

    def gen_cod(self, nivel=0):
        codigo = nivelar(nivel, self.FORMATO_COD %
            (self.nom_var, self.rango_minimo, self.rango_maximo + " + 1")
        )
        codigo += self.bucle.gen_cod(nivel)
        return codigo


class ErdosWhile(ErdosBucle):

    def __init__(self, padre, condiciones):
        super(ErdosWhile, self).__init__(padre)
        self.editar(condiciones)

    def editar(self, condiciones):
        self.condiciones = condiciones
        self.set_texto(self.gen_texto())

    def gen_texto(self):
        return "Mientras (%s) hacer" % self.condiciones.get_texto()

    def gen_cod(self, nivel=0):
        condicion = self.condiciones.get_texto()
        codigo = nivelar(nivel,
            "id_ultimo = %s\nwhile %s:" % (self.uid, condicion)
        )
        codigo += self.bucle.gen_cod(nivel)
        return codigo


class ErdosUntil(ErdosWhile):

    def __init__(self, padre, condiciones):
        super(ErdosUntil, self).__init__(padre, condiciones)

    def gen_texto(self):
        return "Hasta que (%s) repetir" % self.condiciones.get_texto()

    def gen_cod(self, nivel=0):
        condicion = self.condiciones.get_texto()
        codigo = nivelar(nivel, "id_ultimo = %s\nwhile True:" % self.uid)
        codigo += self.bucle.gen_cod(nivel)
        codigo += nivelar(nivel + 1, "if %s: break" % condicion)
        return codigo


class ErdosCase(ErdosRect):

    def __init__(self, padre, nom_var, r_min, r_max):
        super(ErdosCase, self).__init__(padre)
        self.casos = {}
        self.editar(nom_var, r_min, r_max)

    def editar(self, nom_var, r_min, r_max):
        self.nom_var = nom_var
        self.rango_minimo = int(r_min)
        self.rango_maximo = int(r_max)
        self.set_texto(self.gen_texto())
        self.inicializar()
        self.default = ErdosBloque(self)

    def inicializar(self):
        for i in range(self.rango_minimo, self.rango_maximo + 1):
            cont = ErdosBloque(self)
            self.casos[i] = cont
            self.agregar_hijo(cont)

    def gen_texto(self):
        return "Si (%s) vale" % self.nom_var

    def gen_cod(self, nivel=0):
        codigo = ""
        primero = True
        for i in self.casos.keys():
            if primero:
                code = 'if'
                primero = False
            else:
                code = 'elif'
            codigo += nivelar(nivel, "%s %s == %s:" %
                (code, self.nom_var, i)
            )
            codigo += self.casos[i].gen_cod(nivel)
        codigo += nivelar(nivel, "else:")
        codigo += self.default.gen_cod(nivel)
        return codigo
