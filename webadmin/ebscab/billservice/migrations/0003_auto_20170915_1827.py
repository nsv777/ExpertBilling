# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-15 18:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billservice', '0002_auto_20170915_1641'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_rx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_time_rx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_time_tx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_treshold_rx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_treshold_tx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='burst_tx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='max_rx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='max_tx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='min_rx',
        ),
        migrations.RemoveField(
            model_name='accessparameters',
            name='min_tx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_rx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_time_rx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_time_tx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_treshold_rx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_treshold_tx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='burst_tx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='max_rx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='max_tx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='min_rx',
        ),
        migrations.RemoveField(
            model_name='timespeed',
            name='min_tx',
        ),

        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_rx_int',
            new_name='burst_rx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_time_rx_int',
            new_name='burst_time_rx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_time_tx_int',
            new_name='burst_time_tx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_treshold_rx_int',
            new_name='burst_treshold_rx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_treshold_tx_int',
            new_name='burst_treshold_tx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='burst_tx_int',
            new_name='burst_tx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='max_rx_int',
            new_name='max_rx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='max_tx_int',
            new_name='max_tx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='min_rx_int',
            new_name='min_rx'
        ),
        migrations.RenameField(
            model_name='accessparameters',
            old_name='min_tx_int',
            new_name='min_tx'
        ),

        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_rx_int',
            new_name='burst_rx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_time_rx_int',
            new_name='burst_time_rx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_time_tx_int',
            new_name='burst_time_tx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_treshold_rx_int',
            new_name='burst_treshold_rx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_treshold_tx_int',
            new_name='burst_treshold_tx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='burst_tx_int',
            new_name='burst_tx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='max_rx_int',
            new_name='max_rx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='max_tx_int',
            new_name='max_tx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='min_rx_int',
            new_name='min_rx'
        ),
        migrations.RenameField(
            model_name='timespeed',
            old_name='min_tx_int',
            new_name='min_tx'
        )
    ]
