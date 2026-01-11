from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import uuid


def send_verification_email(user, request):
    """Send email verification link to user"""
    token = uuid.uuid4().hex
    user.verification_token = token
    user.save()
    
    verification_url = request.build_absolute_uri(
        reverse('booking:verify_email', args=[token])
    )
    
    subject = 'Verify your ShowSphere account'
    message = f"""
    Hi {user.first_name or user.username},
    
    Welcome to ShowSphere! Please verify your email address by clicking the link below:
    
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create this account, please ignore this email.
    
    Thanks,
    ShowSphere Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, request):
    """Send password reset link to user"""
    token = uuid.uuid4().hex
    user.verification_token = token
    user.save()
    
    reset_url = request.build_absolute_uri(
        reverse('booking:password_reset_confirm', args=[token])
    )
    
    subject = 'Reset your ShowSphere password'
    message = f"""
    Hi {user.first_name or user.username},
    
    You requested to reset your password for your ShowSphere account.
    
    Click the link below to reset your password:
    
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    
    Thanks,
    ShowSphere Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_booking_confirmation_email(booking):
    """Send booking confirmation email to customer"""
    user = booking.user
    show = booking.show
    
    if show.show_type == 'event':
        title = show.event.title
        location = show.venue.name
    else:
        title = show.movie.title
        location = f"{show.screen.theatre.name} - {show.screen.name}"
    
    seats_list = ', '.join([f"{seat.row}{seat.seat_number}" for seat in booking.seats.all()])
    
    subject = f'Booking Confirmed - {title}'
    message = f"""
    Hi {user.first_name or user.username},
    
    Your booking has been confirmed!
    
    Booking ID: {booking.booking_id}
    {show.get_show_type_display()}: {title}
    Location: {location}
    Date: {show.show_date.strftime('%d %B %Y')}
    Time: {show.show_time.strftime('%I:%M %p')}
    Seats: {seats_list}
    Total Amount: ₹{booking.grand_total}
    
    Your e-tickets have been generated. You can view and download them from your account.
    
    Enjoy the show!
    
    ShowSphere Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def lock_seats(seats, user, show, duration_minutes=10):
    """Lock seats for a user during booking process"""
    from .models import SeatBooking
    
    lock_expires_at = timezone.now() + timedelta(minutes=duration_minutes)
    
    for seat in seats:
        seat_booking, created = SeatBooking.objects.get_or_create(
            seat=seat,
            show=show,
            defaults={
                'user': user,
                'status': 'locked',
                'locked_at': timezone.now(),
                'lock_expires_at': lock_expires_at
            }
        )
        
        if not created:
            # Update existing booking
            seat_booking.user = user
            seat_booking.status = 'locked'
            seat_booking.locked_at = timezone.now()
            seat_booking.lock_expires_at = lock_expires_at
            seat_booking.save()


def release_expired_locks():
    """Release all expired seat locks"""
    from .models import SeatBooking
    
    expired_locks = SeatBooking.objects.filter(
        status='locked',
        lock_expires_at__lt=timezone.now()
    )
    
    expired_locks.update(
        status='available',
        user=None,
        locked_at=None,
        lock_expires_at=None
    )
    
    return expired_locks.count()


def confirm_seat_bookings(seats, show):
    """Confirm seat bookings after successful payment"""
    from .models import SeatBooking
    
    for seat in seats:
        try:
            seat_booking = SeatBooking.objects.get(seat=seat, show=show)
            seat_booking.status = 'booked'
            seat_booking.booked_at = timezone.now()
            seat_booking.save()
        except SeatBooking.DoesNotExist:
            # Create new booking if doesn't exist
            SeatBooking.objects.create(
                seat=seat,
                show=show,
                status='booked',
                booked_at=timezone.now()
            )


def get_available_seats(show):
    """Get list of available seats for a show"""
    from .models import SeatBooking
    
    # First, release expired locks
    release_expired_locks()
    
    # Get all seats for the show
    all_seats = show.seats.all()
    
    # Get booked and locked seats
    unavailable_bookings = SeatBooking.objects.filter(
        show=show,
        status__in=['booked', 'locked']
    ).values_list('seat_id', flat=True)
    
    # Return available seats
    available_seats = all_seats.exclude(id__in=unavailable_bookings)
    
    return available_seats


def simulate_payment(booking, payment_method):
    """Simulate payment processing (for development)"""
    import random
    import time
    
    # Simulate processing delay
    time.sleep(1)
    
    # 95% success rate for simulation
    success = random.random() < 0.95
    
    if success:
        booking.payment_status = 'completed'
        booking.payment_method = payment_method
        booking.save()
        
        # Confirm seat bookings
        confirm_seat_bookings(booking.seats.all(), booking.show)
        
        # Generate tickets
        from .models import Ticket
        for seat in booking.seats.all():
            Ticket.objects.create(
                booking=booking,
                seat=seat
            )
        
        # Send confirmation email
        send_booking_confirmation_email(booking)
        
        return True, "Payment successful!"
    else:
        booking.payment_status = 'failed'
        booking.save()
        return False, "Payment failed. Please try again."


def generate_otp(user, purpose):
    """Generate and save 6-digit OTP"""
    import random
    import string
    from .models import OTP
    
    # Invalidate old OTPs for this purpose
    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    
    # Generate new 6-digit code
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Save to DB
    OTP.objects.create(
        user=user,
        otp_code=otp_code,
        purpose=purpose
    )
    
    return otp_code


def send_otp_email(user, otp_code, purpose):
    """Send OTP via email"""
    if purpose == 'login':
        subject = 'Login Verification Code - ShowSphere'
        action = 'log in to'
    else:
        subject = 'Password Reset Code - ShowSphere'
        action = 'reset your password for'
        
    message = f"""
    Hi {user.first_name or user.username},
    
    Your verification code to {action} your ShowSphere account is:
    
    {otp_code}
    
    This code is valid for 5 minutes.
    
    If you did not request this, please ignore this email.
    
    Thanks,
    ShowSphere Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

