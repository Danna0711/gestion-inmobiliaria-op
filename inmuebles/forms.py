from django import forms

from .formato import ETIQUETAS
from .models import Documento, Inmueble, Poliza, Propietario


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
    empresa: KVA, altura y uso de suelo para bodegas y locales. La información
    adicional está disponible para todos los tipos.
    """

    # (titulo, campos, tipos en los que se muestra; None = siempre)
    AYUDAS = {
        "uso_suelo": "Actividad que se realiza en el inmueble.",
        "informacion_adicional": "Notas u observaciones del inmueble que no tengan un campo propio.",
    }

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
        ("Datos de bodega y local", ["kva", "altura", "uso_suelo"], ["bodega", "local"]),
        (
            "Valores",
            ["valor_transaccion", "valor_administracion", "margen_negociacion", "impuesto_predial"],
            None,
        ),
        ("Matrículas inmobiliarias", ["matricula_1", "matricula_2"], None),
        ("Información adicional", ["informacion_adicional"], None),
    ]

    class Meta:
        model = Inmueble
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()
        for nombre, ayuda in self.AYUDAS.items():
            if nombre in self.fields:
                self.fields[nombre].help_text = ayuda
        if "informacion_adicional" in self.fields:
            self.fields["informacion_adicional"].widget.attrs["rows"] = 5

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


# ------------------------------ DOCUMENTOS ------------------------------

TAMANO_MAXIMO_DOCUMENTO = 15 * 1024 * 1024  # 15 MB por documento
EXTENSIONES_DOCUMENTO = ("pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png")


class MultipleDocumentField(forms.FileField):
    """Campo que acepta varios documentos (PDF, Word, Excel o imagen) en una sola subida."""

    def __init__(self, *args, **kwargs):
        accept = ",".join("." + e for e in EXTENSIONES_DOCUMENTO)
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": accept}))
        kwargs.setdefault("error_messages", {"required": "Selecciona al menos un documento."})
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
            extension = archivo.name.rsplit(".", 1)[-1].lower() if "." in archivo.name else ""
            if extension not in EXTENSIONES_DOCUMENTO:
                raise forms.ValidationError(
                    f"«{archivo.name}» no es un formato permitido (usa PDF, Word, Excel, JPG o PNG)."
                )
            if archivo.size > TAMANO_MAXIMO_DOCUMENTO:
                raise forms.ValidationError(
                    f"El documento «{archivo.name}» supera el tamaño máximo de 15 MB."
                )
        return resultado


class DocumentoSubirForm(forms.Form):
    tipo_documento = forms.ChoiceField(
        label="Tipo de documento",
        choices=Documento.TIPO_DOCUMENTO_CHOICES,
        error_messages={"required": "Selecciona el tipo de documento."},
    )
    archivos = MultipleDocumentField(label="Documentos")


# ------------------------------- PÓLIZAS -------------------------------

class PolizaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Poliza
        exclude = ["inmueble"]
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "archivo": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()
        self.fields["archivo"].label = "Documento de la póliza (opcional)"
        self.fields["archivo"].help_text = "PDF, Word, Excel, JPG o PNG, hasta 15 MB."

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        # Si no se subió uno nuevo (o se marcó "borrar"), no hay nada que validar
        if not archivo or not hasattr(archivo, "size") or not hasattr(archivo, "content_type"):
            return archivo
        extension = archivo.name.rsplit(".", 1)[-1].lower() if "." in archivo.name else ""
        if extension not in EXTENSIONES_DOCUMENTO:
            raise forms.ValidationError(
                f"«{archivo.name}» no es un formato permitido (usa PDF, Word, Excel, JPG o PNG)."
            )
        if archivo.size > TAMANO_MAXIMO_DOCUMENTO:
            raise forms.ValidationError(
                f"El documento «{archivo.name}» supera el tamaño máximo de 15 MB."
            )
        return archivo

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor < 0:
            raise forms.ValidationError("El valor de la póliza no puede ser negativo.")
        return valor


# --------------------------- BÚSQUEDA Y FILTROS ---------------------------

def _a_entero(texto):
    """'$ 300.000.000' -> 300000000. Acepta puntos, comas, espacios y el signo $."""
    limpio = texto.replace("$", "").replace(".", "").replace(",", "").replace(" ", "")
    if not limpio.isdigit():
        raise forms.ValidationError("Escribe solo números, por ejemplo 300.000.000.")
    return int(limpio)


class BusquedaInmuebleForm(forms.Form):
    """Filtros del listado de inmuebles (RF14). Todos son opcionales y se combinan entre sí."""

    ORDEN_CHOICES = [
        ("", "Más recientes primero"),
        ("precio_asc", "Precio: menor a mayor"),
        ("precio_desc", "Precio: mayor a menor"),
        ("habitaciones_desc", "Más habitaciones primero"),
    ]

    q = forms.CharField(required=False, label="Buscar")
    tipo = forms.ChoiceField(required=False, label="Tipo",
                             choices=[("", "Todos los tipos")] + Inmueble.TIPO_INMUEBLE_CHOICES)
    estado = forms.ChoiceField(required=False, label="Estado",
                               choices=[("", "Todos los estados")] + Inmueble.ESTADO_CHOICES)
    ciudad = forms.ChoiceField(required=False, label="Ciudad")
    barrio = forms.CharField(required=False, label="Barrio", max_length=100)
    precio_min = forms.CharField(required=False, label="Precio desde")
    precio_max = forms.CharField(required=False, label="Precio hasta")
    habitaciones_min = forms.IntegerField(required=False, label="Habitaciones (mínimo)", min_value=0,
                                          error_messages={"min_value": "Las habitaciones no pueden ser negativas.",
                                                          "invalid": "Escribe un número entero de habitaciones."})
    orden = forms.ChoiceField(required=False, label="Ordenar por", choices=ORDEN_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ciudades = (
            Inmueble.objects.order_by("ciudad").values_list("ciudad", flat=True).distinct()
        )
        self.fields["ciudad"].choices = [("", "Todas las ciudades")] + [(c, c) for c in ciudades]
        self.fields["q"].widget.attrs["placeholder"] = (
            "Buscar por dirección, ciudad, barrio, conjunto, propietario o ID de captación"
        )
        self.fields["precio_min"].widget.attrs["placeholder"] = "Ej.: 200.000.000"
        self.fields["precio_max"].widget.attrs["placeholder"] = "Ej.: 500.000.000"
        for nombre, campo in self.fields.items():
            campo.widget.attrs["class"] = (
                "form-select" if isinstance(campo.widget, forms.Select) else "form-control"
            )

    def clean_precio_min(self):
        texto = self.cleaned_data.get("precio_min", "").strip()
        return _a_entero(texto) if texto else None

    def clean_precio_max(self):
        texto = self.cleaned_data.get("precio_max", "").strip()
        return _a_entero(texto) if texto else None

    def clean(self):
        datos = super().clean()
        minimo, maximo = datos.get("precio_min"), datos.get("precio_max")
        if minimo is not None and maximo is not None and minimo > maximo:
            self.add_error("precio_max", "El precio hasta debe ser mayor o igual al precio desde.")
        return datos

    # campos que se muestran en el panel de filtros avanzados
    AVANZADOS = ("ciudad", "barrio", "precio_min", "precio_max", "habitaciones_min", "orden")

    def hay_avanzados(self):
        return any(self.data.get(n) for n in self.AVANZADOS)
