import os

from django import template

from .. import formato

register = template.Library()


@register.filter
def pesos(valor):
    return formato.pesos(valor)


@register.filter
def basename(ruta):
    """'inmuebles/documentos/escritura_ab12.pdf' -> 'escritura_ab12.pdf'"""
    return os.path.basename(str(ruta))
