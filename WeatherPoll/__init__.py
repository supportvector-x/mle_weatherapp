import datetime
from gc import get_referents
import logging
import datetime
import json
import uuid
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from zoneinfo import ZoneInfo

import azure.functions as func
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


def main(mytimer: func.TimerRequest, temperaturesTable: func.Out[str]) -> None:
    """ Function polls api.openweathermap.org every hour and stores the temperature in Turku in local time to a Azure table storage"""

    try:
        kv = SecretClient(vault_url="https://mle-weatherapp-kv.vault.azure.net/", credential=DefaultAzureCredential())
        api_secret = kv.get_secret("weather-api-key")
    except Exception as e:
        logging.error(f"Error while trying to connect to KeyVault\nError msg: {str(e)}")

    def get_temperature(city: str="Turku") -> str:
        """Gets the current weather from openweathermap.org in provided city
        """
        endpoint = "https://api.openweathermap.org/data/2.5/weather"
        payload = {"q": city, "appid": api_secret.value, 'units': 'metric'}

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
            )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        try:
            response = http.get(endpoint, params=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error while calling openweathermap. Error msg: {str(e)}")
        # TODO: Implement retry and failure logic
        return response.json()['main']['temp']

    temperature = get_temperature()
    # TODO: check if respose provides timestamp of time of measurement and use that instead here
    # TODO: Use unix timestamp
    dt_local = datetime.datetime.now(tz=ZoneInfo("Europe/Helsinki")).replace(microsecond=0)
    rowKey = str(uuid.uuid4())
    data = {
        "partitionKey": "Turku",
        "rowKey": rowKey,
        "year": dt_local.year,
        "month": dt_local.month,
        "day": dt_local.day,
        "hour": dt_local.hour,
        "minute": dt_local.minute,
        "second": dt_local.second,
        "Temperature" : temperature
    }
    try:
        temperaturesTable.set(json.dumps(data))
        logging.info(f"Successfully read temperature into table store at {str(dt_local)}")
    except Exception as e:
        logging.error(f"Error reding data into table store: {str(e)}")