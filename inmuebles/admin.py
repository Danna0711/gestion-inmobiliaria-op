"""Panel de administración de OP Agente Inmobiliario.

El día a día se trabaja en el sistema (listado de inmuebles, propietarios y pólizas).
Este panel queda para tareas internas: crear usuarios de los asesores, cambiar
contraseñas y revisar o corregir registros puntuales.
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html


def _pesos(valor):
    """Valor en pesos sin que se parta en dos líneas."""
    return format_html('<span style="white-space:nowrap">{}</span>', formato.pesos(valor))

from . import formato
from .models import Documento, Fotografia, Inmueble, OfertaComercial, Poliza, Propietario

# ------------------------------ Identidad del panel ------------------------------
admin.site.site_header = "OP Agente Inmobiliario"
admin.site.site_title = "Administración · OP Agente Inmobiliario"
admin.site.index_title = "Panel de administración"
admin.site.site_url = "/"

# Los grupos de permisos no se usan en este sistema: se ocultan para simplificar el panel.
admin.site.unregister(Group)


# --------------------------------- Propietarios ---------------------------------

class InmuebleDelPropietarioInline(admin.TabularInline):
    model = Inmueble
    fields = ("tipo_inmueble", "direccion", "ciudad", "estado")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = "Inmuebles de este propietario"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "numero_identificacion", "numero_contacto", "correo", "cantidad_inmuebles")
    search_fields = ("nombre_completo", "numero_identificacion", "correo")
    inlines = [InmuebleDelPropietarioInline]
    list_per_page = 25

    @admin.display(description="Inmuebles")
    def cantidad_inmuebles(self, obj):
        return obj.inmuebles.count()


# ---------------------------------- Inmuebles ----------------------------------

class OfertaInline(admin.StackedInline):
    model = OfertaComercial
    extra = 0
    min_num = 1
    fields = (("titulo", "modalidad"), ("area", "valor", "aplica_iva", "valor_administracion"), "descripcion", "ventajas")


class FotografiaInline(admin.TabularInline):
    model = Fotografia
    extra = 0
    fields = ("vista_previa", "archivo", "etiqueta")
    readonly_fields = ("vista_previa",)

    @admin.display(description="Vista previa")
    def vista_previa(self, obj):
        if obj.pk and obj.archivo:
            return format_html('<img src="{}" style="height:60px;border-radius:4px">', obj.archivo.url)
        return "—"


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    fields = ("tipo_documento", "archivo")


class PolizaInline(admin.TabularInline):
    model = Poliza
    extra = 0
    fields = ("nombre_poliza", "numero_contrato", "valor", "fecha_vencimiento", "archivo")


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "ciudad", "barrio", "propietario", "valor_en_pesos", "estado", "fecha_captacion", "ver_en_sistema")
    list_filter = ("tipo_inmueble", "estado", "ciudad")
    search_fields = ("direccion", "ciudad", "barrio", "nombre_conjunto", "id_captacion", "propietario__nombre_completo")
    autocomplete_fields = ("propietario",)
    list_select_related = ("propietario",)
    date_hierarchy = "fecha_captacion"
    list_per_page = 25
    readonly_fields = ("fecha_captacion", "valor_principal", "administracion_principal")
    inlines = [OfertaInline, FotografiaInline, DocumentoInline, PolizaInline]
    fieldsets = (
        ("Captación", {"fields": ("propietario", ("id_captacion", "nombre_agente"), ("estado", "fecha_captacion"))}),
        ("Ubicación", {"fields": (("ciudad", "departamento"), ("barrio", "direccion"), "nombre_conjunto")}),
        ("Características generales", {"fields": (
            "tipo_inmueble", ("estrato", "piso", "anos_construccion", "remodelado"),
            ("area_construida", "area_privada"), ("habitaciones", "banos", "garajes", "depositos"),
            ("servicio_agua", "servicio_luz", "servicio_gas"),
        )}),
        ("Zonas comunes del conjunto", {"classes": ("collapse",), "fields": (
            ("aptos_por_piso", "total_unidades", "no_pisos"), ("ascensores", "club_house"),
            ("vigilancia", "parqueadero_visitantes"), "areas_comunes",
        )}),
        ("Datos de bodega y local", {"classes": ("collapse",), "fields": (
            ("kva", "altura", "uso_suelo"), ("area_libre", "area_administrativa"),
            ("capacidad_piso", "muelles", "entradas_nivel"),
        )}),
        ("Valores", {"description": "El valor y la administración se toman de la primera oferta comercial.",
                     "fields": (("valor_principal", "administracion_principal"), ("margen_negociacion", "impuesto_predial"))}),
        ("Matrículas inmobiliarias", {"fields": (("matricula_1", "matricula_2"),)}),
        ("Información adicional", {"fields": ("informacion_adicional",)}),
    )

    @admin.display(description="Valor", ordering="valor_transaccion")
    def valor_en_pesos(self, obj):
        return _pesos(obj.valor_transaccion)

    @admin.display(description="Valor (primera oferta)")
    def valor_principal(self, obj):
        return _pesos(obj.valor_transaccion) if obj.pk else "—"

    @admin.display(description="Administración (primera oferta)")
    def administracion_principal(self, obj):
        return _pesos(obj.valor_administracion) if obj.pk and obj.valor_administracion else "—"

    @admin.display(description="")
    def ver_en_sistema(self, obj):
        return format_html('<a href="{}" style="white-space:nowrap">Ver ficha</a>', reverse("inmueble_detail", args=[obj.pk]))

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Mantiene el valor principal igual al de la primera oferta, como en el sistema
        primera = form.instance.ofertas.order_by("id").first()
        if primera:
            Inmueble.objects.filter(pk=form.instance.pk).update(
                valor_transaccion=primera.valor, valor_administracion=primera.valor_administracion
            )

    def save_model(self, request, obj, form, change):
        if obj.valor_transaccion is None:
            obj.valor_transaccion = 0
        super().save_model(request, obj, form, change)


# ------------------------------- Pólizas y ofertas -------------------------------

@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ("nombre_poliza", "inmueble", "numero_contrato", "valor_en_pesos", "fecha_vencimiento", "estado")
    search_fields = ("nombre_poliza", "numero_contrato", "inmueble__direccion")
    list_select_related = ("inmueble",)
    autocomplete_fields = ("inmueble",)
    date_hierarchy = "fecha_vencimiento"

    @admin.display(description="Valor", ordering="valor")
    def valor_en_pesos(self, obj):
        return _pesos(obj.valor)

    @admin.display(description="Estado")
    def estado(self, obj):
        clave, _, texto = formato.estado_poliza(obj.fecha_vencimiento, timezone.localdate())
        color = {"vencida": "#b42318", "por_vencer": "#b54708", "vigente": "#067647"}[clave]
        return format_html('<strong style="color:{}">{}</strong>', color, texto)


@admin.register(OfertaComercial)
class OfertaComercialAdmin(admin.ModelAdmin):
    list_display = ("__str__", "modalidad", "valor_en_pesos", "aplica_iva", "inmueble")
    list_filter = ("modalidad", "aplica_iva")
    search_fields = ("titulo", "inmueble__direccion")
    list_select_related = ("inmueble",)
    autocomplete_fields = ("inmueble",)

    @admin.display(description="Valor", ordering="valor")
    def valor_en_pesos(self, obj):
        return _pesos(obj.valor)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("tipo_documento", "inmueble", "archivo")
    list_filter = ("tipo_documento",)
    search_fields = ("inmueble__direccion",)
    list_select_related = ("inmueble",)
    autocomplete_fields = ("inmueble",)


@admin.register(Fotografia)
class FotografiaAdmin(admin.ModelAdmin):
    list_display = ("vista_previa", "etiqueta", "inmueble")
    search_fields = ("etiqueta", "inmueble__direccion")
    list_select_related = ("inmueble",)
    autocomplete_fields = ("inmueble",)

    @admin.display(description="Vista previa")
    def vista_previa(self, obj):
        return format_html('<img src="{}" style="height:48px;border-radius:4px">', obj.archivo.url) if obj.archivo else "—"
