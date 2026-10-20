from django import forms

from .formato import ETIQUETAS
from .models import Inmueble, Propietario


class BootstrapFormMixin:
    """Aplica las clases de Bootstrap 5 a todos los campos del formulario."""

    def aplicar_estilos(self):
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"
            if isinstance(widget, forms.Textarea):
                widget.attrs["rows"] = 2
        for nombre, etiqueta in ETIQUETAS.items():
            if nombre in self.fields:
                self.fields[nombre].label = etiqueta


class PropietarioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Propietario
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()


class InmuebleForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario general del inmueble (una sola ficha para todos los tipos).
    Los campos se agrupan en secciones; algunas secciones solo se muestran
    para ciertos tipos de inmueble (ver 'tipos'), tal como lo definió la
    empresa: KVA y altura para bodegas y locales, uso de suelo solo para bodegas.
    """

    # (titulo, campos, tipos en los que se muestra; None = siempre)
    SECCIONES = [
        ("Captación", ["propietario", "id_captacion", "nombre_agente", "estado"], None),
        ("Ubicación", ["ciudad", "departamento", "barrio", "direccion", "nombre_conjunto"], None),
        (
            "Características generales",
            [
                "tipo_inmueble", "estrato", "piso", "anos_construccion", "remodelado",
                "area_construida", "area_privada", "habitaciones", "banos",
                "garajes", "depositos",
            ],
            None,
        ),
        ("Servicios", ["servicio_agua", "servicio_luz", "servicio_gas"], None),
        (
            "Zonas comunes del conjunto",
            [
                "aptos_por_piso", "total_unidades", "no_pisos", "ascensores",
                "vigilancia", "parqueadero_visitantes", "areas_comunes", "club_house",
            ],
            ["casa", "apartamento", "local", "otro"],
        ),
        ("Datos de bodega y local", ["kva", "altura"], ["bodega", "local"]),
        ("Datos de bodega", ["uso_suelo"], ["bodega"]),
        (
            "Valores",
            ["valor_transaccion", "valor_administracion", "margen_negociacion", "impuesto_predial"],
            None,
        ),
        ("Matrículas inmobiliarias", ["matricula_1", "matricula_2"], None),
    ]

    class Meta:
        model = Inmueble
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()

    def secciones(self):
        """Devuelve las secciones con sus campos ya enlazados al formulario."""
        usados = set()
        resultado = []
        for titulo, nombres, tipos in self.SECCIONES:
            campos = [self[n] for n in nombres if n in self.fields]
            usados.update(n for n in nombres if n in self.fields)
            if campos:
                resultado.append(
                    {"titulo": titulo, "campos": campos, "tipos": ",".join(tipos) if tipos else ""}
                )
        restantes = [self[n] for n in self.fields if n not in usados]
        if restantes:
            resultado.append({"titulo": "Otros datos", "campos": restantes, "tipos": ""})
        return resultado


# ----------------------------- FOTOGRAFÍAS -----------------------------

TAMANO_MAXIMO_FOTO = 8 * 1024 * 1024  # 8 MB por fotografía


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Campo que acepta varias imágenes en una sola subida."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*"}))
        kwargs.setdefault(
            "error_messages",
            {
                "invalid_image": "Uno de los archivos no es una imagen válida (usa JPG, PNG o WEBP).",
                "required": "Selecciona al menos una fotografía.",
            },
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpiar_uno = super().clean
        if isinstance(data, (list, tuple)):
            resultado = [limpiar_uno(d, initial) for d in data if d]
        else:
            resultado = [limpiar_uno(data, initial)] if data else []
        if not resultado:
            raise forms.ValidationError(self.error_messages["required"], code="required")
        for archivo in resultado:
            if archivo.size > TAMANO_MAXIMO_FOTO:
                raise forms.ValidationError(
                    f"La fotografía «{archivo.name}» supera el tamaño máximo de 8 MB."
                )
        return resultado


class FotografiaSubirForm(forms.Form):
    archivos = MultipleImageField(label="Fotografías")
    etiqueta = forms.CharField(label="Etiqueta (opcional)", max_length=50, required=False)
