import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.logger import logger


class ExportService:

    def export_json(self, partners: list[dict[str, Any]], output_path: str,) -> None:

        try:

            Path(output_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with open(
                output_path,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    partners,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            logger.info(
                f"JSON exported to {output_path}"
            )

        except Exception:

            logger.exception(
                "Failed to export JSON"
            )

            raise

    def export_csv(self, partners: list[dict[str, Any]], output_path: str,) -> None:

        try:

            Path(output_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            rows = [
                self._flatten_partner(partner)
                for partner in partners
            ]

            dataframe = pd.DataFrame(rows)

            dataframe.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig",
            )

            logger.info(
                f"CSV exported to {output_path}"
            )

        except Exception:

            logger.exception(
                "Failed to export CSV"
            )

            raise

    def _flatten_partner( self, partner: dict[str, Any],) -> dict[str, Any]:

        row = {}

        for key, value in partner.items():

            if isinstance(value, dict):

                for sub_key, sub_value in value.items():

                    row[f"{key}_{sub_key}"] = sub_value

            elif isinstance(value, list):

                row[key] = json.dumps(
                    value,
                    ensure_ascii=False,
                )

            else:

                row[key] = value

        return row