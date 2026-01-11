from django.core.management.base import BaseCommand
from booking.models import Show, Seat, SeatBooking

class Command(BaseCommand):
    help = 'Populates seats for a show to match the specific UI layout'

    def add_arguments(self, parser):
        parser.add_argument('show_id', type=int, help='ID of the show to populate seats for')

    def handle(self, *args, **options):
        show_id = options['show_id']
        try:
            show = Show.objects.get(id=show_id)
        except Show.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Show with ID {show_id} does not exist'))
            return

        # Warning
        self.stdout.write(self.style.WARNING(f'This will DELETE all existing seats and bookings for show {show_id}.'))
        
        # Clear existing seats
        Seat.objects.filter(show=show).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted existing seats for show {show_id}'))

        # Define Layout
        # Image shows:
        # Premium (300): I, H, G
        # Executive (200): E, D
        # Normal (150): A
        
        # Each row has columns 1-14
        
        layout = [
            {'row': 'I', 'price': 300, 'type': 'premium'},
            {'row': 'H', 'price': 300, 'type': 'premium'},
            {'row': 'G', 'price': 300, 'type': 'premium'},
            {'row': 'E', 'price': 200, 'type': 'gold'}, # Mapping Executive -> Gold/Classic
            {'row': 'D', 'price': 200, 'type': 'gold'},
            {'row': 'A', 'price': 150, 'type': 'silver'}, # Mapping Normal -> Silver
        ]

        seats_created = 0
        
        for row_config in layout:
            row_code = row_config['row']
            price = row_config['price']
            seat_type = row_config['type']
            
            for i in range(1, 15): # 1 to 14
                seat_num = str(i)
                Seat.objects.create(
                    show=show,
                    row=row_code,
                    seat_number=seat_num,
                    seat_type=seat_type,
                    price=price
                )
                seats_created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {seats_created} seats for show {show_id} matching the target layout.'))
