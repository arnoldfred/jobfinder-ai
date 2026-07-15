from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='skill',
            name='level',
            field=models.CharField(
                blank=True, default='',
                choices=[
                    ('', 'Niveau non précisé'),
                    ('debutant', 'Débutant (A1/A2)'),
                    ('intermediaire', 'Intermédiaire (B1/B2)'),
                    ('avance', 'Avancé (C1)'),
                    ('bilingue', 'Bilingue / Natif (C2)'),
                ],
                max_length=20
            ),
        ),
    ]
