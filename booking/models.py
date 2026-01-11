from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
try:
    import qrcode
except ImportError:
    qrcode = None
from io import BytesIO
from django.core.files import File
import uuid
from datetime import timedelta


class CustomUser(AbstractUser):
    """Extended user model with role-based access"""
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('organizer', 'Event Organizer'),
        ('theatre_owner', 'Theatre Owner'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class OrganizerProfile(models.Model):
    """Profile for EVENT organizers (concerts, sports, comedy shows, etc.)"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='organizer_profile')
    organization_name = models.CharField(max_length=200, help_text='Event organization/company name')
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.organization_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = 'Event Organizer Profile'
        verbose_name_plural = 'Event Organizer Profiles'


class TheatreOwnerProfile(models.Model):
    """Profile for THEATRE/CINEMA owners (movies only)"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='theatre_profile')
    theatre_chain_name = models.CharField(max_length=200, help_text='Theatre/Cinema chain name (e.g., PVR, INOX)')
    owner_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)
    address = models.TextField(help_text='Head office address')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.theatre_chain_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = 'Theatre Owner Profile'
        verbose_name_plural = 'Theatre Owner Profiles'


class City(models.Model):
    """Cities where events/movies are available"""
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Event categories (Movies, Concerts, Sports, Comedy, Shows, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class name')
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Genre(models.Model):
    """Genres for events/movies"""
    name = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='genres')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Language(models.Model):
    """Languages for events/movies"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Venue(models.Model):
    """Venues for EVENTS ONLY (concerts, sports, comedy shows, etc.)"""
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='venues')
    name = models.CharField(max_length=200, help_text='Venue name (e.g., Stadium, Arena, Auditorium)')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='event_venues')
    address = models.TextField()
    capacity = models.PositiveIntegerField()
    facilities = models.TextField(blank=True, help_text='Parking, Food Court, etc.')
    venue_type = models.CharField(max_length=50, blank=True, help_text='Stadium, Arena, Hall, etc.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.city.name}"


class Theatre(models.Model):
    """Theatres/Cinemas for MOVIES ONLY"""
    owner = models.ForeignKey(TheatreOwnerProfile, on_delete=models.CASCADE, related_name='theatres')
    name = models.CharField(max_length=200, help_text='Theatre/Cinema name with location')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='theatres')
    address = models.TextField()
    total_screens = models.PositiveIntegerField()
    facilities = models.TextField(blank=True, help_text='Parking, Food Court, 3D, IMAX, etc.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.city.name}"


class Screen(models.Model):
    """Screens within a theatre (for movies)"""
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=50, help_text='Screen 1, Audi 2, etc.')
    total_seats = models.PositiveIntegerField()
    screen_type = models.CharField(max_length=50, blank=True, help_text='2D, 3D, IMAX, 4DX, etc.')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['theatre', 'name']
    
    def __str__(self):
        return f"{self.theatre.name} - {self.name}"


class Event(models.Model):
    """Events (concerts, sports, comedy shows, theatre plays, etc.) - NOT movies"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='events', 
                                 help_text='Concerts, Sports, Comedy, Shows, etc.')
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes')
    artist_name = models.CharField(max_length=200, blank=True, help_text='Main artist/performer/team')
    poster = models.ImageField(upload_to='event_posters/')
    trailer_url = models.URLField(blank=True, help_text='YouTube promo/trailer URL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.category.name})"


class Movie(models.Model):
    """Movies ONLY - managed by theatre owners"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CERTIFICATION_CHOICES = [
        ('U', 'U - Universal'),
        ('UA', 'UA - Parental Guidance'),
        ('A', 'A - Adults Only'),
        ('S', 'S - Restricted'),
    ]
    
    theatre_owner = models.ForeignKey(TheatreOwnerProfile, on_delete=models.CASCADE, related_name='movies')
    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes')
    release_date = models.DateField()
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True, help_text='Main cast members')
    certification = models.CharField(max_length=5, choices=CERTIFICATION_CHOICES, blank=True)
    poster = models.ImageField(upload_to='movie_posters/')
    trailer_url = models.URLField(blank=True, help_text='YouTube trailer URL')
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(10)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-release_date']
    
    def __str__(self):
        return self.title


class Show(models.Model):
    """Scheduled shows - can be either event show or movie show"""
    SHOW_TYPE_CHOICES = [
        ('event', 'Event Show'),
        ('movie', 'Movie Show'),
    ]
    
    show_type = models.CharField(max_length=10, choices=SHOW_TYPE_CHOICES)
    
    # For events - uses venue
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='shows')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True, related_name='shows')
    
    # For movies - uses theatre screen
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='shows')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, null=True, blank=True, related_name='shows')
    
    show_date = models.DateField()
    show_time = models.TimeField()
    end_time = models.TimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Starting price')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['show_date', 'show_time']
    
    def __str__(self):
        if self.show_type == 'event':
            return f"{self.event.title} at {self.venue.name} - {self.show_date} {self.show_time}"
        else:
            return f"{self.movie.title} at {self.screen.theatre.name} - {self.show_date} {self.show_time}"
    
    @property
    def available_seats(self):
        total = self.seats.count()
        booked = self.seat_bookings.filter(status='booked').count()
        return total - booked
    
    @property
    def location_name(self):
        """Returns venue or theatre name"""
        if self.show_type == 'event':
            return self.venue.name if self.venue else 'N/A'
        else:
            return f"{self.screen.theatre.name} - {self.screen.name}" if self.screen else 'N/A'


class Seat(models.Model):
    """Seats for shows (both events and movies)"""
    SEAT_TYPE_CHOICES = [
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
        ('recliner', 'Recliner'),
    ]
    
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=5)
    seat_number = models.CharField(max_length=5)
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['row', 'seat_number']
        unique_together = ['show', 'row', 'seat_number']
    
    def __str__(self):
        return f"{self.row}{self.seat_number} ({self.get_seat_type_display()}) - ₹{self.price}"


class SeatBooking(models.Model):
    """Seat booking status with real-time locking mechanism"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('locked', 'Locked'),
        ('booked', 'Booked'),
    ]
    
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='locks')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='seat_bookings')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    locked_at = models.DateTimeField(null=True, blank=True)
    booked_at = models.DateTimeField(null=True, blank=True)
    lock_expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['seat', 'show']
    
    def __str__(self):
        return f"{self.seat} - {self.get_status_display()}"
    
    def is_lock_expired(self):
        """Check if seat lock has expired (typically 10 minutes)"""
        if self.status == 'locked' and self.lock_expires_at:
            return timezone.now() > self.lock_expires_at
        return False


