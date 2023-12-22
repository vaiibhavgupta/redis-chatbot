import requests

def fetch(location):
    params = {'q': location, 'appid': "9db005612f20ea4a281f16e147f74e09", 'units': 'metric'}
    response = requests.get(url="http://api.openweathermap.org/data/2.5/weather", params=params)
    data = response.json()

    if response.status_code == 200:
        weather = {'Temperature': data['main']['temp'], 'Humidity': data['main']['humidity']}
        return weather
    
    elif response.status_code == 404:
        return {'Response': "Invalid entry detected; please try again."}

    return {'Response': f"An Error occurred. Status Code: {response.status_code} | Message: {data['message']}"}