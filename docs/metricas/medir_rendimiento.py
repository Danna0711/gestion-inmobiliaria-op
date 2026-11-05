"""
Medición local de rendimiento del Sistema de Gestión Inmobiliaria OP.

Uso (desde la carpeta del proyecto, con el entorno virtual activo):
    python docs/metricas/medir_rendimiento.py

Crea una base de datos y una carpeta de archivos TEMPORALES (no toca db.sqlite3
ni media/), carga datos de prueba (100 inmuebles, 25 propietarios, ofertas,
3 fotos por inmueble y pólizas), mide cada vista principal varias veces y guarda
los resultados en docs/metricas/metricas_locales.json.

Variables opcionales: N_INM (inmuebles a crear, 100) y REP (repeticiones, 30).
"""

import os, sys, time, statistics, random, json, platform, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_inmobiliaria.settings"
TMP = Path(tempfile.mkdtemp(prefix="medicion_op_"))
from django.conf import settings

settings.DEBUG = False
settings.ALLOWED_HOSTS = ["testserver", "localhost"]
settings.DATABASES["default"]["NAME"] = TMP / "medicion.sqlite3"
settings.MEDIA_ROOT = TMP / "media"
import django

django.setup()
from django.core.management import call_command
from django.test import Client
from django.test.utils import CaptureQueriesContext, setup_test_environment
from django.db import connection
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from PIL import Image, ImageFilter
from inmuebles.models import Propietario, Inmueble, OfertaComercial, Fotografia, Documento, Poliza

setup_test_environment()  # permite capturar el contexto de plantillas sin cambiar nada más
N_INM = int(os.environ.get("N_INM", 100))
REP = int(os.environ.get("REP", 30))
random.seed(7)
call_command("migrate", verbosity=0)
U = get_user_model().objects.create_user("medicion", password="Clave-segura-2026")

# Fotos de prueba: 3 imágenes 1920x1280 (el tamaño máximo que deja el sistema)
fotos_dir = settings.MEDIA_ROOT / "inmuebles" / "fotos"
fotos_dir.mkdir(parents=True, exist_ok=True)
rutas = []
for i in range(3):
    im = (
        Image.effect_noise((480, 320), 60)
        .convert("RGB")
        .resize((1920, 1280))
        .filter(ImageFilter.GaussianBlur(2))
    )
    im = Image.blend(
        im, Image.new("RGB", im.size, [(120, 140, 90), (170, 150, 100), (90, 110, 140)][i]), 0.55
    )
    p = fotos_dir / f"medicion_{i}.jpg"
    im.save(p, "JPEG", quality=85)
    rutas.append(f"inmuebles/fotos/medicion_{i}.jpg")
peso_foto = sum(os.path.getsize(fotos_dir / f"medicion_{i}.jpg") for i in range(3)) / 3

ciudades = ["Bogotá", "Chía", "Cajicá", "Medellín", "Cali"]
tipos = ["apartamento", "casa", "bodega", "local", "oficina", "lote"]
props = [
    Propietario.objects.create(
        nombre_completo=f"Propietario {i}",
        numero_identificacion=str(1000000 + i),
        numero_contacto="3000000000",
    )
    for i in range(25)
]
for i in range(N_INM):
    inm = Inmueble.objects.create(
        propietario=random.choice(props),
        ciudad=random.choice(ciudades),
        tipo_inmueble=random.choice(tipos),
        direccion=f"Calle {i} # {i%40}-{i%90}",
        barrio=f"Barrio {i%12}",
        habitaciones=random.randint(0, 5),
        banos=random.randint(1, 4),
        area_construida=random.randint(40, 900),
        valor_transaccion=random.randint(150, 3000) * 1_000_000,
        estrato=random.randint(1, 6),
        informacion_adicional="Inmueble de prueba para medición de rendimiento. " * 4,
    )
    for k in range(random.randint(1, 3)):
        OfertaComercial.objects.create(
            inmueble=inm,
            modalidad=random.choice(["venta", "arriendo"]),
            valor=random.randint(2, 3000) * 1_000_000,
            titulo=f"Oferta {k+1}",
            descripcion="Descripción de la oferta.",
            ventajas="Buena ubicación",
        )
    for r in rutas:
        Fotografia.objects.create(inmueble=inm, archivo=r, etiqueta="Fachada")
    if i % 3 == 0:
        Poliza.objects.create(
            inmueble=inm,
            nombre_poliza="Arrendamiento",
            valor=1_500_000,
            fecha_vencimiento=date.today() + timedelta(days=random.randint(-10, 90)),
        )

