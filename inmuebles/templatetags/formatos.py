from django import template

from .. import formato

register = template.Library()


@register.filter
def pesos(valor):
    return formato.pesos(valor)
