from django.urls import path

from . import views

urlpatterns = [
    path("", views.InmuebleListView.as_view(), name="inmueble_list"),
    path("inmuebles/nuevo/", views.InmuebleCreateView.as_view(), name="inmueble_create"),
    path("inmuebles/<int:pk>/", views.InmuebleDetailView.as_view(), name="inmueble_detail"),
    path("inmuebles/<int:pk>/editar/", views.InmuebleUpdateView.as_view(), name="inmueble_update"),
    path("inmuebles/<int:pk>/ficha.pdf", views.InmuebleFichaPDFView.as_view(), name="inmueble_ficha_pdf"),
    path("inmuebles/<int:pk>/eliminar/", views.InmuebleDeleteView.as_view(), name="inmueble_delete"),
    path("inmuebles/<int:pk>/fotos/subir/", views.FotografiaSubirView.as_view(), name="foto_subir"),
    path("fotos/<int:pk>/eliminar/", views.FotografiaEliminarView.as_view(), name="foto_eliminar"),
    path("inmuebles/<int:pk>/documentos/subir/", views.DocumentoSubirView.as_view(), name="documento_subir"),
    path("documentos/<int:pk>/eliminar/", views.DocumentoEliminarView.as_view(), name="documento_eliminar"),
    path("inmuebles/<int:pk>/polizas/nueva/", views.PolizaCreateView.as_view(), name="poliza_create"),
    path("polizas/<int:pk>/editar/", views.PolizaUpdateView.as_view(), name="poliza_update"),
    path("polizas/<int:pk>/eliminar/", views.PolizaEliminarView.as_view(), name="poliza_delete"),
    path("polizas/", views.PolizaAlertasView.as_view(), name="poliza_alertas"),
    path("propietarios/", views.PropietarioListView.as_view(), name="propietario_list"),
    path("propietarios/nuevo/", views.PropietarioCreateView.as_view(), name="propietario_create"),
    path("propietarios/<int:pk>/editar/", views.PropietarioUpdateView.as_view(), name="propietario_update"),
]
