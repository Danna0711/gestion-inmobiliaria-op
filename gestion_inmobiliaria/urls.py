from django.contrib import admin
from django.urls import include, path

from inmuebles.views import ArchivoProtegidoView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # Fotografías, documentos y pólizas: solo se entregan con sesión iniciada (RNF04)
    path("media/<path:ruta>", ArchivoProtegidoView.as_view(), name="archivo_protegido"),
    path("", include("inmuebles.urls")),
]
