from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_academico', '0003_aulavirtual_catedra'),
    ]

    operations = [
        migrations.AddField(
            model_name='aulavirtual',
            name='ciclo_escolar',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
