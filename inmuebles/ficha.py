"""Ficha del inmueble en PDF para compartir con los clientes (RF15).

La ficha muestra solo información comercial. Los datos internos de la empresa
(propietario, matrículas, margen de negociación, impuesto predial, ID de
captación y estado) NO se incluyen.
"""
import base64
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.template.loader import render_to_string
from django.utils import timezone
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa

from . import formato

# Datos de contacto de la inmobiliaria que aparecen al pie de la ficha.
# Completa el teléfono y el correo; si se dejan vacíos, no se muestran.
EMPRESA = {
    "nombre": "OP Agente Inmobiliario",
    "telefono": "311 553 7531",
    "correo": "op.agenteinmobiliario@gmail.com",
}

MAX_FOTOS = 7  # 1 foto principal + hasta 6 miniaturas

# Marca de agua: el logo de la inmobiliaria, muy tenue, en el centro de cada página
# (también queda sobre las fotos). Si el archivo no existe, la ficha sale sin marca de agua.
MARCA_DE_AGUA = Path(__file__).resolve().parent / "static" / "inmuebles" / "marca_agua.png"
OPACIDAD_MARCA = 0.22  # 0 = invisible, 1 = colores completos. Sube o baja este número para ajustarla.
ANCHO_MARCA = 0.80     # proporción del ancho de la página que ocupa el logo

# Logo de la inmobiliaria para el encabezado. Si el archivo no existe, la ficha sale sin logo.
LOGO = Path(__file__).resolve().parent / "static" / "inmuebles" / "logo_op.png"

# Secciones de la ficha: solo se muestran los campos con valor
SECCIONES_FICHA = [
    ("Ubicación", ["direccion", "barrio", "ciudad", "departamento", "nombre_conjunto"]),
    (
        "Características",
        [
            "estrato", "piso", "anos_construccion", "remodelado", "area_construida",
            "area_privada", "habitaciones", "banos", "garajes", "depositos",
        ],
    ),
    ("Servicios", ["servicio_agua", "servicio_luz", "servicio_gas"]),
    (
        "Zonas comunes",
        [
            "aptos_por_piso", "total_unidades", "no_pisos", "ascensores", "vigilancia",
            "parqueadero_visitantes", "areas_comunes", "club_house",
        ],
    ),
    (
        "Datos técnicos",
        [
            "kva", "altura", "uso_suelo", "area_libre", "area_administrativa",
            "capacidad_piso", "muelles", "entradas_nivel",
        ],
    ),
]

# Campos que nunca deben aparecer en la ficha (se verifica en las pruebas)
CAMPOS_INTERNOS = {
    "propietario", "id_captacion", "nombre_agente", "estado", "matricula_1", "matricula_2",
    "margen_negociacion", "impuesto_predial",
}

SERVICIOS = {"servicio_agua", "servicio_luz", "servicio_gas"}


def _valor_legible(inmueble, campo):
    """Devuelve el valor listo para mostrar, o None si no debe mostrarse."""
    f = inmueble._meta.get_field(campo)
    valor = getattr(inmueble, campo)
    if valor in (None, ""):
        return None
    if isinstance(valor, bool):
        # Los servicios se muestran siempre (Sí/No); los demás sí/no solo cuando son "Sí"
        if campo in SERVICIOS:
            return "Sí" if valor else "No"
        return "Sí" if valor else None
    if f.choices:
        return getattr(inmueble, f"get_{campo}_display")()
    if campo in formato.CAMPOS_DINERO:
        return formato.pesos(valor)
    if isinstance(valor, Decimal):
        return formato.numero(valor)
    if isinstance(valor, date):
        return formato.fecha(valor)
    return str(valor)


def contexto_ficha(inmueble, usuario=None):
    secciones = []
    for titulo, campos in SECCIONES_FICHA:
        filas = []
        for campo in campos:
            valor = _valor_legible(inmueble, campo)
            if valor is not None:
                etiqueta = formato.ETIQUETAS.get(campo, campo)
                # la fuente del PDF no tiene el símbolo ², por eso se escribe m2
                filas.append((etiqueta.replace("m²", "m2"), valor))
        if filas:
            secciones.append({"titulo": titulo, "filas": filas})

    lugar = ", ".join(p for p in [inmueble.barrio, inmueble.ciudad] if p)

    # Ofertas comerciales (la fuente del PDF no tiene ², por eso m2)
    registros = list(inmueble.ofertas.all())
    ofertas = []
    for n, oferta in enumerate(registros, 1):
        resumen = formato.resumen_oferta(oferta, n)
        resumen["area"] = resumen["area"].replace("m²", "m2")
        ofertas.append(resumen)

    # Precio del encabezado
    if len(registros) == 1:
        etiqueta_precio = ofertas[0]["etiqueta_valor"]
        valor = ofertas[0]["valor"]
        administracion = ofertas[0]["administracion"]
        nota_precio = ""
    elif len(registros) > 1:
        etiqueta_precio = "Desde"
        valor = formato.pesos(min(o.valor for o in registros))
        administracion = ""
        nota_precio = f"{len(registros)} opciones disponibles"
    else:  # inmueble sin ofertas registradas: se usa el valor guardado en el inmueble
        etiqueta_precio = ""
        valor = formato.pesos(inmueble.valor_transaccion)
        administracion = formato.pesos(inmueble.valor_administracion)
        nota_precio = ""

    return {
        "inmueble": inmueble,
        "titulo": f"{inmueble.get_tipo_inmueble_display()} en {lugar}",
        "etiqueta_precio": etiqueta_precio,
        "valor": valor,
        "administracion": administracion,
        "nota_precio": nota_precio,
        "ofertas": ofertas,
        "secciones": secciones,
        "informacion_adicional": inmueble.informacion_adicional or "",
        "fotos": list(inmueble.fotografias.all()[:MAX_FOTOS]),
        "empresa": EMPRESA,
        "fecha": formato.fecha(timezone.localdate()),
    }


