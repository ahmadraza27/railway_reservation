from __future__ import absolute_import,unicode_literals

from celery import shared_task
from .models import Schedule

@shared_task
def check_schedule_seats():
    schedules = Schedule.objects.all()
    for schedule in schedules:
        schedule.check_and_reset_seats()

