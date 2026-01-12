from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import *
from .forms import *
from .decorators import *
from .utils import *


# ============= PUBLIC PAGES (GUEST ACCESS) =============

def home(request):
    """Homepage with trending events and movies"""
    # Get user's selected city from session or default
    selected_city_id = request.session.get('selected_city')
    selected_city = None
    if selected_city_id:
        selected_city = City.objects.filter(id=selected_city_id, is_active=True).first()
    
    # Get trending events and movies
    trending_events = Event.objects.filter(status='approved', is_trending=True)[:6]
    trending_movies = Movie.objects.filter(status='approved', is_trending=True)[:6]
    
    # Get new releases
    new_movies = Movie.objects.filter(status='approved').order_by('-release_date')[:6]
    
    # Filter by city if selected
    if selected_city:
        # Get shows in selected city
        event_shows = Show.objects.filter(
            show_type='event',
            venue__city=selected_city,
            show_date__gte=timezone.now().date()
        ).values_list('event_id', flat=True).distinct()
        
        movie_shows = Show.objects.filter(
            show_type='movie',
            screen__theatre__city=selected_city,
            show_date__gte=timezone.now().date()
        ).values_list('movie_id', flat=True).distinct()
        
        trending_events = trending_events.filter(id__in=event_shows)
        trending_movies = trending_movies.filter(id__in=movie_shows)
        new_movies = new_movies.filter(id__in=movie_shows)
    
    categories = Category.objects.all()
    cities = City.objects.filter(is_active=True)
    
    context = {
        'trending_events': trending_events,
        'trending_movies': trending_movies,
        'new_movies': new_movies,
        'categories': categories,
        'cities': cities,
        'selected_city': selected_city,
    }
    return render(request, 'home.html', context)


def partner_selection(request):
    """Page to select between Theatre Owner and Event Organizer registration"""
    return render(request, 'partner_selection.html')


def browse(request):
    """Browse all events and movies"""
    category_slug = request.GET.get('category')
    city_id = request.GET.get('city')
    language_id = request.GET.get('language')
    genre_id = request.GET.get('genre')
    
    events = Event.objects.filter(status='approved')
    movies = Movie.objects.filter(status='approved')
    
    # Apply filters
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        events = events.filter(category=category)
    
    if city_id:
        city = get_object_or_404(City, id=city_id)
        # Filter by shows in this city
        event_ids = Show.objects.filter(
            show_type='event',
            venue__city=city,
            show_date__gte=timezone.now().date()
        ).values_list('event_id', flat=True).distinct()
        
        movie_ids = Show.objects.filter(
            show_type='movie',
            screen__theatre__city=city,
            show_date__gte=timezone.now().date()
        ).values_list('movie_id', flat=True).distinct()
        
        events = events.filter(id__in=event_ids)
        movies = movies.filter(id__in=movie_ids)
    
    if language_id:
        language = get_object_or_404(Language, id=language_id)
        events = events.filter(language=language)
        movies = movies.filter(language=language)
    
    if genre_id:
        genre = get_object_or_404(Genre, id=genre_id)
        events = events.filter(genre=genre)
        movies = movies.filter(genre=genre)
    
    context = {
        'events': events,
        'movies': movies,
        'categories': Category.objects.all(),
        'cities': City.objects.filter(is_active=True),
        'languages': Language.objects.all(),
        'genres': Genre.objects.all(),
    }
    return render(request, 'browse.html', context)


def search(request):
    """Search events and movies"""
    query = request.GET.get('q', '')
    
    events = Event.objects.filter(
        Q(title__icontains=query) | Q(artist_name__icontains=query) | Q(description__icontains=query),
        status='approved'
    )
    
    movies = Movie.objects.filter(
        Q(title__icontains=query) | Q(director__icontains=query) | Q(cast__icontains=query),
        status='approved'
    )
    
    context = {
        'query': query,
        'events': events,
        'movies': movies,
    }
    return render(request, 'search.html', context)


def load_states(request):
    """AJAX view to load states for a country"""
    country_id = request.GET.get('country_id')
    states = State.objects.filter(country_id=country_id).values('id', 'name').order_by('name')
    return JsonResponse(list(states), safe=False)


def load_cities(request):
    """AJAX view to load cities for a state"""
    state_id = request.GET.get('state_id')
    cities = City.objects.filter(state_id=state_id, is_active=True).values('id', 'name').order_by('name')
    return JsonResponse(list(cities), safe=False)



def event_detail(request, event_id):
    """Event detail page with date selector and venue grouping"""
    event = get_object_or_404(Event, id=event_id, status='approved')
    
    # Get selected date or default to today
    from datetime import datetime, timedelta
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Generate date options (next 7 days)
    date_options = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        date_options.append(date)
    
    # Get shows for this event on the selected date
    shows = Show.objects.filter(
        event=event,
        show_date=selected_date,
        is_active=True
    ).select_related('venue').order_by('venue', 'show_time')
    
    # Group shows by venue
    from collections import defaultdict
    venues_with_shows = defaultdict(list)
    for show in shows:
        venues_with_shows[show.venue].append(show)
    
    context = {
        'event': event,
        'venues_with_shows': dict(venues_with_shows),
        'selected_date': selected_date,
        'date_options': date_options,
    }
    return render(request, 'event_detail.html', context)


def movie_detail(request, movie_id):
    """Movie detail page with date selector and theatre grouping"""
    movie = get_object_or_404(Movie, id=movie_id, status='approved')
    
    # Get selected date or default to today
    from datetime import datetime, timedelta
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Generate date options (next 7 days)
    date_options = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        date_options.append(date)
    
    # Get shows for this movie on the selected date
    shows = Show.objects.filter(
        movie=movie,
        show_date=selected_date,
        is_active=True
    ).select_related('screen__theatre').order_by('screen__theatre', 'show_time')
    
    # Group shows by theatre
    from collections import defaultdict
    theatres_with_shows = defaultdict(list)
    for show in shows:
        theatres_with_shows[show.screen.theatre].append(show)
    
    context = {
        'movie': movie,
        'theatres_with_shows': dict(theatres_with_shows),
        'selected_date': selected_date,
        'date_options': date_options,
    }
    return render(request, 'movie_detail.html', context)


