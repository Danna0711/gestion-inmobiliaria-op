"""Formato de valores y etiquetas en español, independiente de la configuración de idioma."""
from decimal import Decimal

ETIQUETAS = {
    # Propietario
    "nombre_completo": "Nombre completo",
    "numero_identificacion": "Número de identificación",
    "numero_contacto": "Número de contacto",
    "correo": "Correo electrónico",
    # Inmueble
    "propietario": "Propietario",
    "id_captacion": "ID de captación",
    "fecha_captacion": "Fecha de captación",
    "nombre_agente": "Nombre del agente",
    "ciudad": "Ciudad",
    "tipo_inmueble": "Tipo de inmueble",
    "estado": "Estado",
    "departamento": "Departamento",
    "barrio": "Barrio",
    "direccion": "Dirección",
    "nombre_conjunto": "Nombre del conjunto",
    "estrato": "Estrato",
    "piso": "Piso",
    "anos_construccion": "Años de construcción",
    "remodelado": "Remodelado",
    "area_construida": "Área construida (m²)",
    "area_privada": "Área privada (m²)",
    "garajes": "Garajes",
    "depositos": "Depósitos",
    "habitaciones": "Habitaciones",
    "banos": "Baños",
    "servicio_agua": "Servicio de agua",
    "servicio_luz": "Servicio de luz",
    "servicio_gas": "Servicio de gas",
    "aptos_por_piso": "Apartamentos por piso",
    "total_unidades": "Total de unidades",
    "no_pisos": "Número de pisos",
    "ascensores": "Ascensores",
    "vigilancia": "Vigilancia",
    "parqueadero_visitantes": "Parqueadero de visitantes",
    "areas_comunes": "Áreas comunes",
    "club_house": "Club house",
    "valor_transaccion": "Valor de la transacción",
    "valor_administracion": "Valor de administración",
    "margen_negociacion": "Margen de negociación",
    "impuesto_predial": "Impuesto predial",
    "matricula_1": "Matrícula inmobiliaria 1",
    "matricula_2": "Matrícula inmobiliaria 2",
    "kva": "KVA (capacidad eléctrica)",
    "altura": "Altura (m)",
    "uso_suelo": "Uso de suelo",
    "informacion_adicional": "Información adicional",
    # Documento
    "tipo_documento": "Tipo de documento",
    "archivo": "Archivo",
    # Póliza
    "nombre_poliza": "Nombre de la póliza",
    "valor": "Valor de la póliza",
    "fecha_vencimiento": "Fecha de vencimiento",
    "numero_contrato": "Número de contrato",
}

CAMPOS_DINERO = {"valor_transaccion", "valor_administracion", "margen_negociacion", "impuesto_predial"}


def _miles(entero):
    return f"{entero:,}".replace(",", ".")


def pesos(valor):
    """2300000000 -> '$ 2.300.000.000'"""
    if valor in (None, ""):
        return ""
    return "$ " + _miles(int(round(Decimal(valor))))


def numero(valor):
    """Decimal('85.50') -> '85,5'; Decimal('1200.00') -> '1.200'"""
    if valor in (None, ""):
        return ""
    texto = format(Decimal(valor).normalize(), "f")
    entero, _, decimales = texto.partition(".")
    resultado = _miles(int(entero))
    return resultado + ("," + decimales if decimales else "")


def fecha(valor):
    """date(2026, 10, 16) -> '16/10/2026'"""
    return valor.strftime("%d/%m/%Y") if valor else ""


# ------------------------------ PÓLIZAS ------------------------------

DIAS_AVISO_POLIZA = 30  # una póliza "por vencer" es la que vence en 30 días o menos


def estado_poliza(fecha_vencimiento, hoy):
    """Devuelve (estado, dias, texto). estado: 'vencida', 'por_vencer' o 'vigente'.

    dias es la diferencia entre la fecha de vencimiento y hoy (negativo si ya venció).
    """
    dias = (fecha_vencimiento - hoy).days
    if dias < 0:
        n = -dias
        return "vencida", dias, "Vencida hace 1 día" if n == 1 else f"Vencida hace {n} días"
    if dias == 0:
        return "por_vencer", dias, "Vence hoy"
    if dias <= DIAS_AVISO_POLIZA:
        return "por_vencer", dias, "Vence en 1 día" if dias == 1 else f"Vence en {dias} días"
    return "vigente", dias, "Vigente"
