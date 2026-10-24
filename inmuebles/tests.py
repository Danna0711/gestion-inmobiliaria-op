from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Inmueble, Propietario


def oferta(valor, modalidad="venta", indice=0, total=1, iniciales=0, **extra):
    """Datos de formulario para enviar ofertas comerciales junto con el inmueble."""
    datos = {
        "ofertas-TOTAL_FORMS": str(total), "ofertas-INITIAL_FORMS": str(iniciales),
        "ofertas-MIN_NUM_FORMS": "1", "ofertas-MAX_NUM_FORMS": "1000",
        f"ofertas-{indice}-modalidad": modalidad, f"ofertas-{indice}-valor": str(valor),
    }
    for clave, valor_extra in extra.items():
        datos[f"ofertas-{indice}-{clave}"] = valor_extra
    return datos


class ModuloInmueblesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user("asesor", password="clave-segura-123")
        cls.propietario = Propietario.objects.create(
            nombre_completo="Ana Gómez", numero_identificacion="100200300", numero_contacto="3001112233"
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def crear_inmueble(self, **extra):
        datos = dict(
            propietario=self.propietario, ciudad="Bogotá", tipo_inmueble="apartamento",
            direccion="Calle 1 # 2-3", valor_transaccion=300000000,
        )
        datos.update(extra)
        return Inmueble.objects.create(**datos)

    # --- acceso ---
    def test_requiere_login(self):
        self.client.logout()
        resp = self.client.get(reverse("inmueble_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    # --- registro ---
    def test_formulario_se_muestra(self):
        resp = self.client.get(reverse("inmueble_create"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Registrar inmueble")
        self.assertContains(resp, 'name="uso_suelo"')

    def test_registrar_inmueble(self):
        resp = self.client.post(reverse("inmueble_create"), {
            "propietario": self.propietario.pk, "ciudad": "Medellín", "tipo_inmueble": "bodega",
            "estado": "disponible", "direccion": "Zona Industrial 5", **oferta("850000000"),
            "kva": "150", "altura": "8", "uso_suelo": "Industrial",
            "habitaciones": 0, "banos": 1, "garajes": 0, "depositos": 0,
        })
        self.assertEqual(Inmueble.objects.count(), 1)
        inm = Inmueble.objects.get()
        self.assertRedirects(resp, reverse("inmueble_detail", args=[inm.pk]))
        self.assertEqual(inm.uso_suelo, "Industrial")

    def test_registro_invalido_no_guarda(self):
        resp = self.client.post(reverse("inmueble_create"), {"ciudad": "Cali"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Inmueble.objects.count(), 0)
        self.assertContains(resp, "Revisa los campos")

    # --- listado y búsqueda ---
    def test_listado_y_busqueda(self):
        self.crear_inmueble(direccion="Carrera 7 # 10-20")
        self.crear_inmueble(direccion="Avenida Sur 99", ciudad="Cali", tipo_inmueble="casa")
        resp = self.client.get(reverse("inmueble_list"))
        self.assertContains(resp, "Carrera 7")
        self.assertContains(resp, "Avenida Sur")
        resp = self.client.get(reverse("inmueble_list"), {"q": "Cali"})
        self.assertContains(resp, "Avenida Sur")
        self.assertNotContains(resp, "Carrera 7")
        resp = self.client.get(reverse("inmueble_list"), {"tipo": "apartamento"})
        self.assertContains(resp, "Carrera 7")
        self.assertNotContains(resp, "Avenida Sur")
        resp = self.client.get(reverse("inmueble_list"), {"q": "Ana"})
        self.assertContains(resp, "Carrera 7")

    # --- detalle, edición, borrado ---
    def test_detalle(self):
        inm = self.crear_inmueble()
        resp = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
        self.assertContains(resp, "Ana Gómez")
        self.assertContains(resp, "Calle 1 # 2-3")

    def test_editar(self):
        inm = self.crear_inmueble()
        resp = self.client.get(reverse("inmueble_update", args=[inm.pk]))
        self.assertEqual(resp.status_code, 200)
        datos = resp.context["form"].initial.copy()
        datos.update({"direccion": "Nueva dirección 1", "propietario": self.propietario.pk})
        datos.update(oferta("300000000"))
        datos = {k: v for k, v in datos.items() if v is not None and v is not False}
        self.client.post(reverse("inmueble_update", args=[inm.pk]), datos)
        inm.refresh_from_db()
        self.assertEqual(inm.direccion, "Nueva dirección 1")

    def test_eliminar(self):
        inm = self.crear_inmueble()
        self.client.post(reverse("inmueble_delete", args=[inm.pk]))
        self.assertEqual(Inmueble.objects.count(), 0)

    # --- propietarios ---
    def test_registrar_propietario_y_volver(self):
        destino = reverse("inmueble_create")
        resp = self.client.post(
            reverse("propietario_create") + f"?next={destino}",
            {"nombre_completo": "Luis Pérez", "numero_identificacion": "555", "numero_contacto": "3100000000"},
        )
        self.assertRedirects(resp, destino)
        self.assertTrue(Propietario.objects.filter(numero_identificacion="555").exists())

    def test_next_externo_no_se_acepta(self):
        resp = self.client.post(
            reverse("propietario_create") + "?next=https://malicioso.example/",
            {"nombre_completo": "X", "numero_identificacion": "777", "numero_contacto": "1"},
        )
        self.assertRedirects(resp, reverse("propietario_list"))

    def test_identificacion_duplicada_rechazada(self):
        resp = self.client.post(reverse("propietario_create"), {
            "nombre_completo": "Otro", "numero_identificacion": "100200300", "numero_contacto": "1",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Propietario.objects.count(), 1)

    def test_listado_propietarios(self):
        resp = self.client.get(reverse("propietario_list"), {"q": "Gómez"})
        self.assertContains(resp, "Ana Gómez")


class FormatoTests(TestCase):
    def test_pesos_numero_fecha(self):
        from datetime import date
        from decimal import Decimal

        from . import formato

        self.assertEqual(formato.pesos(Decimal("2300000000.00")), "$ 2.300.000.000")
        self.assertEqual(formato.numero(Decimal("85.50")), "85,5")
        self.assertEqual(formato.numero(Decimal("1200.00")), "1.200")
        self.assertEqual(formato.numero(Decimal("0.00")), "0")
        self.assertEqual(formato.fecha(date(2026, 10, 16)), "16/10/2026")

    def test_detalle_muestra_formato_y_tildes(self):
        usuario = get_user_model().objects.create_user("u2", password="clave-segura-123")
        self.client.force_login(usuario)
        p = Propietario.objects.create(nombre_completo="A", numero_identificacion="1", numero_contacto="1")
        inm = Inmueble.objects.create(
            propietario=p, ciudad="Bogotá", tipo_inmueble="casa", direccion="Calle 1",
            valor_transaccion=2300000000, banos=1,
        )
        resp = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
        self.assertContains(resp, "$ 2.300.000.000")
        self.assertContains(resp, "Dirección")
        self.assertContains(resp, "Baños")
        self.assertContains(resp, "Valor de la transacción")


import io
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from .models import Fotografia

MEDIA_TEMPORAL = tempfile.mkdtemp()


def imagen_de_prueba(nombre="foto.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class FotografiasTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        self.usuario = get_user_model().objects.create_user("foto", password="clave-segura-123")
        self.client.force_login(self.usuario)
        propietario = Propietario.objects.create(
            nombre_completo="P", numero_identificacion="42", numero_contacto="1"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=propietario, ciudad="Cali", tipo_inmueble="casa",
            direccion="Calle 5", valor_transaccion=100,
        )

    def subir(self, archivos, etiqueta=""):
        return self.client.post(
            reverse("foto_subir", args=[self.inmueble.pk]),
            {"archivos": archivos, "etiqueta": etiqueta},
        )

    def test_subir_varias_fotos(self):
        resp = self.subir([imagen_de_prueba("a.png"), imagen_de_prueba("b.png")], "Fachada")
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertEqual(self.inmueble.fotografias.count(), 2)
        self.assertEqual(self.inmueble.fotografias.first().etiqueta, "Fachada")

    def test_detalle_muestra_galeria(self):
        self.subir([imagen_de_prueba()], "Sala")
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "Fotografías (1)")
        self.assertContains(resp, "Sala")

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile("nota.txt", b"hola", content_type="text/plain")
        self.subir([falso])
        self.assertEqual(self.inmueble.fotografias.count(), 0)
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "no es una imagen válida")

    def test_subir_sin_archivos_se_rechaza(self):
        self.client.post(reverse("foto_subir", args=[self.inmueble.pk]), {"etiqueta": "x"})
        self.assertEqual(self.inmueble.fotografias.count(), 0)

    def test_eliminar_borra_registro_y_archivo(self):
        self.subir([imagen_de_prueba()])
        foto = self.inmueble.fotografias.get()
        ruta = foto.archivo.path
        self.assertTrue(os.path.exists(ruta))
        self.client.post(reverse("foto_eliminar", args=[foto.pk]))
        self.assertFalse(Fotografia.objects.filter(pk=foto.pk).exists())
        self.assertFalse(os.path.exists(ruta))

    def test_eliminar_inmueble_borra_sus_archivos(self):
        self.subir([imagen_de_prueba()])
        ruta = self.inmueble.fotografias.get().archivo.path
        self.client.post(reverse("inmueble_delete", args=[self.inmueble.pk]))
        self.assertFalse(os.path.exists(ruta))

    def test_requiere_login(self):
        self.client.logout()
        resp = self.subir([imagen_de_prueba()])
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)
        self.assertEqual(Fotografia.objects.count(), 0)

    def test_eliminar_por_get_no_esta_permitido(self):
        self.subir([imagen_de_prueba()])
        foto = self.inmueble.fotografias.get()
        resp = self.client.get(reverse("foto_eliminar", args=[foto.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Fotografia.objects.filter(pk=foto.pk).exists())


class UsoSueloTests(TestCase):
    def test_uso_suelo_se_muestra_para_bodega_y_local_no_para_otros(self):
        from .forms import InmuebleForm

        secciones = {s["titulo"]: s for s in InmuebleForm().secciones()}
        seccion = secciones["Datos de bodega y local"]
        self.assertEqual(set(seccion["tipos"].split(",")), {"bodega", "local"})
        nombres = [c.name for c in seccion["campos"]]
        self.assertIn("uso_suelo", nombres)
        self.assertIn("kva", nombres)
        self.assertIn("altura", nombres)

    def test_registrar_local_con_uso_suelo(self):
        usuario = get_user_model().objects.create_user("l", password="clave-segura-123")
        self.client.force_login(usuario)
        p = Propietario.objects.create(nombre_completo="L", numero_identificacion="8", numero_contacto="1")
        self.client.post(reverse("inmueble_create"), {
            "propietario": p.pk, "ciudad": "Bogotá", "tipo_inmueble": "local", "estado": "disponible",
            "direccion": "Centro 1", **oferta("100000000"), "uso_suelo": "Comercio de ropa",
            "habitaciones": 0, "banos": 1, "garajes": 0, "depositos": 0,
        })
        self.assertEqual(Inmueble.objects.get().uso_suelo, "Comercio de ropa")


class InformacionAdicionalTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("ia", password="clave-segura-123")
        self.client.force_login(self.usuario)
        self.propietario = Propietario.objects.create(
            nombre_completo="I", numero_identificacion="77", numero_contacto="1"
        )

    def test_seccion_disponible_para_todos_los_tipos(self):
        from .forms import InmuebleForm

        seccion = {s["titulo"]: s for s in InmuebleForm().secciones()}["Información adicional"]
        self.assertEqual(seccion["tipos"], "")  # sin restricción de tipo
        self.assertEqual([c.name for c in seccion["campos"]], ["informacion_adicional"])

    def test_registrar_y_ver_en_detalle_para_cada_tipo(self):
        for tipo in ("casa", "apartamento", "bodega", "local", "lote", "otro"):
            resp = self.client.post(reverse("inmueble_create"), {
                "propietario": self.propietario.pk, "ciudad": "Bogotá", "tipo_inmueble": tipo,
                "estado": "disponible", "direccion": f"Dir {tipo}", **oferta("1000"),
                "informacion_adicional": f"Nota de {tipo}\nsegunda línea",
                "habitaciones": 0, "banos": 0, "garajes": 0, "depositos": 0,
            })
            inm = Inmueble.objects.get(direccion=f"Dir {tipo}")
            self.assertRedirects(resp, reverse("inmueble_detail", args=[inm.pk]))
            self.assertEqual(inm.informacion_adicional, f"Nota de {tipo}\nsegunda línea")
            detalle = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
            self.assertContains(detalle, f"Nota de {tipo}")
            self.assertContains(detalle, "<br>")  # respeta los saltos de línea

    def test_es_opcional(self):
        resp = self.client.post(reverse("inmueble_create"), {
            "propietario": self.propietario.pk, "ciudad": "Cali", "tipo_inmueble": "casa",
            "estado": "disponible", "direccion": "Sin nota", **oferta("1000"),
            "habitaciones": 0, "banos": 0, "garajes": 0, "depositos": 0,
        })
        inm = Inmueble.objects.get(direccion="Sin nota")
        self.assertRedirects(resp, reverse("inmueble_detail", args=[inm.pk]))
        detalle = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
        self.assertNotContains(detalle, "Información adicional</div>")


# ======================= DOCUMENTOS LEGALES Y PÓLIZAS =======================

from datetime import date, timedelta

from django.utils import timezone

from .models import Documento, Poliza


def pdf_de_prueba(nombre="escritura.pdf", contenido=b"%PDF-1.4 prueba"):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class DocumentosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("docs", password="clave-segura-123")
        self.client.force_login(self.usuario)
        propietario = Propietario.objects.create(
            nombre_completo="P", numero_identificacion="77", numero_contacto="1"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=propietario, ciudad="Cali", tipo_inmueble="casa",
            direccion="Calle 9", valor_transaccion=100,
        )

    def subir(self, archivos, tipo="escritura"):
        return self.client.post(
            reverse("documento_subir", args=[self.inmueble.pk]),
            {"tipo_documento": tipo, "archivos": archivos},
        )

    def test_subir_varios_documentos(self):
        resp = self.subir([pdf_de_prueba("a.pdf"), pdf_de_prueba("b.pdf")], "planos")
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertEqual(self.inmueble.documentos.count(), 2)
        self.assertEqual(self.inmueble.documentos.first().tipo_documento, "planos")

    def test_detalle_lista_documentos(self):
        self.subir([pdf_de_prueba("mi_escritura.pdf")])
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "Documentos legales (1)")
        self.assertContains(resp, "Escritura")
        self.assertContains(resp, "mi_escritura")

    def test_formato_no_permitido_se_rechaza(self):
        malo = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        self.subir([malo])
        self.assertEqual(self.inmueble.documentos.count(), 0)
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "no es un formato permitido")

    def test_tipo_invalido_se_rechaza(self):
        self.subir([pdf_de_prueba()], tipo="inventado")
        self.assertEqual(self.inmueble.documentos.count(), 0)

    def test_subir_sin_archivos_se_rechaza(self):
        self.client.post(
            reverse("documento_subir", args=[self.inmueble.pk]), {"tipo_documento": "otro"}
        )
        self.assertEqual(self.inmueble.documentos.count(), 0)

    def test_documento_demasiado_grande(self):
        from . import forms
        original = forms.TAMANO_MAXIMO_DOCUMENTO
        forms.TAMANO_MAXIMO_DOCUMENTO = 5
        try:
            self.subir([pdf_de_prueba(contenido=b"123456789")])
        finally:
            forms.TAMANO_MAXIMO_DOCUMENTO = original
        self.assertEqual(self.inmueble.documentos.count(), 0)

    def test_eliminar_borra_registro_y_archivo(self):
        self.subir([pdf_de_prueba()])
        doc = self.inmueble.documentos.get()
        ruta = doc.archivo.path
        self.assertTrue(os.path.exists(ruta))
        resp = self.client.post(reverse("documento_eliminar", args=[doc.pk]))
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertFalse(Documento.objects.filter(pk=doc.pk).exists())
        self.assertFalse(os.path.exists(ruta))

    def test_eliminar_por_get_no_esta_permitido(self):
        self.subir([pdf_de_prueba()])
        doc = self.inmueble.documentos.get()
        resp = self.client.get(reverse("documento_eliminar", args=[doc.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Documento.objects.filter(pk=doc.pk).exists())

    def test_requiere_login(self):
        self.client.logout()
        resp = self.subir([pdf_de_prueba()])
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Documento.objects.count(), 0)

    def test_eliminar_inmueble_borra_archivos_de_documentos(self):
        self.subir([pdf_de_prueba()])
        ruta = self.inmueble.documentos.get().archivo.path
        self.client.post(reverse("inmueble_delete", args=[self.inmueble.pk]))
        self.assertEqual(Documento.objects.count(), 0)
        self.assertFalse(os.path.exists(ruta))


class PolizasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("pol", password="clave-segura-123")
        self.client.force_login(self.usuario)
        propietario = Propietario.objects.create(
            nombre_completo="Prop Uno", numero_identificacion="88", numero_contacto="1"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=propietario, ciudad="Cali", tipo_inmueble="casa",
            direccion="Carrera 7", valor_transaccion=100,
        )
        self.hoy = timezone.localdate()

    def nueva(self, dias, nombre="Todo riesgo"):
        return Poliza.objects.create(
            inmueble=self.inmueble, nombre_poliza=nombre, valor=1000000,
            fecha_vencimiento=self.hoy + timedelta(days=dias),
        )

    def datos(self, **extra):
        d = {
            "nombre_poliza": "Incendio", "valor": "2500000",
            "fecha_vencimiento": (self.hoy + timedelta(days=200)).isoformat(),
            "numero_contrato": "AB-123",
        }
        d.update(extra)
        return d

    # --- regla de estado ---
    def test_estados_segun_dias(self):
        from . import formato
        hoy = date(2026, 10, 22)
        casos = {
            date(2026, 10, 21): ("vencida", "Vencida hace 1 día"),
            date(2026, 10, 12): ("vencida", "Vencida hace 10 días"),
            date(2026, 10, 22): ("por_vencer", "Vence hoy"),
            date(2026, 10, 23): ("por_vencer", "Vence en 1 día"),
            date(2026, 11, 21): ("por_vencer", "Vence en 30 días"),   # límite: aún avisa
            date(2026, 11, 22): ("vigente", "Vigente"),               # 31 días: no avisa
        }
        for fecha_v, (estado, texto) in casos.items():
            e, _, t = formato.estado_poliza(fecha_v, hoy)
            self.assertEqual((e, t), (estado, texto), fecha_v)

    # --- registro ---
    def test_formulario_se_muestra(self):
        resp = self.client.get(reverse("poliza_create", args=[self.inmueble.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Registrar póliza")
        self.assertContains(resp, 'type="date"')

    def test_registrar_poliza(self):
        resp = self.client.post(reverse("poliza_create", args=[self.inmueble.pk]), self.datos())
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        poliza = self.inmueble.polizas.get()
        self.assertEqual(poliza.nombre_poliza, "Incendio")
        self.assertEqual(poliza.numero_contrato, "AB-123")

    def test_registrar_sin_numero_de_contrato(self):
        self.client.post(
            reverse("poliza_create", args=[self.inmueble.pk]), self.datos(numero_contrato="")
        )
        self.assertEqual(self.inmueble.polizas.count(), 1)

    def test_registro_invalido_no_guarda(self):
        resp = self.client.post(
            reverse("poliza_create", args=[self.inmueble.pk]), {"nombre_poliza": "X"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Poliza.objects.count(), 0)

    def test_valor_negativo_se_rechaza(self):
        resp = self.client.post(
            reverse("poliza_create", args=[self.inmueble.pk]), self.datos(valor="-5")
        )
        self.assertEqual(Poliza.objects.count(), 0)
        self.assertContains(resp, "no puede ser negativo")

    def test_editar_poliza(self):
        p = self.nueva(100)
        resp = self.client.post(reverse("poliza_update", args=[p.pk]), self.datos(nombre_poliza="Nueva"))
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        p.refresh_from_db()
        self.assertEqual(p.nombre_poliza, "Nueva")

    def test_eliminar_poliza(self):
        p = self.nueva(100)
        resp = self.client.post(reverse("poliza_delete", args=[p.pk]))
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertEqual(Poliza.objects.count(), 0)
        self.assertEqual(self.client.get(reverse("poliza_delete", args=[999])).status_code, 405)

    # --- alertas ---
    def test_detalle_muestra_estado_y_alerta(self):
        self.nueva(10, "Por vencer")
        self.nueva(-3, "Ya vencida")
        self.nueva(90, "Vigente larga")
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "Pólizas (3)")
        self.assertContains(resp, "Vence en 10 días")
        self.assertContains(resp, "Vencida hace 3 días")
        self.assertContains(resp, "Hay 2 pólizas vencidas o próximas a vencer.")

    def test_pagina_de_alertas_solo_muestra_las_que_corresponden(self):
        self.nueva(5, "Poliza proxima")
        self.nueva(-1, "Poliza vencida")
        self.nueva(60, "Poliza lejana")
        resp = self.client.get(reverse("poliza_alertas"))
        self.assertContains(resp, "Poliza proxima")
        self.assertContains(resp, "Poliza vencida")
        self.assertNotContains(resp, "Poliza lejana")
        resp = self.client.get(reverse("poliza_alertas") + "?todas=1")
        self.assertContains(resp, "Poliza lejana")

    def test_alertas_ordenadas_por_vencimiento(self):
        self.nueva(20, "BBB")
        self.nueva(-5, "AAA")
        resp = self.client.get(reverse("poliza_alertas"))
        contenido = resp.content.decode()
        self.assertLess(contenido.index("AAA"), contenido.index("BBB"))

    def test_listado_muestra_aviso_si_hay_alertas(self):
        resp = self.client.get(reverse("inmueble_list"))
        self.assertNotContains(resp, "vencida o próxima a vencer")
        self.nueva(7)
        resp = self.client.get(reverse("inmueble_list"))
        self.assertContains(resp, "Hay 1 póliza vencida o próxima a vencer.")

    def test_sin_alertas_muestra_mensaje(self):
        resp = self.client.get(reverse("poliza_alertas"))
        self.assertContains(resp, "No hay pólizas vencidas ni por vencer.")

    def test_requiere_login(self):
        self.client.logout()
        for nombre, args in (("poliza_alertas", []), ("poliza_create", [self.inmueble.pk])):
            resp = self.client.get(reverse(nombre, args=args))
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/accounts/login/", resp.url)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class PolizaDocumentoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("polarch", password="clave-segura-123")
        self.client.force_login(self.usuario)
        propietario = Propietario.objects.create(
            nombre_completo="P", numero_identificacion="55", numero_contacto="1"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=propietario, ciudad="Cali", tipo_inmueble="casa",
            direccion="Calle 3", valor_transaccion=100,
        )

    def datos(self, **extra):
        d = {
            "nombre_poliza": "Incendio", "valor": "1000",
            "fecha_vencimiento": (timezone.localdate() + timedelta(days=90)).isoformat(),
            "numero_contrato": "X1",
        }
        d.update(extra)
        return d

    def crear(self, archivo=None):
        datos = self.datos()
        if archivo:
            datos["archivo"] = archivo
        return self.client.post(reverse("poliza_create", args=[self.inmueble.pk]), datos)

    def test_registrar_poliza_con_documento(self):
        resp = self.crear(pdf_de_prueba("poliza.pdf"))
        self.assertRedirects(resp, reverse("inmueble_detail", args=[self.inmueble.pk]))
        poliza = self.inmueble.polizas.get()
        self.assertTrue(poliza.archivo.name.endswith(".pdf"))
        detalle = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(detalle, "poliza")

    def test_documento_es_opcional(self):
        self.crear()
        self.assertEqual(self.inmueble.polizas.count(), 1)
        self.assertFalse(self.inmueble.polizas.get().archivo)

    def test_formato_no_permitido_se_rechaza(self):
        malo = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        resp = self.crear(malo)
        self.assertEqual(self.inmueble.polizas.count(), 0)
        self.assertContains(resp, "no es un formato permitido")

    def test_reemplazar_documento_borra_el_anterior(self):
        self.crear(pdf_de_prueba("uno.pdf"))
        poliza = self.inmueble.polizas.get()
        ruta_vieja = poliza.archivo.path
        datos = self.datos(archivo=pdf_de_prueba("dos.pdf"))
        self.client.post(reverse("poliza_update", args=[poliza.pk]), datos)
        poliza.refresh_from_db()
        self.assertNotEqual(poliza.archivo.path, ruta_vieja)
        self.assertTrue(os.path.exists(poliza.archivo.path))
        self.assertFalse(os.path.exists(ruta_vieja))

    def test_editar_sin_subir_archivo_conserva_el_actual(self):
        self.crear(pdf_de_prueba("uno.pdf"))
        poliza = self.inmueble.polizas.get()
        ruta = poliza.archivo.path
        self.client.post(reverse("poliza_update", args=[poliza.pk]), self.datos(nombre_poliza="Otro nombre"))
        poliza.refresh_from_db()
        self.assertEqual(poliza.nombre_poliza, "Otro nombre")
        self.assertEqual(poliza.archivo.path, ruta)
        self.assertTrue(os.path.exists(ruta))

    def test_quitar_documento_borra_el_archivo(self):
        self.crear(pdf_de_prueba("uno.pdf"))
        poliza = self.inmueble.polizas.get()
        ruta = poliza.archivo.path
        self.client.post(reverse("poliza_update", args=[poliza.pk]), self.datos(**{"archivo-clear": "on"}))
        poliza.refresh_from_db()
        self.assertFalse(poliza.archivo)
        self.assertFalse(os.path.exists(ruta))

    def test_eliminar_poliza_borra_el_archivo(self):
        self.crear(pdf_de_prueba())
        poliza = self.inmueble.polizas.get()
        ruta = poliza.archivo.path
        self.client.post(reverse("poliza_delete", args=[poliza.pk]))
        self.assertEqual(Poliza.objects.count(), 0)
        self.assertFalse(os.path.exists(ruta))

    def test_eliminar_inmueble_borra_archivos_de_polizas(self):
        self.crear(pdf_de_prueba())
        ruta = self.inmueble.polizas.get().archivo.path
        self.client.post(reverse("inmueble_delete", args=[self.inmueble.pk]))
        self.assertFalse(os.path.exists(ruta))


# ============================ BÚSQUEDA Y FILTROS ============================

from .models import OfertaComercial

class BusquedaFiltrosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user("busca", password="clave-segura-123")
        p1 = Propietario.objects.create(nombre_completo="Laura Ríos", numero_identificacion="901", numero_contacto="1")
        p2 = Propietario.objects.create(nombre_completo="Mario Paz", numero_identificacion="902", numero_contacto="2")

        def crear(direccion, **extra):
            datos = dict(propietario=p1, ciudad="Bogotá", tipo_inmueble="apartamento",
                         direccion=direccion, valor_transaccion=300000000, habitaciones=2)
            datos.update(extra)
            inmueble = Inmueble.objects.create(**datos)
            OfertaComercial.objects.create(
                inmueble=inmueble, valor=inmueble.valor_transaccion,
                modalidad="arriendo" if inmueble.estado == "arrendado" else "venta",
            )
            return inmueble

        crear("INM-A Cedritos", barrio="Cedritos", valor_transaccion=250000000, habitaciones=2)
        crear("INM-B Chapinero", barrio="Chapinero Alto", valor_transaccion=480000000, habitaciones=3)
        crear("INM-C Poblado", ciudad="Medellín", barrio="El Poblado", valor_transaccion=620000000,
              habitaciones=4, propietario=p2)
        crear("INM-D Bodega", ciudad="Medellín", barrio="Guayabal", tipo_inmueble="bodega",
              valor_transaccion=900000000, habitaciones=0, estado="arrendado")

    def setUp(self):
        self.client.force_login(self.usuario)

    def buscar(self, **filtros):
        return self.client.get(reverse("inmueble_list"), filtros)

    def direcciones(self, resp):
        return [i.direccion.split()[0] for i in resp.context["inmuebles"]]

    def test_sin_filtros_muestra_todos(self):
        resp = self.buscar()
        self.assertEqual(len(resp.context["inmuebles"]), 4)
        self.assertNotContains(resp, "inmuebles encontrados")

    def test_filtro_ciudad(self):
        resp = self.buscar(ciudad="Medellín")
        self.assertEqual(sorted(self.direcciones(resp)), ["INM-C", "INM-D"])
        self.assertContains(resp, "2 inmuebles encontrados")

    def test_lista_de_ciudades_sale_de_los_inmuebles(self):
        resp = self.buscar()
        opciones = [v for v, _ in resp.context["form_busqueda"].fields["ciudad"].choices]
        self.assertEqual(opciones, ["", "Bogotá", "Medellín"])

    def test_filtro_barrio_parcial(self):
        resp = self.buscar(barrio="chapi")
        self.assertEqual(self.direcciones(resp), ["INM-B"])

    def test_rango_de_precio_con_puntos(self):
        resp = self.buscar(precio_min="300.000.000", precio_max="$ 700.000.000")
        self.assertEqual(sorted(self.direcciones(resp)), ["INM-B", "INM-C"])

    def test_solo_precio_minimo(self):
        resp = self.buscar(precio_min="600000000")
        self.assertEqual(sorted(self.direcciones(resp)), ["INM-C", "INM-D"])

    def test_precio_invalido_muestra_error_y_aplica_los_demas(self):
        resp = self.buscar(precio_min="mucho", ciudad="Bogotá")
        self.assertContains(resp, "Escribe solo números")
        self.assertEqual(sorted(self.direcciones(resp)), ["INM-A", "INM-B"])

    def test_precio_minimo_mayor_que_maximo(self):
        resp = self.buscar(precio_min="800000000", precio_max="100000000")
        self.assertContains(resp, "debe ser mayor o igual")

    def test_habitaciones_minimas(self):
        resp = self.buscar(habitaciones_min="3")
        self.assertEqual(sorted(self.direcciones(resp)), ["INM-B", "INM-C"])

    def test_filtros_combinados(self):
        resp = self.buscar(ciudad="Medellín", tipo="apartamento", precio_max="700000000", habitaciones_min="4")
        self.assertEqual(self.direcciones(resp), ["INM-C"])
        resp = self.buscar(ciudad="Bogotá", estado="arrendado")
        self.assertEqual(self.direcciones(resp), [])
        self.assertContains(resp, "No hay inmuebles que coincidan")

    def test_busqueda_por_texto_sigue_funcionando(self):
        resp = self.buscar(q="Mario")
        self.assertEqual(self.direcciones(resp), ["INM-C"])

    def test_ordenar_por_precio(self):
        resp = self.buscar(orden="precio_asc")
        self.assertEqual(self.direcciones(resp), ["INM-A", "INM-B", "INM-C", "INM-D"])
        resp = self.buscar(orden="precio_desc")
        self.assertEqual(self.direcciones(resp), ["INM-D", "INM-C", "INM-B", "INM-A"])

    def test_ordenar_por_habitaciones(self):
        resp = self.buscar(orden="habitaciones_desc")
        self.assertEqual(self.direcciones(resp)[0], "INM-C")

    def test_panel_avanzado_abierto_si_hay_filtros_avanzados(self):
        self.assertFalse(self.buscar(tipo="casa").context["mostrar_avanzados"])
        self.assertTrue(self.buscar(barrio="Cedritos").context["mostrar_avanzados"])

    def test_paginacion_conserva_filtros(self):
        resp = self.buscar(ciudad="Medellín", page="1")
        self.assertIn("ciudad=Medell", resp.context["filtros_url"])
        self.assertNotIn("page", resp.context["filtros_url"])


# ============================== FICHA EN PDF ==============================

@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class FichaPDFTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "ficha", password="clave-segura-123", first_name="Sara", last_name="Díaz"
        )
        self.client.force_login(self.usuario)
        self.propietario = Propietario.objects.create(
            nombre_completo="Propietario Secreto", numero_identificacion="5551234", numero_contacto="3009998877"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=self.propietario, ciudad="Bogotá", barrio="Cedritos", tipo_inmueble="apartamento",
            direccion="Calle 140 # 12-30", valor_transaccion=350000000, valor_administracion=420000,
            habitaciones=3, banos=2, estrato=4, servicio_agua=True, ascensores=True,
            matricula_1="50N-123456", margen_negociacion=15000000, impuesto_predial=1800000,
            id_captacion="CAP-777", informacion_adicional="Vista exterior y cerca a TransMilenio.",
        )

    def html(self):
        from django.template.loader import render_to_string
        from . import ficha
        ctx = ficha.contexto_ficha(self.inmueble, self.usuario)
        ctx.update({"foto_principal": None, "filas_miniaturas": []})
        return render_to_string("inmuebles/ficha_pdf.html", ctx)

    def test_genera_pdf(self):
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))
        self.assertIn("inline", resp["Content-Disposition"])
        self.assertIn("ficha_apartamento_cedritos", resp["Content-Disposition"])

    def test_descargar(self):
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]), {"descargar": "1"})
        self.assertIn("attachment", resp["Content-Disposition"])

    def test_contenido_comercial(self):
        html = self.html()
        self.assertIn("Apartamento en Cedritos, Bogotá", html)
        self.assertIn("$ 350.000.000", html)
        self.assertIn("$ 420.000", html)
        self.assertIn("Calle 140 # 12-30", html)
        self.assertIn("Habitaciones", html)
        self.assertIn("Vista exterior", html)
        self.assertIn("311 553 7531", html)  # contacto de la inmobiliaria

    def test_areas_en_formato_colombiano(self):
        from decimal import Decimal
        self.inmueble.area_construida = Decimal("82.50")
        self.inmueble.save()
        html = self.html()
        self.assertIn("Área construida (m2)", html)
        self.assertIn("82,5", html)

    def test_no_incluye_datos_internos(self):
        html = self.html()
        for dato in ["Propietario Secreto", "5551234", "3009998877", "50N-123456",
                     "15.000.000", "1.800.000", "CAP-777", "Disponible"]:
            self.assertNotIn(dato, html, dato)

    def test_secciones_internas_no_estan_configuradas(self):
        from . import ficha
        configurados = {c for _, campos in ficha.SECCIONES_FICHA for c in campos}
        self.assertFalse(configurados & ficha.CAMPOS_INTERNOS)

    def test_si_no_falsos_se_omiten_y_servicios_se_muestran(self):
        from . import ficha
        ctx = ficha.contexto_ficha(self.inmueble)
        filas = {e: v for s in ctx["secciones"] for e, v in s["filas"]}
        self.assertEqual(filas["Ascensores"], "Sí")
        self.assertEqual(filas["Servicio de agua"], "Sí")
        self.assertEqual(filas["Servicio de gas"], "No")
        self.assertNotIn("Club house", filas)

    def test_no_muestra_asesor(self):
        self.inmueble.nombre_agente = "Paola Gómez"
        self.inmueble.save()
        html = self.html()
        self.assertNotIn("Paola Gómez", html)
        self.assertNotIn("Sara Díaz", html)  # tampoco el usuario que genera la ficha
        self.assertNotIn("Asesor", html)

    def test_pdf_con_fotografias(self):
        from unittest import mock
        from . import ficha
        self.enterContext(mock.patch.object(ficha, "OPACIDAD_MARCA", 0))
        sin_fotos = len(self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk])).content)
        for i in range(9):
            memoria = io.BytesIO()
            Image.new("RGB", (40, 30), (20 * i, 100, 255 - 20 * i)).save(memoria, "PNG")
            archivo = SimpleUploadedFile(f"f{i}.png", memoria.getvalue(), content_type="image/png")
            Fotografia.objects.create(inmueble=self.inmueble, archivo=archivo, etiqueta=f"Foto {i}")
        from . import ficha
        self.assertEqual(len(ficha.contexto_ficha(self.inmueble)["fotos"]), ficha.MAX_FOTOS)
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.content), sin_fotos)
        # las 7 fotos más el logo deben quedar incrustados como imágenes dentro del PDF
        self.assertEqual(resp.content.count(b"/Subtype /Image"), ficha.MAX_FOTOS + 1)

    def test_logo_en_la_ficha(self):
        from unittest import mock as _mock
        from . import ficha as _ficha
        self.enterContext(_mock.patch.object(_ficha, "OPACIDAD_MARCA", 0))
        from . import ficha
        self.assertTrue(ficha.LOGO.exists())
        con_logo = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk])).content
        self.assertEqual(con_logo.count(b"/Subtype /Image"), 1)

    def test_sin_logo_la_ficha_se_genera_igual(self):
        from unittest import mock as _mock
        from . import ficha as _ficha
        self.enterContext(_mock.patch.object(_ficha, "OPACIDAD_MARCA", 0))
        from pathlib import Path
        from unittest import mock
        from . import ficha
        with mock.patch.object(ficha, "LOGO", Path("no_existe.png")):
            resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))
        self.assertTrue(resp.content.startswith(b"%PDF"))
        self.assertEqual(resp.content.count(b"/Subtype /Image"), 0)

    def test_foto_dañada_no_impide_generar(self):
        Fotografia.objects.create(
            inmueble=self.inmueble, archivo=SimpleUploadedFile("rota.png", b"no es imagen")
        )
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_bodega_muestra_datos_tecnicos(self):
        self.inmueble.tipo_inmueble = "bodega"
        self.inmueble.kva = 150
        self.inmueble.uso_suelo = "Industrial"
        self.inmueble.save()
        html = self.html()
        self.assertIn("Datos técnicos", html)
        self.assertIn("Industrial", html)

    def test_detalle_tiene_botones(self):
        resp = self.client.get(reverse("inmueble_detail", args=[self.inmueble.pk]))
        self.assertContains(resp, "Ver ficha PDF")
        self.assertContains(resp, reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))

    def test_requiere_login(self):
        self.client.logout()
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[self.inmueble.pk]))
        self.assertEqual(resp.status_code, 302)


