import datetime
from gc import get_referents
import logging
import datetime
import pytz
import json
import random
import uuid
import requests
import azure.functions as func


def main(mytimer: func.TimerRequest, temperaturesTable: func.Out[str]) -> None:
    """ Function polls api.openweathermap.org every hour and stores the temperature in Turku in UTC to a Azure table storage"""

    def get_temperature(city: str="Turku") -> str:
        """Gets the current weather from openweathermap.org
        """
        k = '0836cb2fa32074b665161661e476fb53'
        endpoint = "https://api.openweathermap.org/data/2.5/weather"
        payload = {"q": city, "appid": k, 'units': 'metric'}
        response = requests.get(endpoint, params=payload)
        # TODO: Implement retry and failure logic
        return response.json()['main']['temp']


    temperature = get_temperature() # OK
    dt_utc = datetime.datetime.now().replace(microsecond=0) # object
    str_timestamp = dt_utc.isoformat(timespec='seconds') # as string
    rowKey = str(uuid.uuid4())

    data = {
        "partitionKey": "Turku",
        "rowKey": rowKey,
        "year": dt_utc.year,
        "month": dt_utc.month,
        "day": dt_utc.day,
        "hour": dt_utc.hour,
        "minute": dt_utc.minute,
        "second": dt_utc.second,
        "Temperature" : temperature
    }

    logging.info(f"DATA: {data}")

    temperaturesTable.set(json.dumps(data))

    if mytimer.past_due:
        logging.info('Data Read')
