import logging
import json
import datetime
import pytz
import requests

import azure.functions as func


def main(req: func.HttpRequest, temperaturesTable) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    def get_weather():
        k = 'd4b91f7e23e8701dcecd6999af856de4'
        endpoint = "https://api.openweathermap.org/data/2.5/weather"
        payload = {"q" : "Turku", "appid" : k}

        data = requests.get(endpoint, params=payload)
        return data

    weather_data = get_weather()
    date = req.params.get('date')
    table = json.loads(temperaturesTable)
    return func.HttpResponse(f"Date: {date}\nWeatherdata: {weather_data}\nTABLE_STORE: {table}")


    #data = json.loads(tempJSON)
    #if not date:
    #    try:
    #        req_body = req.get_json()
    #    except ValueError:
    #        pass
    #    else:
    #        date = req_body.get('date')

    #if date:
    #    return func.HttpResponse(f"Temperature on {date} was 10 centigrade,\n{data}")
    #else:
    #    return func.HttpResponse(
    #         "This HTTP triggered function executed successfully. Pass a date in the query string or in the request body for a temperature",
    #         status_code=200
    #    )
