from django.db import models


class Propietario(models.Model):
    nombre_completo = models.CharField(max_length=150, verbose_name="Nombre completo")
    numero_identificacion = models.CharField(max_length=30, unique=True, verbose_name="Número de identificación")
    numero_contacto = models.CharField(max_length=30, verbose_name="Número de contacto")
    correo = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")

    class Meta:
        verbose_name = "propietario"
        verbose_name_plural = "propietarios"
        ordering = ["nombre_completo"]

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

    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name="inmuebles", verbose_name="Propietario")

    id_captacion = models.CharField(max_length=30, blank=True, null=True, verbose_name="ID de captación")
    fecha_captacion = models.DateField(auto_now_add=True, verbose_name="Fecha de captación")
    nombre_agente = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del agente")
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad")
    tipo_inmueble = models.CharField(max_length=20, choices=TIPO_INMUEBLE_CHOICES, verbose_name="Tipo de inmueble")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible", verbose_name="Estado")

    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    barrio = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barrio")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    nombre_conjunto = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre del conjunto")
    estrato = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Estrato")
    piso = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Piso")
    anos_construccion = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Años de construcción")
    remodelado = models.BooleanField(default=False, verbose_name="Remodelado")
    area_construida = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Área construida (m²)")
    area_privada = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Área privada (m²)")
    garajes = models.PositiveSmallIntegerField(default=0, verbose_name="Garajes")
    depositos = models.PositiveSmallIntegerField(default=0, verbose_name="Depósitos")
    habitaciones = models.PositiveSmallIntegerField(default=0, verbose_name="Habitaciones")
    banos = models.PositiveSmallIntegerField(default=0, verbose_name="Baños")
    servicio_agua = models.BooleanField(default=False, verbose_name="Servicio de agua")
    servicio_luz = models.BooleanField(default=False, verbose_name="Servicio de luz")
    servicio_gas = models.BooleanField(default=False, verbose_name="Servicio de gas")

    aptos_por_piso = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Apartamentos por piso")
    total_unidades = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Total de unidades")
    ascensores = models.BooleanField(default=False, verbose_name="Ascensores")
    no_pisos = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Número de pisos")
    vigilancia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Vigilancia")
    parqueadero_visitantes = models.CharField(max_length=100, blank=True, null=True, verbose_name="Parqueadero de visitantes")
    areas_comunes = models.TextField(blank=True, null=True, verbose_name="Áreas comunes")
    club_house = models.BooleanField(default=False, verbose_name="Club house")

    valor_transaccion = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Valor de la transacción")
    valor_administracion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor de administración")
    margen_negociacion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Margen de negociación")
    impuesto_predial = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Impuesto predial")

    matricula_1 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Matrícula inmobiliaria 1")
    matricula_2 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Matrícula inmobiliaria 2")

    kva = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="KVA (capacidad eléctrica)")
    altura = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Altura (m)")
    uso_suelo = models.CharField("Uso de suelo", max_length=100, blank=True, null=True)
    informacion_adicional = models.TextField("Información adicional", blank=True, null=True)
    # --- Datos adicionales de bodega (y local) ---
    area_libre = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Área libre (m²)")
    area_administrativa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Área administrativa (m²)")
    capacidad_piso = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Capacidad de piso (ton/m²)")
    muelles = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Muelles")
    entradas_nivel = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Entradas a nivel")

    class Meta:
        verbose_name = "inmueble"
        verbose_name_plural = "inmuebles"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.get_tipo_inmueble_display()} - {self.direccion}"


class Fotografia(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="fotografias", verbose_name="Inmueble")
    archivo = models.ImageField(upload_to="inmuebles/fotos/", verbose_name="Fotografía")
    etiqueta = models.CharField(max_length=50, blank=True, null=True, verbose_name="Etiqueta")

    class Meta:
        verbose_name = "fotografía"
        verbose_name_plural = "fotografías"
        ordering = ["id"]

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

    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="documentos", verbose_name="Inmueble")
    tipo_documento = models.CharField(max_length=30, choices=TIPO_DOCUMENTO_CHOICES, verbose_name="Tipo de documento")
    archivo = models.FileField(upload_to="inmuebles/documentos/", verbose_name="Archivo")

    class Meta:
        verbose_name = "documento legal"
        verbose_name_plural = "documentos legales"
        ordering = ["tipo_documento", "id"]

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.inmueble}"


class Poliza(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="polizas", verbose_name="Inmueble")
    nombre_poliza = models.CharField(max_length=100, verbose_name="Nombre de la póliza")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor de la póliza")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    numero_contrato = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de contrato")
    archivo = models.FileField(upload_to="inmuebles/polizas/", blank=True, null=True, verbose_name="Documento de la póliza")

    class Meta:
        verbose_name = "póliza"
        verbose_name_plural = "pólizas"
        ordering = ["fecha_vencimiento"]

    def __str__(self):
        return f"{self.nombre_poliza} - {self.inmueble}"


class OfertaComercial(models.Model):
    MODALIDAD_CHOICES = [("venta", "Venta"), ("arriendo", "Arriendo")]

    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name="ofertas", verbose_name="Inmueble")
    titulo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre de la oferta")
    modalidad = models.CharField(max_length=10, choices=MODALIDAD_CHOICES, verbose_name="Modalidad")
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Área ofrecida (m²)")
    valor = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Precio de venta o canon mensual")
    aplica_iva = models.BooleanField(default=False, verbose_name="Aplica IVA (19 %)")
    valor_administracion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Administración")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción general")
    ventajas = models.TextField(blank=True, null=True, verbose_name="Ventajas destacadas")

    class Meta:
        verbose_name = "oferta comercial"
        verbose_name_plural = "ofertas comerciales"
        ordering = ["id"]

    def __str__(self):
        return f"{self.titulo or 'Oferta'} - {self.inmueble}"