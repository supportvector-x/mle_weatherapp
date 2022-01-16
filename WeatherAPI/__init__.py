import logging
import json
import datetime
import requests
import re
import os

import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# TODO: Create function to parse the return table from the binding 
# TODO: Make the function return the temperature that was closest to the requesting timestamp

def main(req: func.HttpRequest, temperaturesTable) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # KV
    kv = SecretClient(vault_url="https://mle-weatherapp-kv.vault.azure.net/", credential=DefaultAzureCredential())
    secret = kv.get_secret("weather-api-key")


    # Get connection to the table
    # TODO: get the token away from here to KeyVault
    sas_token = r"https://turkuweather.table.core.windows.net/?sv=2020-08-04&ss=bfqt&srt=so&sp=rwdlacupix&se=2022-03-31T13:49:45Z&st=2022-01-15T06:49:45Z&spr=https&sig=NPe8n8ENrYx8W5WxZZnvOt3XL3ycCvDkbn5KKii%2B2wQ%3D"
    table_service = TableServiceClient(endpoint=sas_token)
    table = table_service.get_table_client("Temperatures")

    def valid_input_parameters(date: str, time: str) -> bool:
        """Light regex to check if input parameters are correctly formatted"""
        # TODO: Handle day, month order
        re_date = r'\d{4}-\d{2}-\d{2}$'
        re_time = r'\d{2}:\d{2}:\d{2}$'
        if re.match(re_date, date) and re.match(re_time, time):
            return True
        else:
            return False

    def get_temperature(date: str, time: str):
        """Given date and time, retrieves the temperature of the closest full hour in Turku"""
        year, month, day = date.split("-")
        hour, minute, second = time.split(":")

        # Since we are only storing the temperature once per hour
        # choose the closest hour based on user input on timestmap
        # e.g. if input time is 15:31:00, return temperature at 16:00:00, if input minute < 30 return temperature at the started hour -> this case 15:00:00
        # TODO: Handle case where the hour shift pushes it into a future hour
        # TODO: rebuild this entire module

        hour = int(hour) + 1 if int(minute) > 30 else hour
        qry_string = f"year eq {year} and month eq {month} and day eq {day} and hour eq {hour} and minute eq 0"
        res = table.query_entities(qry_string)

        # This should already return only one row, but since during testing the function might be run manually
        # It could mean that it returns two valid rows. Pick the latest
        rows = [row for row in res]
        return rows[0].get("Temperature") if rows else None

    # Check if input parameters were given
    if 'date' not in req.params.keys() or 'time' not in req.params.keys():
        return func.HttpResponse("Please provide date and time", status_code=400)

    date = req.params.get('date')
    time = req.params.get('time')

    if not valid_input_parameters(date, time):
        return func.HttpResponse("Invalid parameter format. Date is expected to be 'YYYY-MM-DD' and Time 'HH:MM:SS'", status_code=400)

    temperature = get_temperature(date, time)
    if not temperature:
        return func.HttpResponse("No temperature found for date and time", status_code=404)

    #return func.HttpResponse(\
    #    f"Date: {date}\nTime: {time}\nTemperature: NA\n\nCURRENT TABLE DATA\n{[row for row in table]}"
    #    )
    return func.HttpResponse(str(temperature) + str(secret.value))
