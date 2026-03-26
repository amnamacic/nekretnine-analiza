import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.distance import geodesic
import openpyxl
import json
import sys

def get_coordinates(address):
    api_key = "YOUR_API_KEY"  
    url = f"http://dev.virtualearth.net/REST/v1/Locations?query={address}&key={api_key}"
    r = requests.get(url).json()

    try:
        coords = r["resourceSets"][0]["resources"][0]["point"]["coordinates"]
        return coords[0], coords[1]
    except:
        return None, None


def scrape_olx(city, type, size):
    url = (
        f"https://www.olx.ba/pretraga?lokacija={city}"
        f"&vrsta={type}&min_povrsina={size-10}&max_povrsina={size+10}"
    )

    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select(".pretraga-artikal")
    results = []

    for i in items:
        try:
            link = "https://olx.ba" + i.select_one("a")["href"]
            title = i.select_one(".naslov").text.strip()
            price = i.select_one(".cijena").text.strip()
            date = i.select_one(".datum-objave").text.strip()
            m2 = i.select_one(".detalji").text.strip()

            results.append({
                "title": title,
                "link": link,
                "price": price,
                "date": date,
                "m2": m2
            })
        except:
            continue

    return pd.DataFrame(results)


def main():
    data = json.loads(sys.argv[1])

    city = data["city"]
    address = data["address"]
    size = int(data["size"])
    type = data["type"]

    lat1, lon1 = get_coordinates(address)

    df = scrape_olx(city, type, size)

    distances = []
    for _, row in df.iterrows():
        lat2, lon2 = get_coordinates(city)

        if lat2 and lon2:
            dist = geodesic((lat1, lon1), (lat2, lon2)).km
        else:
            dist = None

        distances.append(dist)

    df["distance_km"] = distances

    df["price_num"] = df["price"].str.replace(".", "", regex=False).str.extract("(\d+)").astype(float)
    df["price_m2"] = df["price_num"] / size

    output = "output.xlsx"
    df.to_excel(output, index=False)
    print(f"Created {output}")


if __name__ == "__main__":
    main()
