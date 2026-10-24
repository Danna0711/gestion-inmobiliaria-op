"""Ofertas comerciales por inmueble y datos adicionales de bodega.

A cada inmueble ya registrado se le crea su "Oferta 1" con el valor y la
administración que tenía, para que no se pierda ninguna información.
"""
import django.db.models.deletion
from django.db import migrations, models


def crear_oferta_inicial(apps, schema_editor):
    Inmueble = apps.get_model("inmuebles", "Inmueble")
    OfertaComercial = apps.get_model("inmuebles", "OfertaComercial")
    for inmueble in Inmueble.objects.all():
        if not OfertaComercial.objects.filter(inmueble=inmueble).exists():
            OfertaComercial.objects.create(
                inmueble=inmueble,
                titulo="Oferta 1",
                modalidad="arriendo" if inmueble.estado == "arrendado" else "venta",
                valor=inmueble.valor_transaccion,
                valor_administracion=inmueble.valor_administracion,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("inmuebles", "0004_poliza_archivo"),
    ]

    operations = [
        migrations.AddField(
            model_name="inmueble",
            name="area_libre",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="inmueble",
            name="area_administrativa",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="inmueble",
            name="capacidad_piso",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="inmueble",
            name="muelles",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="inmueble",
            name="entradas_nivel",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="OfertaComercial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(blank=True, max_length=100, null=True)),
                ("modalidad", models.CharField(choices=[("venta", "Venta"), ("arriendo", "Arriendo")], max_length=10)),
                ("area", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=14)),
                ("aplica_iva", models.BooleanField(default=False)),
                ("valor_administracion", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("ventajas", models.TextField(blank=True, null=True)),
                (
                    "inmueble",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ofertas",
                        to="inmuebles.inmueble",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.RunPython(crear_oferta_inicial, migrations.RunPython.noop),
    ]