def movie_shows(request, movie_id):
    """Whole new page to display available shows for a movie grouped by theatre with date selection"""
    movie = get_object_or_404(Movie, id=movie_id, status='approved')
    
    # Get selected date or default to today
    from datetime import datetime, timedelta
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Generate date options (next 7 days)
    date_options = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        date_options.append(date)
    
    # Get shows for this movie on the selected date
    shows = Show.objects.filter(
        movie=movie,
        show_date=selected_date,
        is_active=True
    ).select_related('screen__theatre').order_by('screen__theatre', 'show_time')
    
    # Group shows by theatre
    from collections import defaultdict
    theatres_with_shows = defaultdict(list)
    for show in shows:
        theatres_with_shows[show.screen.theatre].append(show)
    
    context = {
        'movie': movie,
        'theatres_with_shows': dict(theatres_with_shows),
        'selected_date': selected_date,
        'date_options': date_options,
    }
    return render(request, 'movie_shows.html', context)


def theatre_list(request):
    """List all theatres with filtering options"""
    city_id = request.GET.get('city')
    search_query = request.GET.get('q', '')
    
    theatres = Theatre.objects.filter(is_active=True).select_related('city', 'owner')
    
    # Apply city filter
    if city_id:
        theatres = theatres.filter(city_id=city_id)
    
    # Apply search filter
    if search_query:
        theatres = theatres.filter(
            Q(name__icontains=search_query) | 
            Q(address__icontains=search_query)
        )
    
    theatres = theatres.order_by('city__name', 'name')
    
    context = {
        'theatres': theatres,
        'cities': City.objects.filter(is_active=True),
        'selected_city_id': city_id,
        'search_query': search_query,
    }
    return render(request, 'theatre_list.html', context)


def theatre_detail(request, theatre_id):
    """Theatre detail page showing currently playing movies"""
    theatre = get_object_or_404(Theatre, id=theatre_id, is_active=True)
    
    # Get selected date or default to today
    from datetime import datetime, timedelta
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Generate date options (next 7 days)
    date_options = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        date_options.append(date)
    
    # Get all shows for this theatre on the selected date
    shows = Show.objects.filter(
        screen__theatre=theatre,
        show_date=selected_date,
        is_active=True
    ).select_related('movie', 'screen').order_by('movie', 'show_time')
    
    # Group shows by movie
    from collections import defaultdict
    movies_with_shows = defaultdict(list)
    for show in shows:
        movies_with_shows[show.movie].append(show)
    
    context = {
        'theatre': theatre,
        'movies_with_shows': dict(movies_with_shows),
        'selected_date': selected_date,
        'date_options': date_options,
    }
    return render(request, 'theatre_detail.html', context)


def venue_list(request):
    """List all venues with filtering options"""
    city_id = request.GET.get('city')
    search_query = request.GET.get('q', '')
    
    venues = Venue.objects.filter(is_active=True).select_related('city', 'organizer')
    
    # Apply city filter
    if city_id:
        venues = venues.filter(city_id=city_id)
    
    # Apply search filter
    if search_query:
        venues = venues.filter(
            Q(name__icontains=search_query) | 
            Q(address__icontains=search_query)
        )
    
    venues = venues.order_by('city__name', 'name')
    
    context = {
        'venues': venues,
        'cities': City.objects.filter(is_active=True),
        'selected_city_id': city_id,
        'search_query': search_query,
    }
    return render(request, 'venue_list.html', context)


def venue_detail(request, venue_id):
    """Venue detail page showing upcoming events"""
    venue = get_object_or_404(Venue, id=venue_id, is_active=True)
    
    # Get selected date or default to today
    from datetime import datetime, timedelta
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Generate date options (next 7 days)
    date_options = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        date_options.append(date)
    
    # Get all shows for this venue on the selected date
    shows = Show.objects.filter(
        venue=venue,
        show_date=selected_date,
        is_active=True
    ).select_related('event').order_by('event', 'show_time')
    
    # Group shows by event
    from collections import defaultdict
    events_with_shows = defaultdict(list)
    for show in shows:
        events_with_shows[show.event].append(show)
    
    context = {
        'venue': venue,
        'events_with_shows': dict(events_with_shows),
        'selected_date': selected_date,
        'date_options': date_options,
    }
    return render(request, 'venue_detail.html', context)


# ============= AUTHENTICATION =============

def user_login(request):
    """User login"""
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check if user is active (email verified)
            if not user.is_active:
                # Resend OTP if needed
                otp_code = generate_otp(user, 'registration')
                send_otp_email(user, otp_code, 'registration')
                request.session['registration_user_id'] = user.id
                messages.info(request, 'Your account is not verified. A new verification code has been sent.')
                return redirect('booking:verify_registration_otp')
            
            # Check approval status for organizers and theatre owners
            if user.role == 'organizer':
                try:
                    profile = user.organizer_profile
                    if profile.status == 'pending':
                        messages.warning(request, 'Your account is pending admin approval. Please wait for approval before logging in.')
                        return redirect('booking:login')
                    elif profile.status == 'rejected':
                        messages.error(request, 'Your account application has been rejected. Please contact support for more information.')
                        return redirect('booking:login')
                    elif profile.status == 'suspended':
                        messages.error(request, 'Your account has been suspended. Please contact support.')
                        return redirect('booking:login')
                except:
                    messages.error(request, 'Organizer profile not found.')
                    return redirect('booking:login')
                    
            elif user.role == 'theatre_owner':
                try:
                    profile = user.theatre_profile
                    if profile.status == 'pending':
                        messages.warning(request, 'Your account is pending admin approval. Please wait for approval before logging in.')
                        return redirect('booking:login')
                    elif profile.status == 'rejected':
                        messages.error(request, 'Your account application has been rejected. Please contact support for more information.')
                        return redirect('booking:login')
                    elif profile.status == 'suspended':
                        messages.error(request, 'Your account has been suspended. Please contact support.')
                        return redirect('booking:login')
                except:
                    messages.error(request, 'Theatre owner profile not found.')
                    return redirect('booking:login')
                
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return _redirect_after_login(user)
        else:
            # If form is not valid, check if it's due to an inactive user
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if username and password:
                # Try to authenticate manually to distinguish between wrong credentials and inactive user
                # authenticate() returns None for inactive users by default.
                # We check manually if the user exists and has correct password.
                try:
                    check_user = CustomUser.objects.get(username=username)
                    if not check_user.is_active and check_user.check_password(password):
                        # Correct credentials but account inactive
                        otp_code = generate_otp(check_user, 'registration')
                        send_otp_email(check_user, otp_code, 'registration')
                        request.session['registration_user_id'] = check_user.id
                        messages.info(request, 'Your account is not verified. A new verification code has been sent.')
                        return redirect('booking:verify_registration_otp')
                except CustomUser.DoesNotExist:
                    pass # User does not exist, let the form errors handle it
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


