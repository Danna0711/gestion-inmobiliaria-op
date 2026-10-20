from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inmuebles", "0002_inmueble_uso_suelo"),
    ]

    operations = [
        migrations.AddField(
            model_name="inmueble",
            name="informacion_adicional",
            field=models.TextField(blank=True, null=True, verbose_name="Información adicional"),
        ),
    ]