c = Client()
c.force_login(U)
ejemplo = Inmueble.objects.order_by("id")[N_INM // 2]
casos = [
    ("Ingreso (formulario de login)", "get", "/accounts/login/", None, False),
    ("Listado de inmuebles (pág. 1)", "get", reverse("inmueble_list"), None, True),
    (
        "Listado con filtros combinados",
        "get",
        reverse("inmueble_list")
        + "?q=Calle&ciudad=Bogotá&modalidad=venta&precio_min=100000000&precio_max=2000000000&orden=precio_desc",
        None,
        True,
    ),
    ("Detalle de inmueble", "get", reverse("inmueble_detail", args=[ejemplo.pk]), None, True),
    ("Formulario nuevo inmueble", "get", reverse("inmueble_create"), None, True),
    ("Listado de propietarios", "get", reverse("propietario_list"), None, True),
    ("Alertas de pólizas", "get", reverse("poliza_alertas"), None, True),
    ("Ficha PDF (3 fotos)", "get", reverse("inmueble_ficha_pdf", args=[ejemplo.pk]), None, True),
]
res = []
for nombre, metodo, url, datos, auth in casos:
    cli = c if auth else Client()
    for _ in range(3):
        cli.get(url)  # calentamiento
    tiempos = []
    qn = None
    tam = None
    st = None
    reps = REP if "PDF" not in nombre else max(10, REP // 3)
    for _ in range(reps):
        with CaptureQueriesContext(connection) as ctx:
            t0 = time.perf_counter()
            r = cli.get(url)
            t = (time.perf_counter() - t0) * 1000
        tiempos.append(t)
        qn = len(ctx.captured_queries)
        tam = len(r.content)
        st = r.status_code
    tiempos.sort()
    p95 = tiempos[min(len(tiempos) - 1, int(round(0.95 * len(tiempos))) - 1)]
    res.append(
        dict(
            vista=nombre,
            url=url,
            estado=st,
            n=reps,
            mediana_ms=round(statistics.median(tiempos), 1),
            p95_ms=round(p95, 1),
            max_ms=round(max(tiempos), 1),
            consultas_sql=qn,
            tamano_kb=round(tam / 1024, 1),
        )
    )

conteos = dict(
    inmuebles=Inmueble.objects.count(),
    propietarios=Propietario.objects.count(),
    ofertas=OfertaComercial.objects.count(),
    fotos=Fotografia.objects.count(),
    polizas=Poliza.objects.count(),
)
# Registro (POST) de un inmueble con una oferta
tiempos = []
qn = None
for i in range(REP):
    datos = {
        "propietario": props[0].pk,
        "ciudad": "Bogotá",
        "tipo_inmueble": "apartamento",
        "estado": "disponible",
        "direccion": f"Carrera medición {i}",
        "habitaciones": 2,
        "banos": 1,
        "garajes": 1,
        "depositos": 0,
        "ofertas-TOTAL_FORMS": "1",
        "ofertas-INITIAL_FORMS": "0",
        "ofertas-MIN_NUM_FORMS": "1",
        "ofertas-MAX_NUM_FORMS": "1000",
        "ofertas-0-modalidad": "venta",
        "ofertas-0-valor": "450000000",
    }
    with CaptureQueriesContext(connection) as ctx:
        t0 = time.perf_counter()
        r = c.post(reverse("inmueble_create"), datos)
        tiempos.append((time.perf_counter() - t0) * 1000)
    assert r.status_code == 302, r.status_code
    qn = len(ctx.captured_queries)
tiempos.sort()
res.append(
    dict(
        vista="Registrar inmueble con 1 oferta (POST)",
        url=reverse("inmueble_create"),
        estado=302,
        n=REP,
        mediana_ms=round(statistics.median(tiempos), 1),
        p95_ms=round(tiempos[int(round(0.95 * REP)) - 1], 1),
        max_ms=round(max(tiempos), 1),
        consultas_sql=qn,
        tamano_kb=0,
    )
)

entorno = dict(
    fecha=date.today().isoformat(),
    python=platform.python_version(),
    django=django.get_version(),
    so=platform.platform(),
    cpu=os.cpu_count(),
    **conteos,
    peso_promedio_foto_kb=round(peso_foto / 1024, 1),
    debug=settings.DEBUG,
)
salida = RAIZ / "docs" / "metricas" / "metricas_locales.json"
salida.parent.mkdir(parents=True, exist_ok=True)
json.dump(
    dict(entorno=entorno, resultados=res), open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1
)
import shutil

shutil.rmtree(TMP, ignore_errors=True)
print("Resultados guardados en", salida)
print(json.dumps(entorno, ensure_ascii=False))
for r in res:
    print(r)
