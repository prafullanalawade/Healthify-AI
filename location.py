import requests
import folium
from geopy.geocoders import Nominatim

def get_nearby_locations(current_location, radius=1000):
    """
    Get nearby clinics, doctors, and hospitals based on the user's current location.
    Args:
        current_location (str): The user's current location (address or coordinates).
        radius (int): Radius in meters for searching nearby places.

    Returns:
        map_object: A Folium Map object with nearby locations marked.
        places_list_or_error: A list of nearby places or an error message.
    """
    # Step 1: Get the coordinates of the current location using Nominatim
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': current_location,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'YourAppName/1.0 (your_email@example.com)'  # Replace with your app name and email
    }
    
    try:
        response = requests.get(nominatim_url, params=params, headers=headers)
        if response.status_code != 200 or not response.json():
            return "Error: Unable to fetch location coordinates. Check your input or try again later.", None

        location_data = response.json()[0]
        lat, lon = float(location_data['lat']), float(location_data['lon'])
    except Exception as e:
        return f"Error: Unable to connect to Nominatim API ({e}).", None

    # Step 2: Search for nearby clinics, doctors, and hospitals using Overpass API
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
        node["amenity"="clinic"](around:{radius},{lat},{lon});
        node["amenity"="hospital"](around:{radius},{lat},{lon});
        node["healthcare"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        response = requests.get(overpass_url, params={'data': query})
        if response.status_code != 200:
            return "Error: Unable to fetch nearby locations. Overpass API might be down.", None

        data = response.json()
    except Exception as e:
        return f"Error: Unable to connect to Overpass API ({e}).", None

    # Step 3: Extract places and create a map
    places = []
    map_object = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color="blue")).add_to(map_object)

    for element in data['elements']:
        name = element.get('tags', {}).get('name', 'Unknown')
        address = element.get('tags', {}).get('addr:full', 'Address not available')
        contact = (
            element.get('tags', {}).get('contact:phone') or
            element.get('tags', {}).get('phone') or
            element.get('tags', {}).get('contact:mobile') or
            element.get('tags', {}).get('contact:email') or
            "Contact not available"
        )

        lat, lon = element['lat'], element['lon']

        # Fetch additional details using Practo API
        practo_api_key = "your_practo_api_key"  # Replace with your Practo API key
        practo_url = "https://www.practo.com/api/v1/doctors"
        practo_params = {
            "location": current_location,
            "radius": radius,
            "api_key": practo_api_key
        }
        
        try:
            practo_response = requests.get(practo_url, params=practo_params)
            if practo_response.status_code == 200:
                practo_data = practo_response.json()
                if practo_data and 'doctors' in practo_data:
                    doctor_info = practo_data['doctors'][0]  # Taking the first available doctor
                    contact = doctor_info.get('phone', contact)
                    appointment_link = doctor_info.get('booking_url', '#')
                else:
                    appointment_link = '#'
            else:
                appointment_link = '#'
        except Exception as e:
            appointment_link = '#'

        places.append({
            'name': name,
            'address': address,
            'contact': contact,
            'appointment_link': appointment_link
        })
        # Add marker to the map
        folium.Marker(
            [lat, lon],
            tooltip=name,
            popup=f"Name: {name}<br>Address: {address}<br>Contact: {contact}<br><a href='{appointment_link}' target='_blank'>Book Appointment</a>",
            icon=folium.Icon(color="red")
        ).add_to(map_object)

    return map_object, places
