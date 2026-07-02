from src.clients import SalesforceClient


class ExtractionService:

    def __init__(self):

        self.client = SalesforceClient()

    def extract(self, payload: dict) -> dict:

        return self.client.post(payload)