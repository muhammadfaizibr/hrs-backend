# Generated by Django 5.1.3 on 2024-12-02 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='sentiment',
            field=models.CharField(choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')], default='', max_length=50, verbose_name='Sentiment Type'),
        ),
    ]
