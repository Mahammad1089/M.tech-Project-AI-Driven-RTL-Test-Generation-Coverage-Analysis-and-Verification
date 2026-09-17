import json
from datetime import datetime
from pathlib import Path


class ReportGenerator:

    def save_json(
        self,
        data,
        output_file
    ):

        path = Path(
            output_file
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        report = {

            "generated_at":
                datetime.now().isoformat(),

            **data

        }


        path.write_text(

            json.dumps(
                report,
                indent=4
            )

        )


        return report
