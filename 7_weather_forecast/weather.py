"""Task 7: Weather Forecast app (Tkinter). Real-time data from Open-Meteo (no API key needed).
Location is auto-detected from your IP address; you can also search any city.
Install: pip install requests"""
import threading, tkinter as tk
from tkinter import ttk, messagebox
import requests

CODES = {0: "Clear sky ☀", 1: "Mainly clear 🌤", 2: "Partly cloudy ⛅", 3: "Overcast ☁", 45: "Fog 🌫", 48: "Rime fog 🌫",
         51: "Light drizzle 🌦", 53: "Drizzle 🌦", 55: "Heavy drizzle 🌧", 61: "Light rain 🌧", 63: "Rain 🌧", 65: "Heavy rain 🌧",
         71: "Light snow ❄", 73: "Snow ❄", 75: "Heavy snow ❄", 80: "Rain showers 🌦", 81: "Rain showers 🌧", 82: "Violent showers ⛈",
         95: "Thunderstorm ⛈", 96: "Thunderstorm + hail ⛈", 99: "Thunderstorm + hail ⛈"}

def detect_location():
    r = requests.get("http://ip-api.com/json/", timeout=8).json()
    if r.get("status") != "success": raise RuntimeError("Could not detect location")
    return r["lat"], r["lon"], f"{r['city']}, {r['country']}"

def geocode(city):
    r = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=8).json()
    if not r.get("results"): raise RuntimeError(f"City '{city}' not found")
    x = r["results"][0]
    return x["latitude"], x["longitude"], f"{x['name']}, {x.get('country', '')}"

def fetch_weather(lat, lon):
    return requests.get("https://api.open-meteo.com/v1/forecast", timeout=8, params={
        "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 5,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"}).json()

class WeatherApp:
    def __init__(self, root):
        self.root = root; root.title("Weather Forecast"); root.geometry("430x520")
        top = ttk.Frame(root, padding=8); top.pack(fill="x")
        self.city = ttk.Entry(top); self.city.pack(side="left", expand=True, fill="x")
        self.city.bind("<Return>", lambda e: self.search())
        ttk.Button(top, text="Search", command=self.search).pack(side="left", padx=4)
        ttk.Button(top, text="📍 My location", command=self.locate).pack(side="left")
        self.place = ttk.Label(root, font=("Arial", 16, "bold")); self.place.pack(pady=(10, 0))
        self.temp = ttk.Label(root, font=("Arial", 44, "bold")); self.temp.pack()
        self.desc = ttk.Label(root, font=("Arial", 14)); self.desc.pack()
        self.details = ttk.Label(root, font=("Arial", 11)); self.details.pack(pady=6)
        self.forecast = ttk.Frame(root, padding=10); self.forecast.pack(fill="both", expand=True)
        self.status = ttk.Label(root, text="", foreground="gray"); self.status.pack(pady=4)
        self.locate()

    def run(self, getter):
        self.status.config(text="Loading…")
        def work():
            try:
                lat, lon, name = getter()
                data = fetch_weather(lat, lon)
                self.root.after(0, lambda: self.show(name, data))
            except Exception as e:
                self.root.after(0, lambda: (self.status.config(text=""), messagebox.showerror("Error", str(e))))
        threading.Thread(target=work, daemon=True).start()

    def locate(self): self.run(detect_location)
    def search(self):
        c = self.city.get().strip()
        if c: self.run(lambda: geocode(c))

    def show(self, name, d):
        cur = d["current"]
        self.place.config(text=name)
        self.temp.config(text=f"{cur['temperature_2m']:.0f}°C")
        self.desc.config(text=CODES.get(cur["weather_code"], "Unknown"))
        self.details.config(text=f"Feels like {cur['apparent_temperature']:.0f}°C   |   Humidity {cur['relative_humidity_2m']}%   |   Wind {cur['wind_speed_10m']} km/h")
        for w in self.forecast.winfo_children(): w.destroy()
        day = d["daily"]
        for i, date in enumerate(day["time"]):
            ttk.Label(self.forecast, text=date[5:], width=7).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Label(self.forecast, text=CODES.get(day["weather_code"][i], "?"), width=22).grid(row=i, column=1, sticky="w")
            ttk.Label(self.forecast, text=f"{day['temperature_2m_min'][i]:.0f}° / {day['temperature_2m_max'][i]:.0f}°").grid(row=i, column=2)
            ttk.Label(self.forecast, text=f"💧{day['precipitation_sum'][i]}mm").grid(row=i, column=3, padx=6)
        self.status.config(text="Updated just now")

if __name__ == "__main__":
    root = tk.Tk(); WeatherApp(root); root.mainloop()
