from src.clients import HtmlClient
from src.transformations import HtmlParserService

class TransformationService:

    def __init__(self):

        self.html_client = HtmlClient()
        self.html_parser = HtmlParserService()

    def transform(self, raw_data):

        partners = self._parse_response(raw_data)

        transformed = []

        for partner in partners:

            api_data = self._flatten_partner(partner)

            html = self.html_client.get(
                api_data["listingUrl"]
            )

            html_data = self.html_parser.parse(html)

            api_data.update(html_data)

            transformed.append(api_data)

        return transformed