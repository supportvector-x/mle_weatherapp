import datetime
from gc import get_referents
import logging
import datetime
import json
import uuid
import requests

import azure.functions as func
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


def main(mytimer: func.TimerRequest, temperaturesTable: func.Out[str]) -> None:
    """ Function polls api.openweathermap.org every hour and stores the temperature in Turku in UTC to a Azure table storage"""

    # TODO: Store as environment variables
    kv = SecretClient(vault_url="https://mle-weatherapp-kv.vault.azure.net/", credential=DefaultAzureCredential())
    api_secret = kv.get_secret("weather-api-key")

    def get_temperature(city: str="Turku") -> str:
        """Gets the current weather from openweathermap.org
        """
        endpoint = "https://api.openweathermap.org/data/2.5/weather"
        payload = {"q": city, "appid": api_secret.value, 'units': 'metric'}
        response = requests.get(endpoint, params=payload) # add timeout
        # TODO: Implement retry and failure logic
        return response.json()['main']['temp']


    temperature = get_temperature() # OK
    # TODO: check if respose provides timestamp of time of measurement and use that instead here
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
