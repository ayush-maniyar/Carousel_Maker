import requests

url = "http://127.0.0.1:8000/generate-carousel"
payload = {
    "video_url": "https://youtu.be/2frLKsSsiRk?si=VMmfrlJxxj_Njquk",
    "persona": "Comedian",
    "slide_count": 2,
    "colour_scheme": "blue and red on white backround",
    "vibe": "ancient"
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response Body:", response.json())
