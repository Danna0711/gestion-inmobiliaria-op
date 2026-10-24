from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from . import ficha, formato
from .forms import (
    BusquedaInmuebleForm, DocumentoSubirForm, FotografiaSubirForm, InmuebleForm, OfertaFormSet,
    PolizaForm, PropietarioForm,
)
from .models import Documento, Fotografia, Inmueble, OfertaComercial, Poliza, Propietario


def polizas_en_alerta():
    """Pólizas vencidas o que vencen en los próximos días (ver formato.DIAS_AVISO_POLIZA)."""
    limite = timezone.localdate() + timedelta(days=formato.DIAS_AVISO_POLIZA)
    return Poliza.objects.filter(fecha_vencimiento__lte=limite)


# ----------------------------- INMUEBLES -----------------------------

class InmuebleListView(LoginRequiredMixin, ListView):
    """Listado con búsqueda y filtros combinados (RF14)."""

    model = Inmueble
    template_name = "inmuebles/inmueble_list.html"
    context_object_name = "inmuebles"
    paginate_by = 15

    ORDENES = {
        "": ["-id"],
        "precio_asc": ["valor_transaccion", "-id"],
        "precio_desc": ["-valor_transaccion", "-id"],
        "habitaciones_desc": ["-habitaciones", "-id"],
    }

    def get_queryset(self):
        self.form_busqueda = BusquedaInmuebleForm(self.request.GET or None)
        qs = Inmueble.objects.select_related("propietario").annotate(num_ofertas=Count("ofertas"))
        if not self.form_busqueda.is_bound:
            return qs.order_by(*self.ORDENES[""])
        self.form_busqueda.is_valid()
        # Si algún filtro tiene error se muestra el mensaje y se aplican solo los filtros válidos
        f = self.form_busqueda.cleaned_data
        q = (f.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(direccion__icontains=q)
                | Q(ciudad__icontains=q)
                | Q(barrio__icontains=q)
                | Q(nombre_conjunto__icontains=q)
                | Q(id_captacion__icontains=q)
                | Q(propietario__nombre_completo__icontains=q)
            )
        if f.get("tipo"):
            qs = qs.filter(tipo_inmueble=f["tipo"])
        if f.get("estado"):
            qs = qs.filter(estado=f["estado"])
        if f.get("ciudad"):
            qs = qs.filter(ciudad__iexact=f["ciudad"])
        barrio = (f.get("barrio") or "").strip()
        if barrio:
            qs = qs.filter(barrio__icontains=barrio)
        # Precio y modalidad se buscan en las ofertas: basta con que UNA oferta cumpla todo
        condiciones = {}
        if f.get("modalidad"):
            condiciones["modalidad"] = f["modalidad"]
        if f.get("precio_min") is not None:
            condiciones["valor__gte"] = f["precio_min"]
        if f.get("precio_max") is not None:
            condiciones["valor__lte"] = f["precio_max"]
        if condiciones:
            qs = qs.filter(
                Exists(OfertaComercial.objects.filter(inmueble=OuterRef("pk"), **condiciones))
            )
        if f.get("habitaciones_min") is not None:
            qs = qs.filter(habitaciones__gte=f["habitaciones_min"])
        return qs.order_by(*self.ORDENES.get(f.get("orden") or "", self.ORDENES[""]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self.form_busqueda
        ctx["form_busqueda"] = form
        ctx["filtros_activos"] = form.is_bound and any(
            (v or "").strip() for k, v in self.request.GET.items() if k != "page"
        )
        ctx["mostrar_avanzados"] = form.is_bound and (form.hay_avanzados() or bool(form.errors))
        ctx["total"] = ctx["paginator"].count if ctx.get("paginator") else len(ctx["inmuebles"])
        # conserva los filtros al cambiar de página
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filtros_url"] = params.urlencode()
        ctx["polizas_alerta"] = polizas_en_alerta().count()
        return ctx


class InmuebleDetailView(LoginRequiredMixin, DetailView):
    model = Inmueble
    template_name = "inmuebles/inmueble_detail.html"
    context_object_name = "inmueble"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        campos = []
        tiene_ofertas = obj.ofertas.exists()
        for f in obj._meta.fields:
            if f.name in ("id", "propietario", "informacion_adicional"):
                continue
            # Con ofertas registradas, los valores se muestran en la tarjeta de ofertas
            if tiene_ofertas and f.name in ("valor_transaccion", "valor_administracion"):
                continue
            valor = getattr(obj, f.name)
            if valor in (None, ""):
                continue
            if f.choices:
                valor = getattr(obj, f"get_{f.name}_display")()
            elif isinstance(valor, bool):
                valor = "Sí" if valor else "No"
            elif f.name in formato.CAMPOS_DINERO:
                valor = formato.pesos(valor)
            elif isinstance(valor, Decimal):
                valor = formato.numero(valor)
            elif isinstance(valor, date):
                valor = formato.fecha(valor)
            campos.append((formato.ETIQUETAS.get(f.name, f.verbose_name.capitalize()), valor))
        ctx["campos"] = campos
        ctx["fotos"] = obj.fotografias.all()
        ctx["ofertas"] = [formato.resumen_oferta(o, n) for n, o in enumerate(obj.ofertas.all(), 1)]
        ctx["form_foto"] = FotografiaSubirForm()
        ctx["documentos"] = obj.documentos.order_by("tipo_documento", "id")
        ctx["form_doc"] = DocumentoSubirForm()
        hoy = timezone.localdate()
        polizas = []
        for p in obj.polizas.order_by("fecha_vencimiento"):
            estado, dias, texto = formato.estado_poliza(p.fecha_vencimiento, hoy)
            polizas.append({"obj": p, "estado": estado, "texto": texto})
        ctx["polizas"] = polizas
        ctx["polizas_alerta"] = sum(1 for p in polizas if p["estado"] != "vigente")
        return ctx


class _InmuebleConOfertasMixin:
    """Guarda el inmueble junto con sus ofertas comerciales (mínimo una)."""

    model = Inmueble
    form_class = InmuebleForm
    template_name = "inmuebles/inmueble_form.html"
    mensaje_exito = ""

    def get_success_url(self):
        return reverse_lazy("inmueble_detail", args=[self.object.pk])

    def get_ofertas(self, data=None):
        instancia = self.object if self.object is not None else Inmueble()
        return OfertaFormSet(data, instance=instancia, prefix="ofertas")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("ofertas", self.get_ofertas())
        ctx["titulo"] = self.titulo
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.es_edicion else None
        form = self.get_form()
        ofertas = self.get_ofertas(request.POST)
        if form.is_valid() and ofertas.is_valid():
            return self.guardar(form, ofertas)
        return self.render_to_response(self.get_context_data(form=form, ofertas=ofertas))

    @transaction.atomic
    def guardar(self, form, ofertas):
        # El valor principal del inmueble (listado y orden por precio) es el de la primera oferta
        primera = ofertas.ofertas_vigentes()[0].cleaned_data
        form.instance.valor_transaccion = primera["valor"]
        form.instance.valor_administracion = primera.get("valor_administracion")
        self.object = form.save()
        ofertas.instance = self.object
        ofertas.save()
        messages.success(self.request, self.mensaje_exito)
        return redirect(self.get_success_url())


class InmuebleCreateView(LoginRequiredMixin, _InmuebleConOfertasMixin, CreateView):
    es_edicion = False
    titulo = "Registrar inmueble"
    mensaje_exito = "El inmueble se registró correctamente."


class InmuebleUpdateView(LoginRequiredMixin, _InmuebleConOfertasMixin, UpdateView):
    es_edicion = True
    titulo = "Editar inmueble"
    mensaje_exito = "Los cambios se guardaron correctamente."


class InmuebleDeleteView(LoginRequiredMixin, DeleteView):
    model = Inmueble
    template_name = "inmuebles/inmueble_confirm_delete.html"
    success_url = reverse_lazy("inmueble_list")

    def form_valid(self, form):
        # Borra también los archivos de fotografías y documentos del disco
        for foto in self.object.fotografias.all():
            foto.archivo.delete(save=False)
        for doc in self.object.documentos.all():
            doc.archivo.delete(save=False)
        for poliza in self.object.polizas.exclude(archivo=""):
            poliza.archivo.delete(save=False)
        messages.success(self.request, "El inmueble se eliminó.")
        return super().form_valid(form)


# ---------------------------- PROPIETARIOS ----------------------------

class PropietarioListView(LoginRequiredMixin, ListView):
    model = Propietario
    template_name = "inmuebles/propietario_list.html"
    context_object_name = "propietarios"
    paginate_by = 20

    def get_queryset(self):
        qs = Propietario.objects.order_by("nombre_completo")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(nombre_completo__icontains=q) | Q(numero_identificacion__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class _PropietarioSuccessMixin:
    """Si se llegó desde el formulario de inmueble (?next=...), regresa allí."""

    def get_success_url(self):
        destino = self.request.GET.get("next", "")
        if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts=None):
            return destino
        return reverse_lazy("propietario_list")


class PropietarioCreateView(LoginRequiredMixin, _PropietarioSuccessMixin, CreateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = "inmuebles/propietario_form.html"

    def form_valid(self, form):
        messages.success(self.request, "El propietario se registró correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Registrar propietario"
        return ctx


class PropietarioUpdateView(LoginRequiredMixin, _PropietarioSuccessMixin, UpdateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = "inmuebles/propietario_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Los cambios se guardaron correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar propietario"
        return ctx


# ---------------------------- FOTOGRAFÍAS ----------------------------

class FotografiaSubirView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        inmueble = get_object_or_404(Inmueble, pk=pk)
        form = FotografiaSubirForm(request.POST, request.FILES)
        if form.is_valid():
            etiqueta = form.cleaned_data["etiqueta"].strip()
            archivos = form.cleaned_data["archivos"]
            for archivo in archivos:
                Fotografia.objects.create(inmueble=inmueble, archivo=archivo, etiqueta=etiqueta)
            if len(archivos) == 1:
                messages.success(request, "Se agregó 1 fotografía.")
            else:
                messages.success(request, f"Se agregaron {len(archivos)} fotografías.")
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
        return redirect("inmueble_detail", pk=inmueble.pk)


class FotografiaEliminarView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        foto = get_object_or_404(Fotografia, pk=pk)
        inmueble_pk = foto.inmueble_id
        foto.archivo.delete(save=False)  # borra el archivo del disco
        foto.delete()
        messages.success(request, "La fotografía se eliminó.")
        return redirect("inmueble_detail", pk=inmueble_pk)


# ---------------------------- DOCUMENTOS ----------------------------

class DocumentoSubirView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        inmueble = get_object_or_404(Inmueble, pk=pk)
        form = DocumentoSubirForm(request.POST, request.FILES)
        if form.is_valid():
            tipo = form.cleaned_data["tipo_documento"]
            archivos = form.cleaned_data["archivos"]
            for archivo in archivos:
                Documento.objects.create(inmueble=inmueble, tipo_documento=tipo, archivo=archivo)
            if len(archivos) == 1:
                messages.success(request, "Se agregó 1 documento.")
            else:
                messages.success(request, f"Se agregaron {len(archivos)} documentos.")
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
        return redirect("inmueble_detail", pk=inmueble.pk)


class DocumentoEliminarView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        doc = get_object_or_404(Documento, pk=pk)
        inmueble_pk = doc.inmueble_id
        doc.archivo.delete(save=False)  # borra el archivo del disco
        doc.delete()
        messages.success(request, "El documento se eliminó.")
        return redirect("inmueble_detail", pk=inmueble_pk)


# ------------------------------ PÓLIZAS ------------------------------

class PolizaCreateView(LoginRequiredMixin, CreateView):
    model = Poliza
    form_class = PolizaForm
    template_name = "inmuebles/poliza_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.inmueble = get_object_or_404(Inmueble, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.inmueble = self.inmueble
        messages.success(self.request, "La póliza se registró correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inmueble_detail", args=[self.inmueble.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Registrar póliza"
        ctx["inmueble"] = self.inmueble
        return ctx


class PolizaUpdateView(LoginRequiredMixin, UpdateView):
    model = Poliza
    form_class = PolizaForm
    template_name = "inmuebles/poliza_form.html"

    def form_valid(self, form):
        archivo_anterior = Poliza.objects.get(pk=self.object.pk).archivo
        anterior = archivo_anterior.name if archivo_anterior else ""
        respuesta = super().form_valid(form)
        # Si se reemplazó o se quitó el documento, borra el archivo viejo del disco
        nuevo = self.object.archivo.name if self.object.archivo else ""
        if anterior and anterior != nuevo:
            archivo_anterior.storage.delete(anterior)
        messages.success(self.request, "Los cambios de la póliza se guardaron correctamente.")
        return respuesta

    def get_success_url(self):
        return reverse_lazy("inmueble_detail", args=[self.object.inmueble_id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar póliza"
        ctx["inmueble"] = self.object.inmueble
        return ctx


class PolizaEliminarView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        poliza = get_object_or_404(Poliza, pk=pk)
        inmueble_pk = poliza.inmueble_id
        if poliza.archivo:
            poliza.archivo.delete(save=False)  # borra el archivo del disco
        poliza.delete()
        messages.success(request, "La póliza se eliminó.")
        return redirect("inmueble_detail", pk=inmueble_pk)


class PolizaAlertasView(LoginRequiredMixin, ListView):
    """Pólizas vencidas o por vencer (RF13). Con ?todas=1 muestra todas las pólizas."""

    template_name = "inmuebles/poliza_alertas.html"
    context_object_name = "polizas"
    paginate_by = 25

    def get_queryset(self):
        if self.request.GET.get("todas") == "1":
            qs = Poliza.objects.all()
        else:
            qs = polizas_en_alerta()
        return qs.select_related("inmueble", "inmueble__propietario").order_by("fecha_vencimiento")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        for p in ctx["polizas"]:
            p.estado, _, p.estado_texto = formato.estado_poliza(p.fecha_vencimiento, hoy)
        ctx["todas"] = self.request.GET.get("todas") == "1"
        ctx["dias_aviso"] = formato.DIAS_AVISO_POLIZA
        return ctx


# ---------------------------- FICHA EN PDF ----------------------------

class InmuebleFichaPDFView(LoginRequiredMixin, View):
    """Genera la ficha del inmueble en PDF (RF15). Con ?descargar=1 se descarga el archivo."""

    def get(self, request, pk):
        inmueble = get_object_or_404(Inmueble, pk=pk)
        try:
            pdf = ficha.generar_pdf(inmueble, request.user)
        except RuntimeError:
            messages.error(request, "No se pudo generar la ficha en PDF. Intenta de nuevo.")
            return redirect("inmueble_detail", pk=inmueble.pk)
        partes = [inmueble.get_tipo_inmueble_display(), inmueble.barrio or inmueble.ciudad, str(inmueble.pk)]
        nombre = "ficha_" + slugify("_".join(partes)).replace("-", "_") + ".pdf"
        respuesta = HttpResponse(pdf, content_type="application/pdf")
        modo = "attachment" if request.GET.get("descargar") == "1" else "inline"
        respuesta["Content-Disposition"] = f'{modo}; filename="{nombre}"'
        return respuesta
