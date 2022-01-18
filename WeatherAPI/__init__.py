import logging
import re

import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


def main(req: func.HttpRequest, temperaturesTable) -> func.HttpResponse:
    """Functions takes date (YYYY-MM-DD) and time (HH:MM:SS) as input and returns
    the recorded temperature from Turku at the closest recorded full hour of the input time (UTC)

    ***********
    * EXAMPLE *
    ***********

    import requests
    
    # Replace FUNCTION_ENDPOINT with whatever endpoint the function is assigned to
    response = requests.get(FUNCTION_ENDPOINT, params={"date": "2022-01-17", "time": "10:00:00"})
    print(response.json())

    >> -2.03
    """

    def valid_input_parameters(params: dict) -> bool:
        """Checks that valid parameters are given and that they are of the correct format"""
        
        # Are parameters given and are date and time included
        if not params:
            return False
        elif "date" not in params.keys() or "time" not in params.keys():
            return False
        # If parameters provided, are they of correct form
        re_date = r'\d{4}-\d{2}-\d{2}$'
        re_time = r'\d{2}:\d{2}:\d{2}$'
        if re.match(re_date, params.get('date')) and re.match(re_time, params.get('time')):
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
        hour = int(hour) + 1 if int(minute) > 30 else hour
        qry_string = f"year eq {year} and month eq {month} and day eq {day} and hour eq {hour} and minute eq 0"
        try:
            res = table.query_entities(qry_string)
        except Exception as e:
            logging.error(f"Error retrieving temperature from table\nError Message: {str(e)}")
            res = []

        # During testing the function might be run manually
        # It could mean that it returns two valid rows. Pick the latest
        rows = [row for row in res]
        return rows[0].get("Temperature") if rows else None

    # get keys and connect to table
    try:
        kv = SecretClient(vault_url="https://mle-weatherapp-kv.vault.azure.net/", credential=DefaultAzureCredential())
        storage_secret = kv.get_secret("storage-sas-token")
    except Exception as e:
        logging.error(f"Error while trying to connect to KeyVault\nError msg: {str(e)}")
        func.HttpResponse("Internal Error", status_code=500)
    try:
        table_service = TableServiceClient(endpoint=storage_secret.value)
        table = table_service.get_table_client("Temperatures")
    except Exception as e:
        logging.error(f"Error while trying to connect to table store\nError msg: {str(e)}")
        func.HttpResponse("Internal Error", status_code=500)

    # Check for valid input
    if not valid_input_parameters(req.params):
        return func.HttpResponse("Invalid input parameters, please provide date and time. Date is expected to be 'YYYY-MM-DD' and Time 'HH:MM:SS'", status_code=400)
    
    date = req.params.get('date')
    time = req.params.get('time')
    temperature = get_temperature(date, time)

    if not temperature:
        return func.HttpResponse("No temperature found for date and time", status_code=404)
    return func.HttpResponse(str(temperature), status_code=200)
