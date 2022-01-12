import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    date = req.params.get('date')
    if not date:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            date = req_body.get('date')

    if date:
        return func.HttpResponse(f"Temperature on {date} was 10 centigrade")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a date in the query string or in the request body for a temperature",
             status_code=200
        )