def verify_registration_otp(request):
    """Verify OTP for new account registration"""
    user_id = request.session.get('registration_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('booking:customer_register')
        
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Check OTP
            otp = OTP.objects.filter(user=user, otp_code=otp_code, purpose='registration', is_used=False).first()
            
            if otp and otp.is_valid():
                otp.is_used = True
                otp.save()
                
                # Activate User
                user.is_active = True
                user.email_verified = True
                user.save()
                
                del request.session['registration_user_id']
                
                # Check if user needs approval before login
                if user.role == 'organizer':
                    try:
                        profile = user.organizer_profile
                        if profile.status != 'approved':
                            messages.success(request, 'Email verified successfully! Your account is pending admin approval. You will be notified once approved.')
                            return redirect('booking:login')
                    except:
                        pass
                        
                elif user.role == 'theatre_owner':
                    try:
                        profile = user.theatre_profile
                        if profile.status != 'approved':
                            messages.success(request, 'Email verified successfully! Your account is pending admin approval. You will be notified once approved.')
                            return redirect('booking:login')
                    except:
                        pass
                
                # For customers or approved organizers/theatre owners, log them in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Account verified successfully!')
                return _redirect_after_login(user)
            else:
                messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPVerifyForm()
    
    return render(request, 'auth/verify_otp.html', {
        'form': form, 
        'email': user.email,
        'title': 'Verify Registration',
        'subtitle': f'Please enter the 6-digit code sent to {user.email} to verify your account.'
    })


def _redirect_after_login(user):
    """Helper to redirect based on role"""
    if user.role == 'customer':
        return redirect('booking:home')
    elif user.role == 'organizer':
        return redirect('booking:organizer_dashboard')
    elif user.role == 'theatre_owner':
        return redirect('booking:theatre_dashboard')
    elif user.role == 'admin' or user.is_superuser:
        return redirect('booking:admin_dashboard')
    return redirect('booking:home')


def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('booking:home')


def customer_register(request):
    """Customer registration"""
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until OTP verified
            user.save()
            
            # Generate & Send OTP
            otp_code = generate_otp(user, 'registration')
            send_otp_email(user, otp_code, 'registration')
            
            request.session['registration_user_id'] = user.id
            messages.success(request, 'Registration successful! Please verify your email.')
            return redirect('booking:verify_registration_otp')
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def organizer_register(request):
    """Event organizer registration"""
    if request.method == 'POST':
        form = OrganizerRegistrationForm(request.POST)
        if form.is_valid():
            # Create user account
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                role='organizer',
                is_active=False  # Deactivate until OTP verified
            )
            
            # Create organizer profile
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Generate & Send OTP
            otp_code = generate_otp(user, 'registration')
            send_otp_email(user, otp_code, 'registration')
            
            # Send pending approval email
            from .utils import send_registration_pending_email
            send_registration_pending_email(user, 'Event Organizer')
            
            request.session['registration_user_id'] = user.id
            messages.success(request, 'Registration submitted! Please verify your email.')
            return redirect('booking:verify_registration_otp')
    else:
        form = OrganizerRegistrationForm()
    
    return render(request, 'auth/organizer_register.html', {'form': form})


def theatre_register(request):
    """Theatre owner registration"""
    if request.method == 'POST':
        form = TheatreOwnerRegistrationForm(request.POST)
        if form.is_valid():
            # Create user account
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                role='theatre_owner',
                is_active=False  # Deactivate until OTP verified
            )
            
            # Create theatre owner profile
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Generate & Send OTP
            otp_code = generate_otp(user, 'registration')
            send_otp_email(user, otp_code, 'registration')
            
            # Send pending approval email
            from .utils import send_registration_pending_email
            send_registration_pending_email(user, 'Theatre Owner')
            
            request.session['registration_user_id'] = user.id
            messages.success(request, 'Registration submitted! Please verify your email.')
            return redirect('booking:verify_registration_otp')
    else:
        form = TheatreOwnerRegistrationForm()
    
    return render(request, 'auth/theatre_register.html', {'form': form})


