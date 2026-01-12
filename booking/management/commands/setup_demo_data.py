from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from booking.models import *
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates demo users and initial data for testing'



    def generate_image_file(self, name, color, text):
        from PIL import Image, ImageDraw
        from io import BytesIO
        from django.core.files.base import ContentFile
        
        img = Image.new('RGB', (800, 600), color=color)
        # Create a simple placeholder image
        f = BytesIO()
        img.save(f, format='JPEG')
        return ContentFile(f.getvalue(), name=name)

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up demo data...')

        # 1. Create Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            email='admin@showsphere.com',
            defaults={
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True,
                'is_active': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created Admin: admin / admin123'))
        else:
             self.stdout.write('Admin already exists')

        # 2. Create Organizer
        organizer_user, created = User.objects.get_or_create(
            username='organizer',
            email='organizer@showsphere.com',
            defaults={
                'role': 'organizer',
                'email_verified': True,
                'is_active': True
            }
        )
        
        
        # Create locations
        country_india, _ = Country.objects.get_or_create(name='India')
        state_maharashtra, _ = State.objects.get_or_create(name='Maharashtra', country=country_india)
        state_delhi, _ = State.objects.get_or_create(name='Delhi', country=country_india)
        
        city_mumbai, _ = City.objects.get_or_create(name='Mumbai', state=state_maharashtra)
        city_delhi, _ = City.objects.get_or_create(name='Delhi', state=state_delhi)

        if created:
            organizer_user.set_password('org123')
            organizer_user.save()
            
        OrganizerProfile.objects.get_or_create(
            user=organizer_user,
            defaults={
                'organization_name': 'Rockstar Events',
                'contact_person': 'John Doe',
                'contact_email': 'rockstar@events.com',
                'contact_phone': '9876543210',
                'city': city_mumbai,
                'address': '123, Event Street, Bandra',
                'status': 'approved'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Organizer: organizer / org123'))
        
        # Create Dummy Data for Organizer
        org_profile = OrganizerProfile.objects.get(user=organizer_user)
        category, _ = Category.objects.get_or_create(name='Music', slug='music')
        lang, _ = Language.objects.get_or_create(name='English', code='en')
        
        venue, _ = Venue.objects.get_or_create(
            organizer=org_profile,
            name='DY Patil Stadium',
            defaults={
                'venue_type': 'stadium',
                'city': city_mumbai,
                'address': 'Nerul, Navi Mumbai',
                'capacity': 50000,
                'is_active': True
            }
        )
        
        event, created = Event.objects.get_or_create(
            organizer=org_profile,
            title='Coldplay Concert',
            defaults={
                 'description': 'Live in concert!',
                 'category': category,
                 'language': lang,
                 'duration': 180,
                 'artist_name': 'Coldplay',
                 'status': 'approved',
                 'is_trending': True
            }
        )
        if created or not event.poster:
            event.poster.save('coldplay.jpg', self.generate_image_file('coldplay.jpg', 'blue', 'Coldplay'), save=True)
        
        # Schedule a show
        show, _ = Show.objects.get_or_create(
             event=event,
             venue=venue,
             show_date=timezone.now().date() + timedelta(days=5),
             show_time='19:00:00',
             defaults={
                 'show_type': 'event',
                 'end_time': '22:00:00',
                 'base_price': 5000.00,
                 'is_active': True
              }
        )
        
        # Add some seats
        if not Seat.objects.filter(show=show).exists():
             for r in ['A', 'B', 'C']:
                 for n in range(1, 11):
                     Seat.objects.create(
                         show=show, 
                         row=r, 
                         seat_number=str(n), 
                         seat_type='gold', 
                         price=5000.00
                     )


        # 3. Create Theatre Owner
        theatre_user, created = User.objects.get_or_create(
            username='theatre',
            email='theatre@showsphere.com',
            defaults={
                'role': 'theatre_owner',
                'email_verified': True,
                'is_active': True
            }
        )
        if created:
            theatre_user.set_password('theatre123')
            theatre_user.save()
            
        TheatreOwnerProfile.objects.get_or_create(
            user=theatre_user,
            defaults={
                'theatre_chain_name': 'PVR Cinemas',
                'owner_name': 'Jane Smith',
                'contact_phone': '9876543211',
                'contact_email': 'partners@pvr.com',
                'city': city_delhi,
                'address': 'Connaught Place',
                'status': 'approved'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Theatre Owner: theatre / theatre123'))
            
        # Create Dummy Data for Theatre
        theatre_profile = TheatreOwnerProfile.objects.get(user=theatre_user)
        movie_category, _ = Category.objects.get_or_create(name='Movies', slug='movies')
        genre, _ = Genre.objects.get_or_create(name='Action', category=movie_category)
        
        theatre, _ = Theatre.objects.get_or_create(
             owner=theatre_profile,
             name='PVR Plaza',
             defaults={
                 'city': city_delhi,
                 'address': 'Connaught Place',
                 'total_screens': 2,
                 'is_active': True
             }
        )
        
        screen, _ = Screen.objects.get_or_create(
            theatre=theatre,
            name='Screen 1',
            defaults={'total_seats': 100}
        )
        
        movie, created = Movie.objects.get_or_create(
             theatre_owner=theatre_profile,
             title='Inception',
             defaults={
                 'description': 'A thief who steals corporate secrets...',
                 'language': lang,
                 'genre': genre,
                 'duration': 148,
                 'director': 'Christopher Nolan',
                 'cast': 'Leonardo DiCaprio',
                 'certification': 'UA',
                 'release_date': timezone.now().date(),
                 'status': 'approved',
                 'is_trending': True
             }
        )
        if created or not movie.poster:
             movie.poster.save('inception.jpg', self.generate_image_file('inception.jpg', 'red', 'Inception'), save=True)
        
        # Schedule Movie Show
        movie_show, _ = Show.objects.get_or_create(
             movie=movie,
             screen=screen,
             show_date=timezone.now().date() + timedelta(days=2),
             show_time='14:00:00',
             defaults={
                 'show_type': 'movie',
                 'end_time': '16:30:00',
                 'base_price': 300.00,
                 'is_active': True
             }
        )

        if not Seat.objects.filter(show=movie_show).exists():
             for r in ['A', 'B', 'C']:
                 for n in range(1, 11):
                     Seat.objects.create(
                         show=movie_show, 
                         row=r, 
                         seat_number=str(n), 
                         seat_type='gold', 
                         price=300.00
                     )

        # 4. Create Customer
        customer, created = User.objects.get_or_create(
            username='customer',
            email='customer@showsphere.com',
            defaults={
                'role': 'customer',
                'email_verified': True,
                'is_active': True
            }
        )
        if created:
            customer.set_password('cust123')
            customer.save()
            self.stdout.write(self.style.SUCCESS('Created Customer: customer / cust123'))
        else:
             self.stdout.write('Customer already exists')

        self.stdout.write(self.style.SUCCESS('\nDemo Data Setup Complete!'))
