# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-12 18:27
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicSchema',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_value', models.CharField(blank=True, max_length=100, null=True)),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='DynamicSchemaField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, validators=[django.core.validators.RegexValidator(b'^[\\w]+$', message=b'\xd0\x98\xd0\xbc\xd1\x8f \xd0\xbc\xd0\xbe\xd0\xb6\xd0\xb5\xd1\x82 \xd1\x81\xd0\xbe\xd0\xb4\xd0\xb5\xd1\x80\xd0\xb6\xd0\xb0\xd1\x82\xd1\x8c \xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbb\xd0\xb0\xd1\x82\xd0\xb8\xd0\xbd\xd1\x81\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b/\xd1\x86\xd0\xb8\xd1\x84\xd1\x80\xd1\x8b \xd0\xb8 \xd1\x81\xd0\xb8\xd0\xbc\xd0\xb2\xd0\xbe\xd0\xbb \xd0\xbf\xd0\xbe\xd0\xb4\xd1\x87\xd1\x91\xd1\x80\xd0\xba\xd0\xb8\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x8f.')], verbose_name='\u0418\u043c\u044f \u043f\u043e\u043b\u044f')),
                ('verbose_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u043f\u043e\u043b\u044f')),
                ('field_type', models.CharField(choices=[(b'IntegerField', '\u0426\u0435\u043b\u043e\u0435 \u0447\u0438\u0441\u043b\u043e'), (b'FloatField', '\u0414\u0440\u043e\u0431\u043d\u043e\u0435 \u0447\u0438\u0441\u043b\u043e'), (b'DecimalField', '\u0414\u0440\u043e\u0431\u043d\u043e\u0435 \u0447\u0438\u0441\u043b\u043e \u0441 \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u043d\u043e\u0439 \u0442\u043e\u0447\u043d\u043e\u0441\u0442\u044c\u044e'), (b'CharField', '\u0421\u0442\u0440\u043e\u043a\u0430 \u0442\u0435\u043a\u0441\u0442\u0430'), (b'TextField', '\u041c\u043d\u043e\u0433\u043e\u0441\u0442\u0440\u043e\u0447\u043d\u044b\u0439 \u0442\u0435\u043a\u0441\u0442'), (b'DateField', '\u0414\u0430\u0442\u0430'), (b'DateTimeField', '\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f'), (b'EmailField', 'Email')], help_text='\u041d\u0435 \u043c\u0435\u043d\u044f\u0439\u0442\u0435 \u0442\u0438\u043f \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f. \u042d\u0442\u043e \u043c\u043e\u0436\u0435\u0442 \u043f\u0440\u0438\u0432\u0435\u0441\u0442\u0438 \u043a \u043e\u0448\u0438\u0431\u043a\u0430\u043c \u0432 \u0440\u0430\u0431\u043e\u0442\u0435 \u0441\u0438\u0441\u0442\u0435\u043c\u044b.', max_length=100, verbose_name='\u0422\u0438\u043f \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f')),
                ('required', models.BooleanField(default=True, verbose_name='\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0435')),
                ('schema', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='dynamicmodel.DynamicSchema', verbose_name='\u041a\u043b\u0430\u0441\u0441 \u043e\u0431\u044a\u0435\u043a\u0442\u0430')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dynamicschemafield',
            unique_together=set([('schema', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='dynamicschema',
            unique_together=set([('model', 'type_value')]),
        ),
    ]