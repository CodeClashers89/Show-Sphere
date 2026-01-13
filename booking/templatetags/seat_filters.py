from django import template

register = template.Library()

@register.filter
def get_seat_status(seat_status_dict, seat_key):
    """Get seat status from dictionary using row-seatnum key"""
    return seat_status_dict.get(str(seat_key), 'available')

@register.filter
def make_seat_key(row, seat_num):
    """Create seat key from row and seat number"""
    return f"{row}-{seat_num}"
