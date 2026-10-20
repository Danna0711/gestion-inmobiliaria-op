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
