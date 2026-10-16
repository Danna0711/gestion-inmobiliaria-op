from django import forms

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
