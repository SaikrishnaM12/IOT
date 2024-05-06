import os
import csv
import random
import requests
from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from openmeteo_requests import Client
from retry_requests import retry
import requests_cache
matplotlib.use('Agg')
static_dir = os.path.join(os.getcwd(), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = Client(session = retry_session)
app = Flask(__name__)

@app.route('/')
def index():
    # Read the CSV file
    data = pd.read_csv(r"C:\Users\krish\OneDrive\Desktop\project\AirQualityMonitoringSystem.csv")

    # Convert time column to datetime format
    data['time'] = pd.to_datetime(data['time'])

    # Plotting
    plt.figure(figsize=(10, 6))

    # Time vs Temperature
    plt.subplot(2, 1, 1)
    plt.plot(data['time'], data['temp'], color='blue')
    plt.title('Time vs Temperature')
    plt.xlabel('Time')
    plt.ylabel('Temperature')
    temp_plot_path = os.path.join(static_dir, 'temp_plot.png')
    plt.savefig(temp_plot_path)
    plt.close()

    # Time vs Humidity
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 2)
    plt.plot(data['time'], data['humidity'], color='green')
    plt.title('Time vs Humidity')
    plt.xlabel('Time')
    plt.ylabel('Humidity')
    humidity_plot_path = os.path.join(static_dir, 'humidity_plot.png')
    plt.savefig(humidity_plot_path)
    plt.close()

    return render_template('index.html', temp_plot=temp_plot_path, humidity_plot=humidity_plot_path)

@app.route('/weather')
def weather():
    api_key = "a1e1eb9ec97cc537874c97f711d7c42c"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    city_name = request.args.get('city')
    
    if city_name:
        complete_url = f"{base_url}q={city_name}&appid={api_key}"
    else:
        complete_url = f"{base_url}lat={latitude}&lon={longitude}&appid={api_key}"
    
    response = requests.get(complete_url)
    weather_data = response.json()
    
    if weather_data["cod"] != "404":
        # Get air quality data
        air_quality_info = {}  # Initialize air quality info dictionary
        if city_name:
            params = {"city": city_name}
            air_quality_response = openmeteo.weather_api("https://air-quality-api.open-meteo.com/v1/air-quality", params=params)
            if air_quality_response:  # Check if air quality response exists
                air_quality_data = air_quality_response[0].Hourly().Variables(0).ValuesAsNumpy()
                air_quality_info = {'us_aqi': air_quality_data.tolist()}  # Prepare air quality data
        else:
            params = {"latitude": latitude, "longitude": longitude, "hourly": "us_aqi"}
            air_quality_response = openmeteo.weather_api("https://air-quality-api.open-meteo.com/v1/air-quality", params=params)
            if air_quality_response:  # Check if air quality response exists
                air_quality_data = air_quality_response[0].Hourly().Variables(0).ValuesAsNumpy()
                air_quality_info = {'us_aqi': air_quality_data.tolist()}  # Prepare air quality data

        # Prepare weather data
        weather_info = {
            'temperature': weather_data['main']['temp'],
            'pressure': weather_data['main']['pressure'],
            'humidity': weather_data['main']['humidity'],
            'description': weather_data['weather'][0]['description']
        }

        return jsonify({**weather_info, **air_quality_info})
    else:
        return jsonify({'error': 'Weather data not found'}), 404

def median(lst):
    sorted_lst = sorted(lst)
    lst_len = len(lst)
    index = (lst_len - 1) // 2

    if lst_len % 2:
        return sorted_lst[index]
    else:
        return (sorted_lst[index] + sorted_lst[index + 1]) / 2.0

if __name__ == '__main__':
    app.run(debug=True)
