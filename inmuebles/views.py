from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import InmuebleForm, PropietarioForm
from .models import Inmueble, Propietario


# ----------------------------- INMUEBLES -----------------------------

class InmuebleListView(LoginRequiredMixin, ListView):
    model = Inmueble
    template_name = "inmuebles/inmueble_list.html"
    context_object_name = "inmuebles"
    paginate_by = 15

    def get_queryset(self):
        qs = Inmueble.objects.select_related("propietario").order_by("-id")
        q = self.request.GET.get("q", "").strip()
        tipo = self.request.GET.get("tipo", "")
        estado = self.request.GET.get("estado", "")
        if q:
            qs = qs.filter(
                Q(direccion__icontains=q)
                | Q(ciudad__icontains=q)
                | Q(barrio__icontains=q)
                | Q(nombre_conjunto__icontains=q)
                | Q(id_captacion__icontains=q)
                | Q(propietario__nombre_completo__icontains=q)
            )
        if tipo:
            qs = qs.filter(tipo_inmueble=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["tipo"] = self.request.GET.get("tipo", "")
        ctx["estado"] = self.request.GET.get("estado", "")
        ctx["tipos"] = Inmueble.TIPO_INMUEBLE_CHOICES
        ctx["estados"] = Inmueble.ESTADO_CHOICES
        # conserva los filtros al cambiar de página
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filtros_url"] = params.urlencode()
        return ctx


class InmuebleDetailView(LoginRequiredMixin, DetailView):
    model = Inmueble
    template_name = "inmuebles/inmueble_detail.html"
    context_object_name = "inmueble"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        campos = []
        for f in obj._meta.fields:
            if f.name in ("id", "propietario"):
                continue
            valor = getattr(obj, f.name)
            if valor in (None, ""):
                continue
            if f.choices:
                valor = getattr(obj, f"get_{f.name}_display")()
            elif isinstance(valor, bool):
                valor = "Sí" if valor else "No"
            campos.append((f.verbose_name.capitalize(), valor))
        ctx["campos"] = campos
        return ctx


class InmuebleCreateView(LoginRequiredMixin, CreateView):
    model = Inmueble
    form_class = InmuebleForm
    template_name = "inmuebles/inmueble_form.html"

    def get_success_url(self):
        return reverse_lazy("inmueble_detail", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "El inmueble se registró correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Registrar inmueble"
        return ctx


class InmuebleUpdateView(LoginRequiredMixin, UpdateView):
    model = Inmueble
    form_class = InmuebleForm
    template_name = "inmuebles/inmueble_form.html"

    def get_success_url(self):
        return reverse_lazy("inmueble_detail", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Los cambios se guardaron correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar inmueble"
        return ctx


class InmuebleDeleteView(LoginRequiredMixin, DeleteView):
    model = Inmueble
    template_name = "inmuebles/inmueble_confirm_delete.html"
    success_url = reverse_lazy("inmueble_list")

    def form_valid(self, form):
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
