import datetime
import logging
import datetime
import pytz
import json
import random
import uuid
import requests
import azure.functions as func


def main(mytimer: func.TimerRequest, temperaturesTable: func.Out[str]) -> None:

    k = '0836cb2fa32074b665161661e476fb53'
    endpoint = "https://api.openweathermap.org/data/2.5/weather"
    payload = {"q" : "Turku", "appid" : k}

    data =
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    temp = random.randrange(0, 100)
    rowKey = str(uuid.uuid4())

    data = {
        "partitionKey": "Turku",
        "rowKey": rowKey,
        "timestamp_utc": str(utc_now),
        "Temperature" : temp
    }

    logging.info(f"DATA: {data}")

    temperaturesTable.set(json.dumps(data))

    if mytimer.past_due:
        logging.info('Data Read')
