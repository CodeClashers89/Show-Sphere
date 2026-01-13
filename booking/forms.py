from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    CustomUser, OrganizerProfile, TheatreOwnerProfile,
    Event, Movie, Venue, Theatre, Screen, Show, Seat, City, Country, State
)


class CustomerRegistrationForm(UserCreationForm):
    """Customer registration form"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Phone Number'
    }))
    city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'city']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        if commit:
            user.save()
        return user


class OrganizerRegistrationForm(forms.ModelForm):
    """Event Organizer registration form"""
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Country"
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = OrganizerProfile
        fields = ['organization_name', 'contact_person', 'contact_email', 'contact_phone', 'country', 'state', 'city', 'address']
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person Name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact Email'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].initial = Country.objects.filter(name='India').first()
        
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            pass
            
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data


class TheatreOwnerRegistrationForm(forms.ModelForm):
    """Theatre Owner registration form"""
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Country"
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = TheatreOwnerProfile
        fields = ['theatre_chain_name', 'owner_name', 'contact_email', 'contact_phone', 'country', 'state', 'city', 'address']
        widgets = {
            'theatre_chain_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Theatre Chain Name'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner Name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact Email'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Head Office Address'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].initial = Country.objects.filter(name='India').first()
        
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            # If editing an existing instance (not relevant for registration but good practice)
            pass
            
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data


class LoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class PasswordResetRequestForm(forms.Form):
    """Password reset request form"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email address'
    }))


class PasswordResetConfirmForm(forms.Form):
    """Password reset confirmation form"""
    password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }))
    password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }))
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data


class EventForm(forms.ModelForm):
    """Event creation/edit form"""
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'genre', 'language', 'duration', 
                  'artist_name', 'poster', 'trailer_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Event Description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in minutes'}),
            'artist_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main Artist/Performer'}),
            'poster': forms.FileInput(attrs={'class': 'form-control'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube URL'}),
        }


class MovieForm(forms.ModelForm):
    """Movie creation/edit form"""
    class Meta:
        model = Movie
        fields = ['title', 'description', 'genre', 'language', 'duration', 'release_date',
                  'director', 'cast', 'certification', 'poster', 'trailer_url', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Movie Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Movie Description'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in minutes'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'director': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Director Name'}),
            'cast': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Main Cast (comma separated)'}),
            'certification': forms.Select(attrs={'class': 'form-control'}),
            'poster': forms.FileInput(attrs={'class': 'form-control'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube URL'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '10'}),
        }


class VenueForm(forms.ModelForm):
    """Venue creation/edit form"""
    class Meta:
        model = Venue
        fields = ['name', 'city', 'address', 'capacity', 'venue_type', 'facilities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue Name'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Capacity'}),
            'venue_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Stadium, Arena, Hall'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Parking, Food Court, etc.'}),
        }


class TheatreForm(forms.ModelForm):
    """Theatre creation/edit form"""
    class Meta:
        model = Theatre
        fields = ['name', 'city', 'address', 'total_screens', 'facilities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Theatre Name with Location'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'total_screens': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Screens'}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Parking, 3D, IMAX, etc.'}),
        }


class ScreenForm(forms.ModelForm):
    """Screen creation/edit form"""
    class Meta:
        model = Screen
        fields = ['name', 'total_seats', 'screen_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Screen Name (e.g., Screen 1)'}),
            'total_seats': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Seats'}),
            'screen_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2D, 3D, IMAX, 4DX, etc.'}),
        }


class ShowForm(forms.ModelForm):
    """Show scheduling form"""
    class Meta:
        model = Show
        fields = ['show_date', 'show_time', 'end_time', 'base_price']
        widgets = {
            'show_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'show_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Base Price', 'step': '0.01'}),
        }


class SeatForm(forms.ModelForm):
    """Seat configuration form"""
    class Meta:
        model = Seat
        fields = ['row', 'seat_number', 'seat_type', 'price']
        widgets = {
            'row': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Row (e.g., A, B, C)'}),
            'seat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seat Number'}),
            'seat_type': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price', 'step': '0.01'}),
        }


class OTPVerifyForm(forms.Form):
    """OTP Verification Form"""
    otp_code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control text-center', 
        'placeholder': 'Enter 6-digit Code',
        'style': 'letter-spacing: 0.5em; font-size: 1.5rem; max-width: 300px; margin: 0 auto;'
    }))


class SetNewPasswordForm(forms.Form):
    """Set New Password Form"""
    password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }))
    password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }))
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