def _foto_incrustada(origen, ancho, alto):
    """Recorta y reduce la foto (sin deformarla) y la devuelve como imagen incrustada (data URI).

    Así el PDF no queda pesado y no se usan archivos temporales.
    """
    with Image.open(origen) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, (ancho, alto), Image.LANCZOS)
        memoria = io.BytesIO()
        img.save(memoria, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(memoria.getvalue()).decode("ascii")


def _logo_incrustado():
    """Devuelve el logo como imagen incrustada, o None si no está disponible."""
    try:
        with Image.open(LOGO) as img:
            img = img.convert("RGB")
            img.thumbnail((300, 160), Image.LANCZOS)  # el logo se imprime a 150 x 80 puntos
            memoria = io.BytesIO()
            img.save(memoria, "JPEG", quality=88, optimize=True)
    except (OSError, ValueError):
        return None
    return "data:image/jpeg;base64," + base64.b64encode(memoria.getvalue()).decode("ascii")


def generar_pdf(inmueble, usuario=None):
    """Devuelve los bytes del PDF de la ficha. Lanza RuntimeError si no se pudo generar."""
    ctx = contexto_ficha(inmueble, usuario)
    fotos = []
    for i, foto in enumerate(ctx["fotos"]):
        # Tamaños pensados para que se vean nítidas impresas sin que el PDF pese de más
        tamano = (960, 640) if i == 0 else (400, 300)
        try:
            src = _foto_incrustada(foto.archivo.path, *tamano)
        except (OSError, ValueError):
            continue  # si un archivo falta o está dañado, se omite esa foto
        fotos.append({"src": src, "etiqueta": foto.etiqueta or ""})
    ctx["foto_principal"] = fotos[0] if fotos else None
    miniaturas = fotos[1:]
    ctx["filas_miniaturas"] = [miniaturas[i:i + 3] for i in range(0, len(miniaturas), 3)]
    ctx["fotos_incluidas"] = len(fotos)
    ctx["logo"] = _logo_incrustado()

    html = render_to_string("inmuebles/ficha_pdf.html", ctx)
    salida = io.BytesIO()
    resultado = pisa.CreatePDF(html, dest=salida, encoding="utf-8")
    if resultado.err:
        raise RuntimeError("No se pudo generar la ficha en PDF.")
    return _aplicar_marca_de_agua(salida.getvalue())


def _pagina_marca_de_agua(ancho, alto):
    """Crea una página transparente con el logo tenue en el centro."""
    with Image.open(MARCA_DE_AGUA) as img:
        logo = img.convert("RGBA")
    transparencia = logo.getchannel("A").point(lambda v: int(v * OPACIDAD_MARCA))
    logo.putalpha(transparencia)
    w = ancho * ANCHO_MARCA
    h = w * logo.height / logo.width
    memoria = io.BytesIO()
    lienzo = canvas.Canvas(memoria, pagesize=(ancho, alto))
    lienzo.drawImage(ImageReader(logo), (ancho - w) / 2, (alto - h) / 2, w, h, mask="auto")
    lienzo.save()
    return PdfReader(io.BytesIO(memoria.getvalue())).pages[0]


def _aplicar_marca_de_agua(pdf):
    """Superpone la marca de agua en todas las páginas del PDF."""
    if OPACIDAD_MARCA <= 0 or not MARCA_DE_AGUA.exists():
        return pdf
    lector = PdfReader(io.BytesIO(pdf))
    escritor = PdfWriter()
    marcas = {}  # una sola marca por tamaño de página, compartida por todas las páginas
    for pagina in lector.pages:
        tamano = (float(pagina.mediabox.width), float(pagina.mediabox.height))
        if tamano not in marcas:
            marcas[tamano] = _pagina_marca_de_agua(*tamano)
        pagina.merge_page(marcas[tamano])
        escritor.add_page(pagina)
    for pagina in escritor.pages:
        pagina.compress_content_streams()  # mantiene el PDF liviano
    escritor.compress_identical_objects()
    salida = io.BytesIO()
    escritor.write(salida)
    return salida.getvalue()
