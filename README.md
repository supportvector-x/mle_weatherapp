# Weather App
Weather app consists of two functions.
A poll function that fetches the temperature in centigrade in Turku every hour and stores the temperature in an Azure table store
A WeatherAPI function exposes an endpoint to access this data by providing date (YYYY-MM-DD) and time (HH:MM:SS) as input parameters. Returns the temperature of the closest full hour of the input time.

# Function URL
https://turku-weather.azurewebsites.net/api/weatherapi/
