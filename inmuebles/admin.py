from django.contrib import admin
from .models import Propietario, Inmueble, Fotografia, Documento, Poliza

admin.site.register(Propietario)
admin.site.register(Inmueble)
admin.site.register(Fotografia)
admin.site.register(Documento)
admin.site.register(Poliza)