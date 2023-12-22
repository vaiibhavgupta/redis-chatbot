import requests

def fetch():
    for _ in range(10):
        response = requests.get("http://numbersapi.com/random/trivia")
        if response.status_code == 200:
            return response.text
    
    return "Error fetching an interesting fact. Please try again later."