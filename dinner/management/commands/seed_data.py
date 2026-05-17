from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dinner.models import Couple

COUPLES = [
    ('florian_afra', 'Florian & Afra', 'florian'),
    ('philipe_lena', 'Philipe & Lena', 'philipe'),
    ('brecht_ragna', 'Brecht & Ragna', 'brecht'),
]


class Command(BaseCommand):
    help = 'Seed the three couple users'

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
        self.stdout.write(self.style.SUCCESS('Seed voltooid!'))
