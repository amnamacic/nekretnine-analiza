import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

def get_coordinates(address):
    geolocator = Nominatim(user_agent="nekretnine-app")
    try:
        location = geolocator.geocode(address)
        return location.latitude, location.longitude
    except:
        return None, None

def scrape_olx(city, size, type):
    url = f"https://www.olx.ba/pretraga?vrsta={type}&lokacija={city}&min_povrsina={size-10}&max_povrsina={size+10}"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select(".pretraga-artikal")
    data = []

    for item in items:
        try:
            link = "https://olx.ba" + item.select_one("a")["href"]
            title = item.select_one(".naslov").text.strip()
            price = item.select_one(".cijena").text.strip()
            date = item.select_one(".datum-objave").text.strip()

            data.append({
                "link": link,
                "title": title,
                "price": price,
                "date": date
            })
        except:
            continue

    return pd.DataFrame(data)

def main():
    import sys
    body = json.loads(sys.argv[1])

    city = body["city"]
    address = body["address"]
    size = int(body["size"])
    type = body["type"]

    lat1, lon1 = get_coordinates(address)
    df = scrape_olx(city, size, type)

    distances = []
    for _, row in df.iterrows():
        lat2, lon2 = get_coordinates(city)
        if lat2 and lon2:
            dist = geodesic((lat1, lon1), (lat2, lon2)).km
        else:
            dist = None
        distances.append(dist)

    df["distance_km"] = distances
    df["price_num"] = (
        df["price"].str.replace(".", "").str.extract("(\d+)", expand=False).astype(float)
    )
    df["price_m2"] = df["price_num"] / size

    df.to_excel("output.xlsx", index=False)

if __name__ == "__main__":
    main()
