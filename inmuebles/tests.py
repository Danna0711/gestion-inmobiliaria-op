from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Inmueble, Propietario


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
            "estado": "disponible", "direccion": "Zona Industrial 5", "valor_transaccion": "850000000",
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
            "direccion": "Centro 1", "valor_transaccion": "100000000", "uso_suelo": "Comercio de ropa",
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
                "estado": "disponible", "direccion": f"Dir {tipo}", "valor_transaccion": "1000",
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
            "estado": "disponible", "direccion": "Sin nota", "valor_transaccion": "1000",
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
            return Inmueble.objects.create(**datos)

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
