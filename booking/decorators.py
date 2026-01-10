from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def customer_required(view_func):
    """Decorator to restrict access to customers only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'customer':
            messages.error(request, 'Access denied. This page is for customers only.')
            return redirect('booking:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def organizer_required(view_func):
    """Decorator to restrict access to event organizers only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'organizer':
            messages.error(request, 'Access denied. This page is for event organizers only.')
            return redirect('booking:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def approved_organizer_required(view_func):
    """Decorator to restrict access to approved event organizers only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'organizer':
            messages.error(request, 'Access denied. This page is for event organizers only.')
            return redirect('booking:home')
        
        try:
            profile = request.user.organizer_profile
            if profile.status != 'approved':
                messages.warning(request, f'Your account is {profile.get_status_display()}. Please wait for admin approval.')
                return redirect('booking:organizer_dashboard')
        except:
            messages.error(request, 'Organizer profile not found.')
            return redirect('booking:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def theatre_owner_required(view_func):
    """Decorator to restrict access to theatre owners only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'theatre_owner':
            messages.error(request, 'Access denied. This page is for theatre owners only.')
            return redirect('booking:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def approved_theatre_owner_required(view_func):
    """Decorator to restrict access to approved theatre owners only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'theatre_owner':
            messages.error(request, 'Access denied. This page is for theatre owners only.')
            return redirect('booking:home')
        
        try:
            profile = request.user.theatre_profile
            if profile.status != 'approved':
                messages.warning(request, f'Your account is {profile.get_status_display()}. Please wait for admin approval.')
                return redirect('booking:theatre_dashboard')
        except:
            messages.error(request, 'Theatre owner profile not found.')
            return redirect('booking:home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator to restrict access to admins only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('booking:login')
        if request.user.role != 'admin' and not request.user.is_superuser:
            messages.error(request, 'Access denied. This page is for administrators only.')
            return redirect('booking:home')
        return view_func(request, *args, **kwargs)
    return wrapper
