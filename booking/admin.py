from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, OrganizerProfile, TheatreOwnerProfile,
    City, Category, Genre, Language,
    Venue, Theatre, Screen,
    Event, Movie, Show, Seat, SeatBooking,
    Booking, Ticket
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'city', 'email_verified', 'is_active']
    list_filter = ['role', 'email_verified', 'is_active', 'city']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'city', 'phone', 'email_verified', 'verification_token')}),
    )


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'contact_person', 'city', 'status', 'created_at']
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['organization_name', 'contact_person', 'contact_email']
    readonly_fields = ['created_at', 'approved_at']
    
    actions = ['approve_organizers', 'reject_organizers']
    
    def approve_organizers(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} organizer(s) approved successfully.")
    approve_organizers.short_description = "Approve selected organizers"
    
    def reject_organizers(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} organizer(s) rejected.")
    reject_organizers.short_description = "Reject selected organizers"


@admin.register(TheatreOwnerProfile)
class TheatreOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ['theatre_chain_name', 'owner_name', 'city', 'status', 'created_at']
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['theatre_chain_name', 'owner_name', 'contact_email']
    readonly_fields = ['created_at', 'approved_at']
    
    actions = ['approve_theatre_owners', 'reject_theatre_owners']
    
    def approve_theatre_owners(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} theatre owner(s) approved successfully.")
    approve_theatre_owners.short_description = "Approve selected theatre owners"
    
    def reject_theatre_owners(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} theatre owner(s) rejected.")
    reject_theatre_owners.short_description = "Reject selected theatre owners"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'is_active']
    list_filter = ['state', 'is_active']
    search_fields = ['name', 'state']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'organizer', 'capacity', 'is_active']
    list_filter = ['city', 'is_active', 'venue_type']
    search_fields = ['name', 'address']


@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'owner', 'total_screens', 'is_active']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'address']


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['theatre', 'name', 'total_seats', 'screen_type', 'is_active']
    list_filter = ['theatre', 'screen_type', 'is_active']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'organizer', 'status', 'is_trending', 'created_at']
    list_filter = ['status', 'category', 'is_trending', 'language']
    search_fields = ['title', 'artist_name']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_events', 'reject_events', 'mark_trending']
    
    def approve_events(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} event(s) approved.")
    approve_events.short_description = "Approve selected events"
    
    def reject_events(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} event(s) rejected.")
    reject_events.short_description = "Reject selected events"
    
    def mark_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} event(s) marked as trending.")
    mark_trending.short_description = "Mark as trending"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'theatre_owner', 'genre', 'release_date', 'status', 'is_trending', 'rating']
    list_filter = ['status', 'genre', 'language', 'certification', 'is_trending']
    search_fields = ['title', 'director', 'cast']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_movies', 'reject_movies', 'mark_trending']
    
    def approve_movies(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} movie(s) approved.")
    approve_movies.short_description = "Approve selected movies"
    
    def reject_movies(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} movie(s) rejected.")
    reject_movies.short_description = "Reject selected movies"
    
    def mark_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} movie(s) marked as trending.")
    mark_trending.short_description = "Mark as trending"


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'show_type', 'show_date', 'show_time', 'is_active']
    list_filter = ['show_type', 'show_date', 'is_active']
    search_fields = ['event__title', 'movie__title']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['show', 'row', 'seat_number', 'seat_type', 'price']
    list_filter = ['seat_type', 'show']


@admin.register(SeatBooking)
class SeatBookingAdmin(admin.ModelAdmin):
    list_display = ['seat', 'show', 'user', 'status', 'locked_at', 'booked_at']
    list_filter = ['status', 'show']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'show', 'total_amount', 'payment_status', 'booking_date']
    list_filter = ['payment_status', 'payment_method', 'booking_date']
    search_fields = ['booking_id', 'user__username']
    readonly_fields = ['booking_id', 'booking_date']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'booking', 'seat', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['ticket_id', 'booking__booking_id']
    readonly_fields = ['ticket_id', 'created_at']
