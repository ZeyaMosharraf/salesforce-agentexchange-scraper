from src.services.extraction_service import ExtractionService
from src.services.transformation_service import TransformationService
from src.services.export_service import ExportService
from src.utils.logger import logger


class Pipeline:

    def __init__(self):

        self.extraction_service = ExtractionService()

        self.transformation_service = TransformationService()

        self.export_service = ExportService()

    def run(self) -> None:

        logger.info("Starting Partner Data Pipeline")

        try:
            raw_data = self.extraction_service.extract()

            logger.info("Extraction completed")

            partners = self.transformation_service.transform(
                raw_data
            )

            logger.info("Transformation completed")

            self.export_service.export_json(
                partners,
                "output/partners.json",
            )

            self.export_service.export_csv(
                partners,
                "output/partners.csv",
            )

            logger.info("Export completed")

            logger.info(
                "Partner Data Pipeline completed successfully."
            )

        except Exception:

            logger.exception(
                "Partner Data Pipeline failed."
            )

            raise