def verify_email(request, token):
    """Verify email address (Legacy - can be removed or kept for backward compatibility)"""
    try:
        user = CustomUser.objects.get(verification_token=token)
        user.email_verified = True
        user.is_active = True  # Activate account
        user.verification_token = ''
        user.save()
        messages.success(request, 'Email verified successfully! You can now login.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('booking:login')


def password_reset_request(request):
    """Password reset request with OTP"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Generate & Send OTP
                otp_code = generate_otp(user, 'reset_password')
                send_otp_email(user, otp_code, 'reset_password')
                
                request.session['reset_otp_email'] = email
                messages.success(request, 'OTP sent to your email.')
                return redirect('booking:verify_reset_otp')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'No account found with this email.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'auth/password_reset.html', {'form': form})


def verify_reset_otp(request):
    """Verify OTP for password reset"""
    email = request.session.get('reset_otp_email')
    if not email:
        return redirect('booking:password_reset')
        
    user = get_object_or_404(CustomUser, email=email)
    
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            otp = OTP.objects.filter(user=user, otp_code=otp_code, purpose='reset_password', is_used=False).first()
            
            if otp and otp.is_valid():
                otp.is_used = True
                otp.save()
                
                request.session['reset_verified'] = True
                return redirect('booking:set_new_password')
            else:
                messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPVerifyForm()
        
    return render(request, 'auth/password_reset_otp.html', {'form': form, 'email': email})


def set_new_password(request):
    """Set new password after OTP verification"""
    email = request.session.get('reset_otp_email')
    if not email or not request.session.get('reset_verified'):
        return redirect('booking:password_reset')
        
    user = get_object_or_404(CustomUser, email=email)
    
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Clear session
            if 'reset_otp_email' in request.session: del request.session['reset_otp_email']
            if 'reset_verified' in request.session: del request.session['reset_verified']
            
            messages.success(request, 'Password verified successfully! Please login.')
            return redirect('booking:login')
    else:
        form = SetNewPasswordForm()
        
    return render(request, 'auth/set_new_password.html', {'form': form})



# ============= CUSTOMER PAGES =============

@customer_required
def customer_dashboard(request):
    """Customer dashboard"""
    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        show__show_date__gte=timezone.now().date(),
        payment_status='completed'
    ).order_by('show__show_date', 'show__show_time')[:5]
    
    context = {
        'upcoming_bookings': upcoming_bookings,
    }
    return render(request, 'customer/dashboard.html', context)


@customer_required
def seat_selection(request, show_id):
    """Seat selection page"""
    show = get_object_or_404(Show, id=show_id, is_active=True)
    
    # Release expired locks
    release_expired_locks()
    
    # Get all seats for this show
    seats = show.seats.all().order_by('row', 'seat_number')
    
    # Get seat bookings
    seat_bookings = SeatBooking.objects.filter(show=show).select_related('seat')
    
    # Create seat status map
    seat_status = {}
    for booking in seat_bookings:
        if booking.status == 'booked':
            seat_status[booking.seat.id] = 'booked'
        elif booking.status == 'locked' and not booking.is_lock_expired():
            if booking.user == request.user:
                seat_status[booking.seat.id] = 'my_lock'
            else:
                seat_status[booking.seat.id] = 'locked'
    
    context = {
        'show': show,
        'seats': seats,
        'seat_status': seat_status,
    }
    return render(request, 'customer/seat_selection.html', context)


@customer_required
def payment(request, show_id):
    """Payment page"""
    show = get_object_or_404(Show, id=show_id)
    
    if request.method == 'POST':
        seat_ids = request.POST.getlist('seats')
        payment_method = request.POST.get('payment_method')
        
        if not seat_ids:
            messages.error(request, 'Please select at least one seat.')
            return redirect('booking:seat_selection', show_id=show_id)
        
        seats = Seat.objects.filter(id__in=seat_ids, show=show)
        total_amount = sum(seat.price for seat in seats)
        convenience_fee = total_amount * Decimal('0.02')  # 2% convenience fee
        
        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            show=show,
            total_amount=total_amount,
            convenience_fee=convenience_fee,
            payment_method=payment_method,
            payment_status='pending'
        )
        booking.seats.set(seats)
        
        # Simulate payment
        success, message = simulate_payment(booking, payment_method)
        
        if success:
            messages.success(request, message)
            return redirect('booking:booking_success', booking_id=booking.id)
        else:
            messages.error(request, message)
            return redirect('booking:seat_selection', show_id=show_id)
    
    # GET request - show payment form
    seat_ids = request.GET.getlist('seats')
    if not seat_ids:
        messages.error(request, 'Please select seats first.')
        return redirect('booking:seat_selection', show_id=show_id)
    
    seats = Seat.objects.filter(id__in=seat_ids, show=show)
    total_amount = sum(seat.price for seat in seats)
    convenience_fee = total_amount * Decimal('0.02')
    grand_total = total_amount + convenience_fee
    
    # Lock seats for this user
    lock_seats(seats, request.user, show)
    
    context = {
        'show': show,
        'seats': seats,
        'total_amount': total_amount,
        'convenience_fee': convenience_fee,
        'grand_total': grand_total,
    }
    return render(request, 'customer/payment.html', context)


@customer_required
def booking_success(request, booking_id):
    """Booking success page"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
    }
    return render(request, 'customer/booking_success.html', context)


@customer_required
def my_tickets(request):
    """My tickets page"""
    tickets = Ticket.objects.filter(
        booking__user=request.user,
        booking__payment_status='completed'
    ).select_related('booking', 'seat', 'booking__show').order_by('-created_at')
    
    context = {
        'tickets': tickets,
    }
    return render(request, 'customer/my_tickets.html', context)


@customer_required
def booking_history(request):
    """Booking history page"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'customer/booking_history.html', context)


@customer_required
def ticket_detail(request, ticket_id):
    """Ticket detail page"""
    ticket = get_object_or_404(Ticket, id=ticket_id, booking__user=request.user)
    
    context = {
        'ticket': ticket,
    }
    return render(request, 'customer/ticket_detail.html', context)


# ============= EVENT ORGANIZER PAGES =============

@organizer_required
def organizer_dashboard(request):
    """Event organizer dashboard"""
    try:
        profile = request.user.organizer_profile
    except:
        messages.error(request, 'Organizer profile not found.')
        return redirect('booking:home')
    
    events = Event.objects.filter(organizer=profile).order_by('-created_at')[:5]
    venues = Venue.objects.filter(organizer=profile)[:5]
    
    # Get total bookings
    total_bookings = Booking.objects.filter(
        show__event__organizer=profile,
        payment_status='completed'
    ).count()
    
    context = {
        'profile': profile,
        'events': events,
        'venues': venues,
        'total_bookings': total_bookings,
    }
    return render(request, 'organizer/dashboard.html', context)


@approved_organizer_required
def manage_events(request):
    """Manage events"""
    profile = request.user.organizer_profile
    events = Event.objects.filter(organizer=profile).order_by('-created_at')
    
    context = {
        'events': events,
    }
    return render(request, 'organizer/manage_events.html', context)


@approved_organizer_required
def create_event(request):
    """Create new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user.organizer_profile
            event.save()
            messages.success(request, 'Event created successfully! It is pending admin approval.')
            return redirect('booking:manage_events')
    else:
        form = EventForm()
    
    return render(request, 'organizer/event_form.html', {'form': form, 'title': 'Create Event'})


@approved_organizer_required
def edit_event(request, event_id):
    """Edit event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user.organizer_profile)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('booking:manage_events')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'organizer/event_form.html', {'form': form, 'event': event, 'title': 'Edit Event'})


@approved_organizer_required
def delete_event(request, event_id):
    """Delete event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user.organizer_profile)
    event.delete()
    messages.success(request, 'Event deleted successfully!')
    return redirect('booking:manage_events')


@approved_organizer_required
def manage_venues(request):
    """Manage venues"""
    profile = request.user.organizer_profile
    venues = Venue.objects.filter(organizer=profile).order_by('-created_at')
    
    context = {
        'venues': venues,
    }
    return render(request, 'organizer/manage_venues.html', context)


@approved_organizer_required
def create_venue(request):
    """Create new venue"""
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.organizer = request.user.organizer_profile
            venue.save()
            messages.success(request, 'Venue created successfully!')
            return redirect('booking:manage_venues')
    else:
        form = VenueForm()
    
    return render(request, 'organizer/venue_form.html', {'form': form, 'title': 'Create Venue'})


@approved_organizer_required
def edit_venue(request, venue_id):
    """Edit venue"""
    venue = get_object_or_404(Venue, id=venue_id, organizer=request.user.organizer_profile)
    
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue updated successfully!')
            return redirect('booking:manage_venues')
    else:
        form = VenueForm(instance=venue)
    
    return render(request, 'organizer/venue_form.html', {'form': form, 'venue': venue, 'title': 'Edit Venue'})


