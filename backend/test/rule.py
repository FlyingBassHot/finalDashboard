import httpx

respons = httpx.get("http://open-meteo.com/")
print(respons.status_code)