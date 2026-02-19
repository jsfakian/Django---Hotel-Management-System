import requests
import csv
from bs4 import BeautifulSoup

# Συλλογή δεδομένων μέσω API (π.χ. πλατφόρμας κρατήσεων)
def fetch_data_from_api(api_url, headers=None):
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# Παράδειγμα: API δεδομένων τιμών ξενοδοχείων
api_url = "https://api.example.com/hotels/pricing"
headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
api_data = fetch_data_from_api(api_url, headers)

# Αποθήκευση δεδομένων από API σε CSV
if api_data:
    with open("hotel_pricing_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Hotel", "Room Type", "Price", "Date", "Occupancy"])
        for item in api_data["results"]:
            writer.writerow([item["hotel_name"], item["room_type"], item["price"], item["date"], item["occupancy"]])

# Web Scraping δεδομένων από ιστοσελίδα ξενοδοχείων
def scrape_hotel_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        data = []
        for hotel in soup.find_all("div", class_="hotel-info"):
            name = hotel.find("h2", class_="hotel-name").text.strip()
            price = hotel.find("span", class_="price").text.strip()
            rating = hotel.find("span", class_="rating").text.strip()
            data.append([name, price, rating])
        return data
    else:
        print(f"Error: {response.status_code}")
        return []

# Παράδειγμα: Web scraping από πλατφόρμα
url = "https://www.example-hotel-platform.com"
hotel_data = scrape_hotel_data(url)

# Αποθήκευση δεδομένων από scraping σε CSV
if hotel_data:
    with open("scraped_hotel_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Hotel Name", "Price", "Rating"])
        writer.writerows(hotel_data)