@approved_organizer_required
def delete_venue(request, venue_id):
    """Delete venue"""
    venue = get_object_or_404(Venue, id=venue_id, organizer=request.user.organizer_profile)
    
    if request.method == 'POST':
        venue.delete()
        messages.success(request, 'Venue deleted successfully!')
        return redirect('booking:manage_venues')
        
    return render(request, 'organizer/confirm_delete_venue.html', {'object': venue})


@approved_organizer_required
def configure_venue_layout(request, venue_id):
    """Configure seat layout for a venue"""
    venue = get_object_or_404(Venue, id=venue_id, organizer=request.user.organizer_profile)
    
    if request.method == 'POST':
        import json
        
        venue.rows = int(request.POST.get('rows', 8))
        venue.seats_per_row = int(request.POST.get('seats_per_row', 20))
        
        # Parse seat layout from JSON
        seat_layout_json = request.POST.get('seat_layout', '{}')
        try:
            venue.seat_layout = json.loads(seat_layout_json)
        except:
            venue.seat_layout = {}
        
        # Parse price tiers from JSON
        price_tiers_json = request.POST.get('price_tiers', '{}')
        try:
            venue.price_tiers = json.loads(price_tiers_json)
        except:
            venue.price_tiers = {}
        
        # Calculate total seats from layout
        total = 0
        for row_data in venue.seat_layout.values():
            if isinstance(row_data, dict) and 'seats' in row_data:
                total += len(row_data['seats'])
        venue.capacity = total if total > 0 else venue.rows * venue.seats_per_row
        
        venue.save()
        messages.success(request, f'Seat layout configured! Total seats: {venue.capacity}')
        return redirect('booking:manage_venues')
    
    context = {
        'venue': venue,
    }
    return render(request, 'organizer/configure_venue_layout.html', context)


