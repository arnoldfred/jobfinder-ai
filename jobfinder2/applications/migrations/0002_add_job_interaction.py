from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0002_add_search_alert'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobInteraction',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('action',     models.CharField(choices=[('viewed','Vue'),('saved','Sauvegardée'),('applied','Candidature envoyée'),('dismissed','Pas intéressé')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user',       models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_interactions', to=settings.AUTH_USER_MODEL)),
                ('job',        models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='jobs.job')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='jobinteraction',
            constraint=models.UniqueConstraint(fields=('user', 'job', 'action'), name='unique_user_job_action'),
        ),
        migrations.AddIndex(
            model_name='jobinteraction',
            index=models.Index(fields=['user', 'action', 'created_at'], name='jobinteract_user_action_idx'),
        ),
    ]
