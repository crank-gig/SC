import requests

def get_geolocation_data(ip_address):
    # Replace 'YOUR_API_KEY' with the actual API key from your chosen geolocation service
    api_key = 'YOUR_API_KEY'
    api_url = f'https://api.example.com/geolocation?ip={ip_address}&apikey={api_key}'

    try:
        response = requests.get(api_url)
        data = response.json()

        # Extract relevant geolocation information
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        city = data.get('city')
        country = data.get('country_name')

        return {'latitude': latitude, 'longitude': longitude, 'city': city, 'country': country}
    except Exception as e:
        print(f"Error fetching geolocation data: {e}")
        return None
