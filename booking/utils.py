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
    
    # Get seats from either dynamic seat_bookings or legacy seats M2M
    if booking.seat_bookings.exists():
        seats_list = ', '.join([f"{sb.row}{sb.display_seat_number or sb.seat_number}" for sb in booking.seat_bookings.all()])
    else:
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
        
        # Confirm seat bookings (these are already confirmed and linked in the view,
        # but we use the linked records for ticket generation)
        
        # Generate tickets
        from .models import Ticket
        
        # Use SeatBooking records instead of legacy Seat records
        # Create a single ticket for the entire booking
        Ticket.objects.create(
            booking=booking
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
    elif purpose == 'registration':
        subject = 'Account Verification Code - ShowSphere'
        action = 'verify your new'
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


def send_registration_pending_email(user, role_name):
    """Send email to organizer/theatre owner after registration - pending approval"""
    from django.core.mail import EmailMultiAlternatives
    
    subject = f'Registration Received - ShowSphere {role_name}'
    
    # Plain text version
    text_content = f"""
    Hi {user.first_name or user.username},
    
    Thank you for registering with ShowSphere as a {role_name}!
    
    Your registration has been received and is currently under review by our admin team.
    You will receive an email notification once your account has been approved.
    
    This process typically takes 24-48 hours.
    
    If you have any questions, please contact our support team.
    
    Thanks,
    ShowSphere Team
    """
    
    # HTML version with branding
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Roboto', Arial, sans-serif;
                background-color: #F9F7FF;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(140, 82, 255, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #8C52FF 0%, #00BFB2 100%);
                padding: 30px 20px;
                text-align: center;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                color: white;
                margin: 0;
            }}
            .content {{
                padding: 40px 30px;
                color: #2D2042;
            }}
            .content h2 {{
                color: #8C52FF;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .content p {{
                line-height: 1.8;
                color: #666;
                margin: 15px 0;
            }}
            .highlight-box {{
                background: #F9F7FF;
                border-left: 4px solid #8C52FF;
                padding: 15px 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .highlight-box p {{
                margin: 0;
                font-weight: 500;
                color: #2D2042;
            }}
            .footer {{
                background: #1f2533;
                padding: 25px 30px;
                text-align: center;
                color: #abb2bf;
                font-size: 14px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1 class="logo">Show<span style="color: #00BFB2;">Sphere</span></h1>
            </div>
            
            <div class="content">
                <h2>Registration Received!</h2>
                
                <p>Hi <strong>{user.first_name or user.username}</strong>,</p>
                
                <p>Thank you for registering with ShowSphere as a <strong>{role_name}</strong>!</p>
                
                <div class="highlight-box">
                    <p>✅ Your registration has been received and is currently under review by our admin team.</p>
                </div>
                
                <p>You will receive an email notification once your account has been approved. This process typically takes <strong>24-48 hours</strong>.</p>
                
                <p>Once approved, you'll be able to:</p>
                <ul>
                    <li>Access your dashboard</li>
                    <li>Manage your listings</li>
                    <li>Start selling tickets</li>
                </ul>
                
                <p>If you have any questions, please don't hesitate to contact our support team.</p>
                
                <p style="margin-top: 30px;">Best regards,<br><strong>The ShowSphere Team</strong></p>
            </div>
            
            <div class="footer">
                <p>© {timezone.now().year} ShowSphere Entertainment Pvt. Ltd. All Rights Reserved.</p>
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)


def send_approval_email(user, role_name):
    """Send email to organizer/theatre owner after admin approval"""
    from django.core.mail import EmailMultiAlternatives
    
    subject = f'Account Approved - ShowSphere {role_name}'
    
    # Plain text version
    text_content = f"""
    Hi {user.first_name or user.username},
    
    Great news! Your ShowSphere {role_name} account has been approved!
    
    You can now log in to your account and start using all the features available to you.
    
    Login here: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://showsphere.com'}/login/
    
    Username: {user.username}
    
    If you have any questions, our support team is here to help.
    
    Welcome to ShowSphere!
    
    Thanks,
    ShowSphere Team
    """
    
    # HTML version with branding
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Roboto', Arial, sans-serif;
                background-color: #F9F7FF;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(140, 82, 255, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #8C52FF 0%, #00BFB2 100%);
                padding: 30px 20px;
                text-align: center;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                color: white;
                margin: 0;
            }}
            .content {{
                padding: 40px 30px;
                color: #2D2042;
            }}
            .content h2 {{
                color: #8C52FF;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .content p {{
                line-height: 1.8;
                color: #666;
                margin: 15px 0;
            }}
            .success-box {{
                background: linear-gradient(135deg, #8C52FF 0%, #00BFB2 100%);
                color: white;
                padding: 25px;
                margin: 25px 0;
                border-radius: 8px;
                text-align: center;
            }}
            .success-box h3 {{
                margin: 0 0 10px 0;
                font-size: 28px;
            }}
            .success-box p {{
                margin: 0;
                color: white;
                opacity: 0.95;
            }}
            .login-button {{
                display: inline-block;
                background: #8C52FF;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                margin: 20px 0;
            }}
            .info-box {{
                background: #F9F7FF;
                padding: 15px 20px;
                margin: 25px 0;
                border-radius: 8px;
                border-left: 4px solid #8C52FF;
            }}
            .info-box p {{
                margin: 5px 0;
                color: #2D2042;
            }}
            .footer {{
                background: #1f2533;
                padding: 25px 30px;
                text-align: center;
                color: #abb2bf;
                font-size: 14px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1 class="logo">Show<span style="color: #00BFB2;">Sphere</span></h1>
            </div>
            
            <div class="content">
                <div class="success-box">
                    <h3>🎉 Congratulations!</h3>
                    <p>Your account has been approved</p>
                </div>
                
                <p>Hi <strong>{user.first_name or user.username}</strong>,</p>
                
                <p>Great news! Your ShowSphere <strong>{role_name}</strong> account has been approved by our admin team!</p>
                
                <p>You can now log in to your account and start using all the features available to you.</p>
                
                <div style="text-align: center;">
                    <a href="{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/login/" class="login-button">
                        Login to Your Account
                    </a>
                </div>
                
                <div class="info-box">
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                </div>
                
                <p><strong>What you can do now:</strong></p>
                <ul>
                    <li>Access your personalized dashboard</li>
                    <li>Create and manage your listings</li>
                    <li>Start selling tickets to customers</li>
                    <li>Track your sales and analytics</li>
                </ul>
                
                <p>If you have any questions or need assistance getting started, our support team is here to help!</p>
                
                <p style="margin-top: 30px;">Welcome to the ShowSphere family!</p>
                
                <p>Best regards,<br><strong>The ShowSphere Team</strong></p>
            </div>
            
            <div class="footer">
                <p>© {timezone.now().year} ShowSphere Entertainment Pvt. Ltd. All Rights Reserved.</p>
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)



def lock_seats_by_position(seat_positions_with_display, user, show, duration_minutes=10):
    """Lock seats by position (row-seatnumber) with optional display number for a user"""
    from .models import SeatBooking
    from datetime import timedelta
    from django.utils import timezone
    
    lock_expires_at = timezone.now() + timedelta(minutes=duration_minutes)
    seat_layout = show.get_seat_layout()
    price_tiers = show.get_pricing()
    
    locked_seats = []
    
    for item in seat_positions_with_display:
        try:
            # Handle both list of strings or list of dicts/tuples
            if isinstance(item, dict):
                seat_pos = item['position']
                display_num = item.get('display_number')
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                seat_pos, display_num = item
            else:
                seat_pos = item
                display_num = None

            row, seat_num = seat_pos.split('-')
            
            # Get row data from layout
            row_data = seat_layout.get(row, {})
            if not row_data or int(seat_num) not in row_data.get('seats', []):
                continue
            
            # Get price from category
            category_name = row_data.get('category', '')
            price = show.base_price
            
            for tier_key, tier_data in price_tiers.items():
                if isinstance(tier_data, dict) and tier_data.get('name', '').lower() == category_name.lower():
                    price = tier_data.get('price', show.base_price)
                    break
            
            # Create or update seat booking
            seat_booking, created = SeatBooking.objects.get_or_create(
                show=show,
                row=row,
                seat_number=str(seat_num),
                defaults={
                    'user': user,
                    'status': 'locked',
                    'locked_at': timezone.now(),
                    'lock_expires_at': lock_expires_at,
                    'seat_category': category_name,
                    'price': price,
                    'display_seat_number': display_num
                }
            )
            
            if not created:
                # Update existing booking
                seat_booking.user = user
                seat_booking.status = 'locked'
                seat_booking.locked_at = timezone.now()
                seat_booking.lock_expires_at = lock_expires_at
                seat_booking.seat_category = category_name
                seat_booking.price = price
                if display_num:
                    seat_booking.display_seat_number = display_num
                seat_booking.save()
            
            locked_seats.append({
                'row': row,
                'seat_number': seat_num,
                'display_number': display_num or seat_booking.display_seat_number,
                'category': category_name,
                'price': price,
                'position': seat_pos
            })
            
        except (ValueError, AttributeError):
            continue
    
    return locked_seats


def confirm_seat_bookings(seat_positions, user, show, booking=None):
    """Mark seat bookings as booked (confirmed) and link to booking"""
    from .models import SeatBooking
    from django.utils import timezone
    
    confirmed_seats = []
    
    for seat_pos in seat_positions:
        try:
            row, seat_num = seat_pos.split('-')
            
            seat_booking = SeatBooking.objects.filter(
                show=show,
                row=row,
                seat_number=str(seat_num),
                user=user,
                status='locked'
            ).first()
            
            if seat_booking:
                seat_booking.status = 'booked'
                seat_booking.booked_at = timezone.now()
                if booking:
                    seat_booking.booking = booking
                seat_booking.save()
                confirmed_seats.append(seat_booking)
                
        except (ValueError, AttributeError):
            continue
    
    return confirmed_seats
