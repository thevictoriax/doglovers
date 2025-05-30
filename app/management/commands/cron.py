from django_cron import CronJobBase, Schedule
from django.utils.timezone import now
from datetime import timedelta
from app.models import Event, ReminderLog
from app.views import send_event_reminder

class RemindEventsCronJob(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'app.remind_events_cron'

    def do(self):
        current_time = now()

        reminder_types = {
            "week": current_time + timedelta(days=7),
            "day": current_time + timedelta(days=1),
            "3h": current_time + timedelta(hours=3),
        }

        labels = {
            "week": "за тиждень",
            "day": "завтра",
            "3h": "через 3 години",
        }

        for reminder_key, target_time in reminder_types.items():
            tolerance = timedelta(hours=12)
            start_range = target_time - tolerance
            end_range = target_time + tolerance

            events = Event.objects.filter(start__range=(start_range, end_range))
            for event in events:
                user = event.dog.owner
                to_email = user.email

                if ReminderLog.objects.filter(user=user, event=event, reminder_type=reminder_key).exists():
                    continue

                if to_email:
                    try:
                        send_event_reminder(to_email, event, labels[reminder_key])
                        ReminderLog.objects.create(user=user, event=event, reminder_type=reminder_key)
                        print(f"✅ {labels[reminder_key]} — '{event.name}' → {to_email}")
                    except Exception as e:
                        print(f"❌ Помилка: {to_email} — {str(e)}")
