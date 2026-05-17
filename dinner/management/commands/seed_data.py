from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dinner.models import Couple, DinnerDate

COUPLES = [
    ('florian_afra',  'Florian & Afra',  'florian'),
    ('philipe_lena',  'Philipe & Lena',  'philipe'),
    ('brecht_ragna',  'Brecht & Ragna',  'brecht'),
]

DINNERS = [
    ('florian_afra',  date(2026, 3, 1)),
    ('brecht_ragna',  date(2026, 7, 1)),
    ('philipe_lena',  date(2026, 8, 1)),
]


class Command(BaseCommand):
    help = 'Seed the three couple users and their dinner dates'

    def handle(self, *args, **options):
        for username, display_name, password in COUPLES:
            user, created = User.objects.get_or_create(username=username)
            if created or not user.has_usable_password():
                user.set_password(password)
                user.save()
                self.stdout.write(f'  User aangemaakt: {username} (wachtwoord: {password})')
            else:
                self.stdout.write(f'  User bestaat al: {username}')
            couple, c_created = Couple.objects.get_or_create(user=user, defaults={'name': display_name})
            if c_created:
                self.stdout.write(f'  Koppel aangemaakt: {display_name}')

        for username, dinner_date in DINNERS:
            couple = Couple.objects.get(user__username=username)
            _, created = DinnerDate.objects.get_or_create(date=dinner_date, defaults={'host': couple})
            if created:
                self.stdout.write(f'  Diner aangemaakt: {couple.name} op {dinner_date}')
            else:
                self.stdout.write(f'  Diner bestaat al: {dinner_date}')

        self.stdout.write(self.style.SUCCESS('Seed voltooid!'))