class Booking(models.Model):
    """Customer bookings for both events and movies"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Debit/Credit Card'),
        ('wallet', 'Wallet'),
        ('netbanking', 'Net Banking'),
    ]
    
    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='bookings')
    seats = models.ManyToManyField(Seat, related_name='bookings')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    convenience_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-booking_date']
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            # Generate unique booking ID
            self.booking_id = f"SS{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.booking_id} - {self.user.username}"
    
    @property
    def grand_total(self):
        return self.total_amount + self.convenience_fee


class Ticket(models.Model):
    """E-tickets with QR codes"""
    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = f"TKT{uuid.uuid4().hex[:10].upper()}"
        
        # Generate QR code
        if not self.qr_code and qrcode:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_data = f"ShowSphere Ticket\nTicket ID: {self.ticket_id}\nBooking ID: {self.booking.booking_id}\nSeat: {self.seat}\nShow: {self.booking.show}"
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'ticket_{self.ticket_id}.png'
            self.qr_code.save(file_name, File(buffer), save=False)
            buffer.close()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_id} - {self.seat}"


class OTP(models.Model):
    """One-Time Passwords for authentication"""
    PURPOSE_CHOICES = [
        ('login', 'Login'),
        ('reset_password', 'Reset Password'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        # Valid for 5 minutes
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=5)
    
    def __str__(self):
        return f"{self.user.username} - {self.otp_code} ({self.purpose})"