import logging
from pathlib import Path
from datetime import date

logger= logging.getLogger(__name__)

from src.event_scrapper.export import init_finc
from src.pdf_parser.domain import AdditionalInfo
from src.pdf_parser.parser import parser

def clean_parts(part):
    return " ".join(part.split("-")).title().strip()

def web_pdf(url,output=None):
    output,history=init_finc(url,dl_pdf=True,output=output)

    pdfs=sorted(output.glob("*.pdf"))

    for pdf_path in pdfs:
        date_comp,competition,category,segment= pdf_path.stem.split("_")

        addinfo=AdditionalInfo(
            name=clean_parts(competition),
            date=date.fromisoformat(date_comp),
            source_url=history[pdf_path.name]
        )


        parser(
            filename=pdf_path,
            dir=None,
            addinfo=addinfo,
            relative_dir=output
                )
        logger.info(f"Passing to next pdf if any")

    logger.info("Finished Parsing !")

