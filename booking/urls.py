from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Public pages (Guest access)
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('search/', views.search, name='search'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.customer_register, name='customer_register'),
    path('register/organizer/', views.organizer_register, name='organizer_register'),
    path('register/theatre/', views.theatre_register, name='theatre_register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Customer pages
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('show/<int:show_id>/seats/', views.seat_selection, name='seat_selection'),
    path('booking/payment/<int:show_id>/', views.payment, name='payment'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('booking-history/', views.booking_history, name='booking_history'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # Event Organizer pages
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('organizer/events/', views.manage_events, name='manage_events'),
    path('organizer/event/create/', views.create_event, name='create_event'),
    path('organizer/event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('organizer/event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('organizer/venues/', views.manage_venues, name='manage_venues'),
    path('organizer/venue/create/', views.create_venue, name='create_venue'),
    path('organizer/venue/<int:venue_id>/edit/', views.edit_venue, name='edit_venue'),
    path('organizer/venue/<int:venue_id>/delete/', views.delete_venue, name='delete_venue'),
    path('organizer/event/<int:event_id>/schedule/', views.schedule_event_show, name='schedule_event_show'),
    path('organizer/show/<int:show_id>/seats/', views.configure_event_seats, name='configure_event_seats'),
    path('organizer/analytics/', views.organizer_analytics, name='organizer_analytics'),
    
    # Theatre Owner pages
    path('theatre/dashboard/', views.theatre_dashboard, name='theatre_dashboard'),
    path('theatre/movies/', views.manage_movies, name='manage_movies'),
    path('theatre/movie/create/', views.create_movie, name='create_movie'),
    path('theatre/movie/<int:movie_id>/edit/', views.edit_movie, name='edit_movie'),
    path('theatre/movie/<int:movie_id>/delete/', views.delete_movie, name='delete_movie'),
    path('theatre/theatres/', views.manage_theatres, name='manage_theatres'),
    path('theatre/theatre/create/', views.create_theatre, name='create_theatre'),
    path('theatre/theatre/<int:theatre_id>/edit/', views.edit_theatre, name='edit_theatre'),
    path('theatre/theatre/<int:theatre_id>/screens/', views.manage_screens, name='manage_screens'),
    path('theatre/screen/create/<int:theatre_id>/', views.create_screen, name='create_screen'),
    path('theatre/screen/<int:screen_id>/edit/', views.edit_screen, name='edit_screen'),
    path('theatre/movie/<int:movie_id>/schedule/', views.schedule_movie_show, name='schedule_movie_show'),
    path('theatre/show/<int:show_id>/seats/', views.configure_movie_seats, name='configure_movie_seats'),
    path('theatre/analytics/', views.theatre_analytics, name='theatre_analytics'),
    
    # Admin pages
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/organizers/', views.admin_organizers, name='admin_organizers'),
    path('admin-panel/organizer/<int:profile_id>/approve/', views.approve_organizer, name='approve_organizer'),
    path('admin-panel/organizer/<int:profile_id>/reject/', views.reject_organizer, name='reject_organizer'),
    path('admin-panel/theatre-owners/', views.admin_theatre_owners, name='admin_theatre_owners'),
    path('admin-panel/theatre-owner/<int:profile_id>/approve/', views.approve_theatre_owner, name='approve_theatre_owner'),
    path('admin-panel/theatre-owner/<int:profile_id>/reject/', views.reject_theatre_owner, name='reject_theatre_owner'),
    path('admin-panel/events/', views.admin_events, name='admin_events'),
    path('admin-panel/event/<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('admin-panel/event/<int:event_id>/reject/', views.reject_event, name='reject_event'),
    path('admin-panel/movies/', views.admin_movies, name='admin_movies'),
    path('admin-panel/movie/<int:movie_id>/approve/', views.approve_movie, name='approve_movie'),
    path('admin-panel/movie/<int:movie_id>/reject/', views.reject_movie, name='reject_movie'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    
    # AJAX endpoints
    path('api/check-seat-availability/<int:show_id>/', views.check_seat_availability, name='check_seat_availability'),
    path('api/lock-seats/<int:show_id>/', views.lock_seats_api, name='lock_seats_api'),
]
