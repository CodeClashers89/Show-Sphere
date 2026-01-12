import os
import django
import sys

# Add the project root to python path if needed, though usually strict relative path execution works
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'showsphere.settings')
django.setup()

from booking.models import Country, State, City

import csv

def seed():
    # 1. Country
    india, _ = Country.objects.get_or_create(name='India')
    print(f"Country: {india}")

    # 2. States and Cities from CSV
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'india_states_major_cities.csv')
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return

    print("Reading from CSV...")
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            state_name = row['state'].strip()
            city_name = row['city'].strip()
            
            if not state_name or not city_name:
                continue

            # Create/Get State
            state, created = State.objects.get_or_create(name=state_name, country=india)
            if created:
                print(f"Created State: {state.name}")
            
            # Create/Get City
            city, created = City.objects.get_or_create(name=city_name, state=state)
            if created:
                print(f"  - Created City: {city.name} in {state.name}")
            else:
                # Ensure correct state link if logic requires, typically seeded data is static
                if city.state != state:
                    city.state = state
                    city.save()
                    print(f"  - Updated City: {city.name} -> {state.name}")

if __name__ == '__main__':
    seed()
