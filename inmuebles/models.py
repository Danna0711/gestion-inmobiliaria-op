# Create your models here.
from django.db import models


class Propietario(models.Model):
    nombre_completo = models.CharField(max_length=150)
    numero_identificacion = models.CharField(max_length=30, unique=True)
    numero_contacto = models.CharField(max_length=30)
    correo = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nombre_completo


class Inmueble(models.Model):
    TIPO_INMUEBLE_CHOICES = [
        ("casa", "Casa"),
        ("apartamento", "Apartamento"),
        ("bodega", "Bodega"),
        ("local", "Local"),
        ("lote", "Lote"),
        ("otro", "Otro"),
    ]
    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("reservado", "Reservado"),
        ("vendido", "Vendido"),
        ("arrendado", "Arrendado"),
    ]

    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name="inmuebles")

    id_captacion = models.CharField(max_length=30, blank=True, null=True)
    fecha_captacion = models.DateField(auto_now_add=True)
    nombre_agente = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100)
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")

    departamento = models.CharField(max_length=100, blank=True, null=True)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200)
    nombre_conjunto = models.CharField(max_length=150, blank=True, null=True)
    estrato = models.PositiveSmallIntegerField(blank=True, null=True)
    piso = models.PositiveSmallIntegerField(blank=True, null=True)
    anos_construccion = models.PositiveSmallIntegerField(blank=True, null=True)
    remodelado = models.BooleanField(default=False)
    area_construida = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    area_privada = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    garajes = models.PositiveSmallIntegerField(default=0)
    depositos = models.PositiveSmallIntegerField(default=0)
    habitaciones = models.PositiveSmallIntegerField(default=0)
    banos = models.PositiveSmallIntegerField(default=0)
    servicio_agua = models.BooleanField(default=False)
    servicio_luz = models.BooleanField(default=False)
    servicio_gas = models.BooleanField(default=False)

    aptos_por_piso = models.PositiveSmallIntegerField(blank=True, null=True)
    total_unidades = models.PositiveSmallIntegerField(blank=True, null=True)
    ascensores = models.BooleanField(default=False)
    no_pisos = models.PositiveSmallIntegerField(blank=True, null=True)
    vigilancia = models.CharField(max_length=100, blank=True, null=True)
    parqueadero_visitantes = models.CharField(max_length=100, blank=True, null=True)
    areas_comunes = models.TextField(blank=True, null=True)
    club_house = models.BooleanField(default=False)

    valor_transaccion = models.DecimalField(max_digits=14, decimal_places=2)
    valor_administracion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    margen_negociacion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    impuesto_predial = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    matricula_1 = models.CharField(max_length=50, blank=True, null=True)
    matricula_2 = models.CharField(max_length=50, blank=True, null=True)

    kva = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    altura = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    uso_suelo = models.CharField("Uso de suelo", max_length=100, blank=True, null=True)
    informacion_adicional = models.TextField("Información adicional", blank=True, null=True)
    # --- Datos adicionales de bodega (y local) ---
    area_libre = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    area_administrativa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    capacidad_piso = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    muelles = models.PositiveSmallIntegerField(blank=True, null=True)
    entradas_nivel = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_inmueble_display()} - {self.direccion}"


class Fotografia(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="fotografias")
    archivo = models.ImageField(upload_to="inmuebles/fotos/")
    etiqueta = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Foto de {self.inmueble} ({self.etiqueta or 'sin etiqueta'})"


class Documento(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ("escritura", "Escritura"),
        ("certificado_tradicion", "Certificado de tradición"),
        ("impuesto_predial", "Impuesto predial"),
        ("planos", "Planos"),
        ("contrato_consignacion", "Contrato de consignación"),
        ("otro", "Otro"),
    ]

    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.CharField(max_length=30, choices=TIPO_DOCUMENTO_CHOICES)
    archivo = models.FileField(upload_to="inmuebles/documentos/")

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.inmueble}"


class Poliza(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="polizas")
    nombre_poliza = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()
    numero_contrato = models.CharField(max_length=50, blank=True, null=True)
    archivo = models.FileField(upload_to="inmuebles/polizas/", blank=True, null=True)

    def __str__(self):
        return f"{self.nombre_poliza} - {self.inmueble}"

    
class OfertaComercial(models.Model):
    MODALIDAD_CHOICES = [("venta", "Venta"), ("arriendo", "Arriendo")]

    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="ofertas")
    titulo = models.CharField(max_length=100, blank=True, null=True)
    modalidad = models.CharField(max_length=10, choices=MODALIDAD_CHOICES)
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    aplica_iva = models.BooleanField(default=False)
    valor_administracion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    ventajas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.titulo or 'Oferta'} - {self.inmueble}"