from pathlib import Path

from src.services.export_service import ExportService
from src.services.extraction_service import ExtractionService
from src.services.transformation_service import TransformationService
from src.utils.logger import logger


class Pipeline:

    def __init__(self):
        # Automatically ensure all output directories exist
        for directory in ["output/raw", "output/processed", "output/logs"]:
            Path(directory).mkdir(parents=True, exist_ok=True)

        self.extraction_service = ExtractionService()
        self.transformation_service = TransformationService()
        self.export_service = ExportService()

    def run(self) -> None:
        logger.info("Starting Partner Data Pipeline")

        try:
            # 1. Extraction (Raw API responses)
            raw_data = self.extraction_service.extract()
            logger.info("Extraction completed")

            # Save raw extraction responses into output/raw/
            self.export_service.export_json(
                raw_data,
                "output/raw/partners_raw.json",
            )

            # 2. Transformation (Deduplication, HTML scraping & Enrichment)
            partners = self.transformation_service.transform(raw_data)
            logger.info("Transformation completed")

            # 3. Export Processed Datasets into output/processed/
            self.export_service.export_json(
                partners,
                "output/processed/partners.json",
            )

            self.export_service.export_csv(
                partners,
                "output/processed/partners.csv",
            )

            logger.info("Export completed")
            logger.info("Partner Data Pipeline completed successfully.")

        except Exception:
            logger.exception("Partner Data Pipeline failed.")
            raise