@approved_organizer_required
def schedule_event_show(request, event_id):
    """Bulk schedule shows for an event across multiple days"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user.organizer_profile)
    venues = Venue.objects.filter(organizer=request.user.organizer_profile, is_active=True)
    
    if request.method == 'POST':
        import json
        from datetime import datetime, timedelta
        
        # Get date range
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get selected venue
        venue_id = request.POST.get('venue')
        venue = get_object_or_404(Venue, id=venue_id, organizer=request.user.organizer_profile)
        
        # Get timing configurations
        weekday_timings_json = request.POST.get('weekday_timings', '[]')
        weekend_timings_json = request.POST.get('weekend_timings', '[]')
        
        try:
            weekday_timings = json.loads(weekday_timings_json)
            weekend_timings = json.loads(weekend_timings_json)
        except:
            weekday_timings = []
            weekend_timings = []
        
        # Generate shows
        shows_created = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Determine if weekend
            is_weekend = current_date.weekday() >= 5
            timings = weekend_timings if is_weekend else weekday_timings
            
            # Create shows for each timing
            for timing in timings:
                try:
                    show_time = datetime.strptime(timing, '%H:%M').time()
                    
                    # Check if show already exists
                    existing = Show.objects.filter(
                        show_type='event',
                        event=event,
                        venue=venue,
                        show_date=current_date,
                        show_time=show_time
                    ).exists()
                    
                    if not existing:
                        Show.objects.create(
                            show_type='event',
                            event=event,
                            venue=venue,
                            show_date=current_date,
                            show_time=show_time
                        )
                        shows_created += 1
                except Exception as e:
                    continue
            
            current_date += timedelta(days=1)
        
        messages.success(request, f'Successfully created {shows_created} shows!')
        return redirect('booking:manage_events')
    
    context = {
        'event': event,
        'venues': venues,
    }
    return render(request, 'organizer/schedule_event_bulk.html', context)


@approved_organizer_required
def configure_event_seats(request, show_id):
    """Configure seats for event show"""
    show = get_object_or_404(Show, id=show_id, event__organizer=request.user.organizer_profile)
    
    if request.method == 'POST':
        # Bulk seat creation
        rows = request.POST.get('rows', '').split(',')
        seats_per_row = int(request.POST.get('seats_per_row', 10))
        seat_types = request.POST.getlist('seat_types')
        prices = request.POST.getlist('prices')
        
        for row in rows:
            row = row.strip()
            for i in range(1, seats_per_row + 1):
                # Determine seat type based on position
                if i <= seats_per_row // 3:
                    seat_type_idx = 0
                elif i <= 2 * seats_per_row // 3:
                    seat_type_idx = min(1, len(seat_types) - 1)
                else:
                    seat_type_idx = min(2, len(seat_types) - 1)
                
                Seat.objects.create(
                    show=show,
                    row=row,
                    seat_number=str(i),
                    seat_type=seat_types[seat_type_idx] if seat_type_idx < len(seat_types) else 'silver',
                    price=prices[seat_type_idx] if seat_type_idx < len(prices) else show.base_price
                )
        
        messages.success(request, 'Seats configured successfully!')
        return redirect('booking:manage_events')
    
    context = {
        'show': show,
    }
    return render(request, 'organizer/configure_seats.html', context)


@approved_organizer_required
def organizer_analytics(request):
    """Organizer analytics"""
    profile = request.user.organizer_profile
    
    # Get booking statistics
    total_bookings = Booking.objects.filter(
        show__event__organizer=profile,
        payment_status='completed'
    ).count()
    
    total_revenue = Booking.objects.filter(
        show__event__organizer=profile,
        payment_status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Event-wise bookings
    event_stats = Event.objects.filter(organizer=profile).annotate(
        booking_count=Count('shows__bookings', filter=Q(shows__bookings__payment_status='completed'))
    ).order_by('-booking_count')[:10]
    
    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'event_stats': event_stats,
    }
    return render(request, 'organizer/analytics.html', context)


# ============= THEATRE OWNER PAGES =============

@theatre_owner_required
def theatre_dashboard(request):
    """Theatre owner dashboard"""
    try:
        profile = request.user.theatre_profile
    except:
        messages.error(request, 'Theatre owner profile not found.')
        return redirect('booking:home')
    
    movies = Movie.objects.filter(theatre_owner=profile).order_by('-created_at')[:5]
    theatres = Theatre.objects.filter(owner=profile)[:5]
    
    # Get total bookings
    total_bookings = Booking.objects.filter(
        show__movie__theatre_owner=profile,
        payment_status='completed'
    ).count()
    
    context = {
        'profile': profile,
        'movies': movies,
        'theatres': theatres,
        'total_bookings': total_bookings,
    }
    return render(request, 'theatre/dashboard.html', context)


@approved_theatre_owner_required
def manage_movies(request):
    """Manage movies"""
    profile = request.user.theatre_profile
    movies = Movie.objects.filter(theatre_owner=profile).order_by('-created_at')
    
    context = {
        'movies': movies,
    }
    return render(request, 'theatre/manage_movies.html', context)


@approved_theatre_owner_required
def create_movie(request):
    """Create new movie"""
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save(commit=False)
            movie.theatre_owner = request.user.theatre_profile
            movie.save()
            messages.success(request, 'Movie added successfully! It is pending admin approval.')
            return redirect('booking:manage_movies')
    else:
        form = MovieForm()
    
    return render(request, 'theatre/movie_form.html', {'form': form, 'title': 'Add Movie'})


@approved_theatre_owner_required
def edit_movie(request, movie_id):
    """Edit movie"""
    movie = get_object_or_404(Movie, id=movie_id, theatre_owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, 'Movie updated successfully!')
            return redirect('booking:manage_movies')
    else:
        form = MovieForm(instance=movie)
    
    return render(request, 'theatre/movie_form.html', {'form': form, 'movie': movie, 'title': 'Edit Movie'})


@approved_theatre_owner_required
def delete_movie(request, movie_id):
    """Delete movie"""
    movie = get_object_or_404(Movie, id=movie_id, theatre_owner=request.user.theatre_profile)
    movie.delete()
    messages.success(request, 'Movie deleted successfully!')
    return redirect('booking:manage_movies')


@approved_theatre_owner_required
def manage_theatres(request):
    """Manage theatres"""
    profile = request.user.theatre_profile
    theatres = Theatre.objects.filter(owner=profile).order_by('-created_at')
    
    context = {
        'theatres': theatres,
    }
    return render(request, 'theatre/manage_theatres.html', context)


@approved_theatre_owner_required
def create_theatre(request):
    """Create new theatre"""
    if request.method == 'POST':
        form = TheatreForm(request.POST)
        if form.is_valid():
            theatre = form.save(commit=False)
            theatre.owner = request.user.theatre_profile
            theatre.save()
            messages.success(request, 'Theatre created successfully!')
            return redirect('booking:manage_theatres')
    else:
        form = TheatreForm()
    
    return render(request, 'theatre/theatre_form.html', {'form': form, 'title': 'Add Theatre'})


@approved_theatre_owner_required
def edit_theatre(request, theatre_id):
    """Edit theatre"""
    theatre = get_object_or_404(Theatre, id=theatre_id, owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        form = TheatreForm(request.POST, instance=theatre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Theatre updated successfully!')
            return redirect('booking:manage_theatres')
    else:
        form = TheatreForm(instance=theatre)
    
    return render(request, 'theatre/theatre_form.html', {'form': form, 'theatre': theatre, 'title': 'Edit Theatre'})


@approved_theatre_owner_required
def manage_screens(request, theatre_id):
    """Manage screens for a theatre"""
    theatre = get_object_or_404(Theatre, id=theatre_id, owner=request.user.theatre_profile)
    screens = Screen.objects.filter(theatre=theatre)
    
    context = {
        'theatre': theatre,
        'screens': screens,
    }
    return render(request, 'theatre/manage_screens.html', context)


@approved_theatre_owner_required
def create_screen(request, theatre_id):
    """Create new screen"""
    theatre = get_object_or_404(Theatre, id=theatre_id, owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        form = ScreenForm(request.POST)
        if form.is_valid():
            screen = form.save(commit=False)
            screen.theatre = theatre
            screen.save()
            messages.success(request, 'Screen created successfully!')
            return redirect('booking:manage_screens', theatre_id=theatre_id)
    else:
        form = ScreenForm()
    
    context = {
        'form': form,
        'theatre': theatre,
    }
    return render(request, 'theatre/screen_form.html', context)


@approved_theatre_owner_required
def edit_screen(request, screen_id):
    """Edit screen"""
    screen = get_object_or_404(Screen, id=screen_id, theatre__owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        form = ScreenForm(request.POST, instance=screen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Screen updated successfully!')
            return redirect('booking:manage_theatres')
    else:
        form = ScreenForm(instance=screen)
    
    context = {
        'form': form,
        'theatre': screen.theatre,
        'screen': screen,
        'title': 'Edit Screen'
    }
    return render(request, 'theatre/screen_form.html', context)


@approved_theatre_owner_required
def configure_screen_layout(request, screen_id):
    """Configure seat layout for a screen"""
    screen = get_object_or_404(Screen, id=screen_id, theatre__owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        import json
        
        # Update screen format if changed
        screen.screen_type = request.POST.get('screen_type', screen.screen_type)
        screen.rows = int(request.POST.get('rows', 10))
        screen.seats_per_row = int(request.POST.get('seats_per_row', 15))
        
        # Parse seat layout from JSON
        seat_layout_json = request.POST.get('seat_layout', '{}')
        try:
            screen.seat_layout = json.loads(seat_layout_json)
        except:
            screen.seat_layout = {}
        
        # Parse price tiers from JSON
        price_tiers_json = request.POST.get('price_tiers', '{}')
        try:
            screen.price_tiers = json.loads(price_tiers_json)
        except:
            screen.price_tiers = {}
        
        # Calculate total seats from layout
        total = 0
        for row_data in screen.seat_layout.values():
            if isinstance(row_data, dict) and 'seats' in row_data:
                total += len(row_data['seats'])
        screen.total_seats = total if total > 0 else screen.rows * screen.seats_per_row
        
        screen.save()
        messages.success(request, f'Seat layout configured! Total seats: {screen.total_seats}')
        return redirect('booking:manage_screens', theatre_id=screen.theatre.id)
    
    context = {
        'screen': screen,
        'format_choices': Screen.SCREEN_FORMAT_CHOICES,
    }
    return render(request, 'theatre/configure_screen_layout.html', context)


@approved_theatre_owner_required
def schedule_movie_show(request, movie_id):
    """Bulk schedule shows for a movie across multiple days and screens"""
    movie = get_object_or_404(Movie, id=movie_id, theatre_owner=request.user.theatre_profile)
    theatres = Theatre.objects.filter(owner=request.user.theatre_profile, is_active=True)
    screens = Screen.objects.filter(theatre__owner=request.user.theatre_profile, is_active=True)
    
    if request.method == 'POST':
        import json
        from datetime import datetime, timedelta
        
        # Get date range
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get selected screens
        selected_screen_ids = request.POST.getlist('screens')
        selected_screens = Screen.objects.filter(id__in=selected_screen_ids)
        
        # Get show format
        show_format = request.POST.get('show_format', '2D')
        
        # Get timing configurations
        weekday_timings_json = request.POST.get('weekday_timings', '[]')
        weekend_timings_json = request.POST.get('weekend_timings', '[]')
        
        try:
            weekday_timings = json.loads(weekday_timings_json)
            weekend_timings = json.loads(weekend_timings_json)
        except:
            weekday_timings = []
            weekend_timings = []
        
        # Generate shows
        shows_created = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Determine if weekend (5=Saturday, 6=Sunday)
            is_weekend = current_date.weekday() >= 5
            timings = weekend_timings if is_weekend else weekday_timings
            
            # Create shows for each selected screen and timing
            for screen in selected_screens:
                for timing in timings:
                    try:
                        show_time = datetime.strptime(timing, '%H:%M').time()
                        
                        # Check if show already exists
                        existing = Show.objects.filter(
                            show_type='movie',
                            movie=movie,
                            screen=screen,
                            show_date=current_date,
                            show_time=show_time
                        ).exists()
                        
                        if not existing:
                            Show.objects.create(
                                show_type='movie',
                                movie=movie,
                                screen=screen,
                                show_date=current_date,
                                show_time=show_time,
                                show_format=show_format
                            )
                            shows_created += 1
                    except Exception as e:
                        continue
            
            current_date += timedelta(days=1)
        
        messages.success(request, f'Successfully created {shows_created} shows!')
        return redirect('booking:manage_movies')
    
    context = {
        'movie': movie,
        'theatres': theatres,
        'screens': screens,
    }
    return render(request, 'theatre/schedule_movie_bulk.html', context)


@approved_theatre_owner_required
def configure_movie_seats(request, show_id):
    """Configure seats for movie show"""
    show = get_object_or_404(Show, id=show_id, movie__theatre_owner=request.user.theatre_profile)
    
    if request.method == 'POST':
        # Bulk seat creation
        rows = request.POST.get('rows', '').split(',')
        seats_per_row = int(request.POST.get('seats_per_row', 10))
        seat_types = request.POST.getlist('seat_types')
        prices = request.POST.getlist('prices')
        
        for row in rows:
            row = row.strip()
            for i in range(1, seats_per_row + 1):
                # Determine seat type based on position
                if i <= seats_per_row // 3:
                    seat_type_idx = 0
                elif i <= 2 * seats_per_row // 3:
                    seat_type_idx = min(1, len(seat_types) - 1)
                else:
                    seat_type_idx = min(2, len(seat_types) - 1)
                
                Seat.objects.create(
                    show=show,
                    row=row,
                    seat_number=str(i),
                    seat_type=seat_types[seat_type_idx] if seat_type_idx < len(seat_types) else 'silver',
                    price=prices[seat_type_idx] if seat_type_idx < len(prices) else show.base_price
                )
        
        messages.success(request, 'Seats configured successfully!')
        return redirect('booking:manage_movies')
    
    context = {
        'show': show,
    }
    return render(request, 'theatre/configure_seats.html', context)


@approved_theatre_owner_required
def theatre_analytics(request):
    """Theatre analytics"""
    profile = request.user.theatre_profile
    
    # Get booking statistics
    total_bookings = Booking.objects.filter(
        show__movie__theatre_owner=profile,
        payment_status='completed'
    ).count()
    
    total_revenue = Booking.objects.filter(
        show__movie__theatre_owner=profile,
        payment_status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Movie-wise bookings
    movie_stats = Movie.objects.filter(theatre_owner=profile).annotate(
        booking_count=Count('shows__bookings', filter=Q(shows__bookings__payment_status='completed'))
    ).order_by('-booking_count')[:10]
    
    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'movie_stats': movie_stats,
    }
    return render(request, 'theatre/analytics.html', context)


# ============= ADMIN PAGES =============

@admin_required
def admin_dashboard(request):
    """Admin dashboard"""
    # Get QuerySets for tables
    pending_organizers_qs = OrganizerProfile.objects.filter(status='pending')
    pending_theatres_qs = TheatreOwnerProfile.objects.filter(status='pending')
    pending_events_qs = Event.objects.filter(status='pending').select_related('organizer', 'category')
    pending_movies_qs = Movie.objects.filter(status='pending').select_related('theatre_owner', 'language')
    
    # Get counts for statistics
    pending_organizers_count = pending_organizers_qs.count()
    pending_theatres_count = pending_theatres_qs.count()
    pending_events_count = pending_events_qs.count()
    pending_movies_count = pending_movies_qs.count()
    
    pending_approvals = pending_organizers_count + pending_theatres_count + pending_events_count + pending_movies_count
    
    total_users = CustomUser.objects.filter(role='customer').count()
    total_bookings = Booking.objects.filter(payment_status='completed').count()
    total_revenue = Booking.objects.filter(payment_status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get recent users
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    context = {
        'pending_organizers': pending_organizers_qs,
        'pending_theatres': pending_theatres_qs,
        'pending_events': pending_events_qs,
        'pending_movies': pending_movies_qs,
        'pending_approvals': pending_approvals,
        'total_users': total_users,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_users(request):
    """Manage users"""
    users = CustomUser.objects.filter(role='customer').order_by('-date_joined')
    
    context = {
        'users': users,
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_organizers(request):
    """Manage organizers - redirects to dashboard with approvals section"""
    return redirect('booking:admin_dashboard')


@admin_required
def approve_organizer(request, profile_id):
    """Approve organizer"""
    profile = get_object_or_404(OrganizerProfile, id=profile_id)
    profile.status = 'approved'
    profile.approved_at = timezone.now()
    profile.save()
    
    # Send approval email
    from .utils import send_approval_email
    send_approval_email(profile.user, 'Event Organizer')
    
    messages.success(request, f'{profile.organization_name} approved successfully!')
    return redirect('booking:admin_dashboard')


@admin_required
def reject_organizer(request, profile_id):
    """Reject organizer"""
    profile = get_object_or_404(OrganizerProfile, id=profile_id)
    profile.status = 'rejected'
    profile.save()
    messages.warning(request, f'{profile.organization_name} rejected.')
    return redirect('booking:admin_dashboard')


@admin_required
def admin_theatre_owners(request):
    """Manage theatre owners - redirects to dashboard with approvals section"""
    return redirect('booking:admin_dashboard')


@admin_required
def approve_theatre_owner(request, profile_id):
    """Approve theatre owner"""
    profile = get_object_or_404(TheatreOwnerProfile, id=profile_id)
    profile.status = 'approved'
    profile.approved_at = timezone.now()
    profile.save()
    
    # Send approval email
    from .utils import send_approval_email
    send_approval_email(profile.user, 'Theatre Owner')
    
    messages.success(request, f'{profile.theatre_chain_name} approved successfully!')
    return redirect('booking:admin_dashboard')


@admin_required
def reject_theatre_owner(request, profile_id):
    """Reject theatre owner"""
    profile = get_object_or_404(TheatreOwnerProfile, id=profile_id)
    profile.status = 'rejected'
    profile.save()
    messages.warning(request, f'{profile.theatre_chain_name} rejected.')
    return redirect('booking:admin_dashboard')


@admin_required
def admin_events(request):
    """Manage events - redirects to dashboard with approvals section"""
    return redirect('booking:admin_dashboard')


@admin_required
def approve_event(request, event_id):
    """Approve event"""
    event = get_object_or_404(Event, id=event_id)
    event.status = 'approved'
    event.save()
    messages.success(request, f'{event.title} approved successfully!')
    return redirect('booking:admin_dashboard')


@admin_required
def reject_event(request, event_id):
    """Reject event"""
    event = get_object_or_404(Event, id=event_id)
    event.status = 'rejected'
    event.save()
    messages.warning(request, f'{event.title} rejected.')
    return redirect('booking:admin_dashboard')


@admin_required
def admin_movies(request):
    """Manage movies - redirects to dashboard with approvals section"""
    return redirect('booking:admin_dashboard')


@admin_required
def approve_movie(request, movie_id):
    """Approve movie"""
    movie = get_object_or_404(Movie, id=movie_id)
    movie.status = 'approved'
    movie.save()
    messages.success(request, f'{movie.title} approved successfully!')
    return redirect('booking:admin_dashboard')


@admin_required
def reject_movie(request, movie_id):
    """Reject movie"""
    movie = get_object_or_404(Movie, id=movie_id)
    movie.status = 'rejected'
    movie.save()
    messages.warning(request, f'{movie.title} rejected.')
    return redirect('booking:admin_dashboard')


@admin_required
def admin_reports(request):
    """Admin reports"""
    # Booking statistics by date
    from django.db.models.functions import TruncDate
    
    bookings_by_date = Booking.objects.filter(
        payment_status='completed'
    ).annotate(
        date=TruncDate('booking_date')
    ).values('date').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-date')[:30]
    
    # Top events
    top_events = Event.objects.annotate(
        booking_count=Count('shows__bookings', filter=Q(shows__bookings__payment_status='completed'))
    ).order_by('-booking_count')[:10]
    
    # Top movies
    top_movies = Movie.objects.annotate(
        booking_count=Count('shows__bookings', filter=Q(shows__bookings__payment_status='completed'))
    ).order_by('-booking_count')[:10]
    
    context = {
        'bookings_by_date': bookings_by_date,
        'top_events': top_events,
        'top_movies': top_movies,
    }
    return render(request, 'admin_panel/reports.html', context)


# ============= AJAX ENDPOINTS =============

@login_required
def check_seat_availability(request, show_id):
    """Check seat availability (AJAX)"""
    show = get_object_or_404(Show, id=show_id)
    release_expired_locks()
    
    available_seats = get_available_seats(show)
    available_seat_ids = list(available_seats.values_list('id', flat=True))
    
    return JsonResponse({
        'available_seats': available_seat_ids,
        'total_available': len(available_seat_ids)
    })


@login_required
def lock_seats_api(request, show_id):
    """Lock seats (AJAX)"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        seat_ids = data.get('seat_ids', [])
        
        show = get_object_or_404(Show, id=show_id)
        seats = Seat.objects.filter(id__in=seat_ids, show=show)
        
        # Check if seats are available
        available_seats = get_available_seats(show)
        if not all(seat in available_seats for seat in seats):
            return JsonResponse({'success': False, 'message': 'Some seats are no longer available'})
        
        # Lock seats
        lock_seats(seats, request.user, show)
        
        return JsonResponse({'success': True, 'message': 'Seats locked successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def scan_ticket_page(request):
    """Render the QR scanner page for authorized users"""
    is_authorized = False
    
    if hasattr(request.user, 'theatre_profile') and request.user.theatre_profile.status == 'approved':
        is_authorized = True
    elif hasattr(request.user, 'organizer_profile') and request.user.organizer_profile.status == 'approved':
        is_authorized = True
        
    if not is_authorized:
        messages.error(request, "You are not authorized to access the scanner.")
        return redirect('booking:home')
        
    return render(request, 'common/scan_ticket.html')


@login_required
def api_verify_ticket(request):
    """Verify ticket from QR code"""
    ticket_id = request.GET.get('ticket_id')
    if not ticket_id:
        return JsonResponse({'valid': False, 'error': 'No Ticket ID provided'})
    
    try:
        if 'TKT' not in ticket_id:
             return JsonResponse({'valid': False, 'error': 'Invalid Ticket ID format'})

        ticket = Ticket.objects.get(ticket_id=ticket_id)
        booking = ticket.booking
        show = booking.show
        
        # Authorization check
        is_authorized = False
        
        print(f"DEBUG: Verify Ticket {ticket_id}")
        print(f"DEBUG: Show Type: {show.show_type}")
        print(f"DEBUG: User: {request.user}")
        
        # Check if Theatre Owner owns this movie show
        if show.show_type == 'movie':
            if hasattr(request.user, 'theatre_profile'):
                print(f"DEBUG: T-Owner: {show.movie.theatre_owner.id} vs {request.user.theatre_profile.id}")
                if request.user.theatre_profile.id == show.movie.theatre_owner.id:
                    is_authorized = True
        
        # Check if Organizer owns this event show
        elif show.show_type == 'event':
            if hasattr(request.user, 'organizer_profile'):
                 print(f"DEBUG: Organizer: {show.event.organizer.id} vs {request.user.organizer_profile.id}")
                 if request.user.organizer_profile.id == show.event.organizer.id:
                    is_authorized = True
                
        if not is_authorized:
            print("DEBUG: Authorization Failed")
            return JsonResponse({'valid': False, 'error': f'You are not authorized to verify this ticket. (User: {request.user.username})'})
            
        data = {
            'valid': True,
            'ticket_id': ticket.ticket_id,
            'booking_id': booking.booking_id,
            'user': booking.user.username,
            'seat': str(ticket.seat),
            'show': str(show),
            'is_used': ticket.is_used,
            'used_at': ticket.used_at.strftime('%Y-%m-%d %H:%M') if ticket.used_at else None
        }
        return JsonResponse(data)
        
    except Ticket.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Ticket not found.'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)})