class MarcaDeAguaTests(TestCase):
    def setUp(self):
        propietario = Propietario.objects.create(
            nombre_completo="P", numero_identificacion="61", numero_contacto="1"
        )
        self.inmueble = Inmueble.objects.create(
            propietario=propietario, ciudad="Cali", tipo_inmueble="casa", direccion="Calle 1",
            valor_transaccion=100, informacion_adicional="Línea\n" * 120,  # fuerza más de una página
        )

    def imagenes_por_pagina(self, pdf):
        from pypdf import PdfReader
        resultado = []
        for pagina in PdfReader(io.BytesIO(pdf)).pages:
            xobjects = pagina["/Resources"].get("/XObject", {})
            resultado.append(len(xobjects))
        return resultado

    def generar(self, **cambios):
        from unittest import mock
        from . import ficha
        with mock.patch.multiple(ficha, **cambios) if cambios else mock.patch.object(ficha, "MAX_FOTOS", 7):
            return ficha.generar_pdf(self.inmueble)

    def test_archivo_de_marca_existe(self):
        from . import ficha
        self.assertTrue(ficha.MARCA_DE_AGUA.exists())

    def test_marca_en_todas_las_paginas(self):
        con_marca = self.imagenes_por_pagina(self.generar())
        sin_marca = self.imagenes_por_pagina(self.generar(OPACIDAD_MARCA=0))
        self.assertGreater(len(con_marca), 1)
        for con, sin in zip(con_marca, sin_marca):
            self.assertEqual(con, sin + 1)  # una imagen más por página: la marca de agua

    def test_sin_archivo_la_ficha_se_genera_sin_marca(self):
        from pathlib import Path
        pdf = self.generar(MARCA_DE_AGUA=Path("no_existe.png"))
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(self.imagenes_por_pagina(pdf), self.imagenes_por_pagina(self.generar(OPACIDAD_MARCA=0)))


