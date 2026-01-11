from django.core.management.base import BaseCommand
from core.models import Category

class Command(BaseCommand):
    help = 'Create all categories from kupujemprodajem.com'

    def handle(self, *args, **options):
        categories = [
            'Alati i oruđa',
            'Antikviteti',
            'Aksesoari',
            'Audio | Ploče, CD i kasete',
            'Auto delovi i alati',
            'Auto oprema',
            'Automobili',
            'Bela tehnika i kućni aparati',
            'Bicikli',
            'Bicikli | Delovi i oprema',
            'Časopisi i stripovi',
            'Dvorište i bašta',
            'Elektro i rasveta',
            'Elektronika',
            'Etno stvari',
            'Fitnes i vežbanje',
            'Foto-aparati i kamere',
            'Građevinarstvo',
            'Građevinske mašine',
            'Igračke',
            'Industrijska oprema',
            'Knjige',
            'Kompjuteri',
            'Konzole i igrice',
            'Kućni ljubimci',
            'Kućni ljubimci | Oprema',
            'Kupatilo i oprema',
            'Lov i ribolov',
            'Mobilni tel. | Oprema i delovi',
            'Mobilni telefoni',
            'Motocikli',
            'Motocikli | Oprema i delovi',
            'Muzički instrumenti',
            'Nakit i dragocenosti',
            'Nameštaj',
            'Nekretnine',
            'Obuća | Dečja',
            'Obuća | Muška',
            'Obuća | Ženska',
            'Odeća | Dečja',
            'Odeća | Muška',
            'Odeća | Ženska',
            'Plovni objekti',
            'Poljoprivreda',
            'Poljoprivreda | Domaće životinje',
            'Sport i razonoda',
            'Sve za školu',
            'Transportna vozila',
            'Transportna vozila | Delovi i oprema',
            'Ugostiteljstvo | Oprema',
            'Uređenje kuće',
        ]

        created_count = 0
        for category_name in categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Kreirano: {category_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Već postoji: {category_name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Ukupno kreirano: {created_count} kategorija'))
