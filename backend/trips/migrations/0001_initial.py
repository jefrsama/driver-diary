from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trip_id', models.CharField(max_length=64, unique=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment', models.CharField(choices=[('cash', 'Наличные'), ('card', 'Карта')], max_length=8)),
                ('commission', models.DecimalField(decimal_places=2, max_digits=12)),
            ],
            options={
                'ordering': ['start', 'trip_id'],
                'indexes': [models.Index(fields=['start'], name='trip_start_idx')],
            },
        ),
    ]