# ======================== OFERTAS COMERCIALES Y BODEGA ========================

class OfertasComercialesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("ofe", password="clave-segura-123")
        self.client.force_login(self.usuario)
        self.propietario = Propietario.objects.create(
            nombre_completo="Dueño", numero_identificacion="4040", numero_contacto="1"
        )

    def base(self, **extra):
        datos = {
            "propietario": self.propietario.pk, "ciudad": "Bogotá", "tipo_inmueble": "bodega",
            "estado": "disponible", "direccion": "Parque Industrial Santodomingo",
            "habitaciones": 0, "banos": 2, "garajes": 0, "depositos": 0,
        }
        datos.update(extra)
        return datos

    def dos_ofertas(self):
        """Como la presentación de la bodega: opción 1 en arriendo con IVA y opción 2."""
        datos = self.base()
        datos.update(oferta("157500000", "arriendo", indice=0, total=2, titulo="Opción 1",
                            aplica_iva="on", valor_administracion="2500000", area="4000",
                            descripcion="4.000 m2 con estantería", ventajas="2 muelles"))
        datos.update(oferta("74000000", "arriendo", indice=1, total=2, titulo="Opción 2",
                            aplica_iva="on", valor_administracion="2500000"))
        return datos

    def crear(self, datos):
        return self.client.post(reverse("inmueble_create"), datos)

    # --- formulario ---
    def test_formulario_tiene_ofertas_y_boton(self):
        resp = self.client.get(reverse("inmueble_create"))
        self.assertContains(resp, "Ofertas comerciales")
        self.assertContains(resp, "+ Agregar oferta")
        self.assertContains(resp, 'name="ofertas-TOTAL_FORMS"')
        self.assertContains(resp, 'name="ofertas-0-valor"')
        self.assertContains(resp, "ofertas-__prefix__-valor")  # plantilla para el botón
        self.assertNotContains(resp, 'name="valor_transaccion"')

    def test_registrar_con_una_oferta(self):
        resp = self.crear({**self.base(), **oferta("450000000")})
        inm = Inmueble.objects.get()
        self.assertRedirects(resp, reverse("inmueble_detail", args=[inm.pk]))
        self.assertEqual(inm.ofertas.count(), 1)
        self.assertEqual(inm.valor_transaccion, 450000000)

    def test_registrar_con_dos_ofertas(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        self.assertEqual([o.titulo for o in inm.ofertas.all()], ["Opción 1", "Opción 2"])
        self.assertEqual(inm.valor_transaccion, 157500000)  # valor principal = primera oferta
        self.assertEqual(inm.valor_administracion, 2500000)

    def test_oferta_obligatoria_vacia(self):
        resp = self.crear({**self.base(), **oferta("")})
        self.assertEqual(Inmueble.objects.count(), 0)
        self.assertContains(resp, "Este campo es obligatorio", status_code=200)

    def test_sin_ninguna_oferta(self):
        datos = self.base()
        datos.update({"ofertas-TOTAL_FORMS": "0", "ofertas-INITIAL_FORMS": "0",
                      "ofertas-MIN_NUM_FORMS": "1", "ofertas-MAX_NUM_FORMS": "1000"})
        resp = self.crear(datos)
        self.assertEqual(Inmueble.objects.count(), 0)
        self.assertContains(resp, "Registra al menos una oferta comercial.")

    def test_valor_cero_se_rechaza(self):
        resp = self.crear({**self.base(), **oferta("0")})
        self.assertEqual(Inmueble.objects.count(), 0)
        self.assertContains(resp, "El valor debe ser mayor que cero.")

    def test_oferta_quitada_con_el_boton_no_se_guarda(self):
        datos = self.dos_ofertas()
        datos["ofertas-1-DELETE"] = "on"
        self.crear(datos)
        self.assertEqual(Inmueble.objects.get().ofertas.count(), 1)

    # --- edición ---
    def datos_edicion(self, inm, **cambios):
        datos = self.base()
        ofertas = list(inm.ofertas.all())
        datos.update({"ofertas-TOTAL_FORMS": str(len(ofertas)), "ofertas-INITIAL_FORMS": str(len(ofertas)),
                      "ofertas-MIN_NUM_FORMS": "1", "ofertas-MAX_NUM_FORMS": "1000"})
        for i, o in enumerate(ofertas):
            datos.update({f"ofertas-{i}-id": str(o.pk), f"ofertas-{i}-modalidad": o.modalidad,
                          f"ofertas-{i}-valor": str(o.valor)})
        datos.update(cambios)
        return datos

    def test_editar_valor_de_la_primera_oferta_actualiza_el_inmueble(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        self.client.post(reverse("inmueble_update", args=[inm.pk]),
                         self.datos_edicion(inm, **{"ofertas-0-valor": "160000000"}))
        inm.refresh_from_db()
        self.assertEqual(inm.valor_transaccion, 160000000)

    def test_eliminar_una_oferta_al_editar(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        self.client.post(reverse("inmueble_update", args=[inm.pk]),
                         self.datos_edicion(inm, **{"ofertas-1-DELETE": "on"}))
        self.assertEqual(inm.ofertas.count(), 1)

    def test_no_se_pueden_eliminar_todas(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        resp = self.client.post(reverse("inmueble_update", args=[inm.pk]),
                                self.datos_edicion(inm, **{"ofertas-0-DELETE": "on", "ofertas-1-DELETE": "on"}))
        self.assertContains(resp, "Registra al menos una oferta comercial.")
        self.assertEqual(inm.ofertas.count(), 2)

    def test_editar_inmueble_antiguo_sin_ofertas_obliga_a_crear_una(self):
        inm = Inmueble.objects.create(propietario=self.propietario, ciudad="Cali", tipo_inmueble="casa",
                                      direccion="Antiguo", valor_transaccion=100)
        resp = self.client.get(reverse("inmueble_update", args=[inm.pk]))
        self.assertContains(resp, 'name="ofertas-0-valor"')  # aparece un formulario de oferta vacío

    # --- detalle y listado ---
    def test_detalle_muestra_ofertas_con_iva(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        resp = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
        self.assertContains(resp, "Ofertas comerciales (2)")
        self.assertContains(resp, "Canon mensual")
        self.assertContains(resp, "$ 157.500.000")
        self.assertContains(resp, "$ 29.925.000")   # IVA 19 % de 157.500.000
        self.assertContains(resp, "$ 14.060.000")   # IVA 19 % de 74.000.000 (igual a la presentación)
        self.assertContains(resp, "4.000 m²")

    def test_listado_indica_varias_ofertas(self):
        self.crear(self.dos_ofertas())
        self.assertContains(self.client.get(reverse("inmueble_list")), "2 ofertas")

    # --- búsqueda ---
    def test_buscar_por_modalidad_y_precio_de_cualquier_oferta(self):
        self.crear(self.dos_ofertas())
        lista = reverse("inmueble_list")
        self.assertEqual(len(self.client.get(lista, {"modalidad": "arriendo"}).context["inmuebles"]), 1)
        self.assertEqual(len(self.client.get(lista, {"modalidad": "venta"}).context["inmuebles"]), 0)
        # solo la opción 2 (74 millones) cae en este rango
        resp = self.client.get(lista, {"precio_min": "70.000.000", "precio_max": "80.000.000"})
        self.assertEqual(len(resp.context["inmuebles"]), 1)

    def test_la_misma_oferta_debe_cumplir_modalidad_y_precio(self):
        self.crear({**self.base(), **oferta("74000000", "venta", total=2),
                    "ofertas-1-modalidad": "arriendo", "ofertas-1-valor": "5000000"})
        resp = self.client.get(reverse("inmueble_list"), {"modalidad": "arriendo", "precio_min": "70000000"})
        self.assertEqual(len(resp.context["inmuebles"]), 0)

    # --- ficha PDF ---
    def html_ficha(self, inm):
        from django.template.loader import render_to_string
        from . import ficha
        ctx = ficha.contexto_ficha(inm)
        ctx.update({"foto_principal": None, "filas_miniaturas": []})
        return render_to_string("inmuebles/ficha_pdf.html", ctx)

    def test_ficha_con_varias_ofertas(self):
        self.crear(self.dos_ofertas())
        html = self.html_ficha(Inmueble.objects.get())
        self.assertIn("Desde:", html)
        self.assertIn("$ 74.000.000", html)
        self.assertIn("2 opciones disponibles", html)
        self.assertIn("Ofertas comerciales", html)
        self.assertIn("Opción 1 (Arriendo)", html)
        self.assertIn("Ventajas destacadas", html)
        self.assertIn("4.000 m2", html)
        self.assertIn("$ 29.925.000", html)

    def test_ficha_con_una_oferta(self):
        self.crear({**self.base(), **oferta("450000000", "venta")})
        html = self.html_ficha(Inmueble.objects.get())
        self.assertIn("Precio de venta:", html)
        self.assertIn("Oferta comercial", html)
        self.assertNotIn("IVA 19 %", html)

    def test_ficha_pdf_se_genera_con_ofertas(self):
        self.crear(self.dos_ofertas())
        inm = Inmueble.objects.get()
        resp = self.client.get(reverse("inmueble_ficha_pdf", args=[inm.pk]))
        self.assertTrue(resp.content.startswith(b"%PDF"))

    # --- campos de bodega ---
    def test_campos_de_bodega_en_formulario_detalle_y_ficha(self):
        from .forms import InmuebleForm
        seccion = {s["titulo"]: s for s in InmuebleForm().secciones()}["Datos de bodega y local"]
        nombres = [c.name for c in seccion["campos"]]
        for campo in ["area_libre", "area_administrativa", "capacidad_piso", "muelles", "entradas_nivel"]:
            self.assertIn(campo, nombres)
        self.crear({**self.base(area_libre="8000", area_administrativa="800", capacidad_piso="8",
                                muelles="16", entradas_nivel="2", kva="50", altura="11"),
                    **oferta("205000000", "arriendo")})
        inm = Inmueble.objects.get()
        self.assertEqual(inm.muelles, 16)
        detalle = self.client.get(reverse("inmueble_detail", args=[inm.pk]))
        self.assertContains(detalle, "Capacidad de piso (ton/m²)")
        self.assertContains(detalle, "8.000")
        html = self.html_ficha(inm)
        self.assertIn("Muelles", html)
        self.assertIn("Entradas a nivel", html)
        self.assertIn("Capacidad de piso (ton/m2)", html)

    def test_valores_internos_no_estan_en_la_ficha(self):
        from .forms import InmuebleForm
        seccion = {s["titulo"]: s for s in InmuebleForm().secciones()}["Valores internos"]
        self.assertEqual([c.name for c in seccion["campos"]], ["margen_negociacion", "impuesto_predial"])


class MigracionOfertasTests(TestCase):
    def test_crea_oferta_inicial_con_el_valor_existente(self):
        import importlib
        from django.apps import apps
        modulo = [m for m in __import__("inmuebles.migrations", fromlist=["*"]).__path__]
        import pkgutil
        nombre = next(n for _, n, _ in pkgutil.iter_modules(modulo) if n.endswith("ofertas_y_datos_bodega"))
        migracion = importlib.import_module(f"inmuebles.migrations.{nombre}")
        p = Propietario.objects.create(nombre_completo="M", numero_identificacion="1", numero_contacto="1")
        arrendado = Inmueble.objects.create(propietario=p, ciudad="C", tipo_inmueble="bodega", direccion="A",
                                            valor_transaccion=205000000, valor_administracion=5000000,
                                            estado="arrendado")
        vendible = Inmueble.objects.create(propietario=p, ciudad="C", tipo_inmueble="casa", direccion="B",
                                           valor_transaccion=450000000)
        migracion.crear_oferta_inicial(apps, None)
        migracion.crear_oferta_inicial(apps, None)  # ejecutarla dos veces no duplica
        o1 = arrendado.ofertas.get()
        self.assertEqual((o1.modalidad, o1.valor, o1.valor_administracion, o1.titulo),
                         ("arriendo", 205000000, 5000000, "Oferta 1"))
        self.assertEqual(vendible.ofertas.get().modalidad, "venta")
