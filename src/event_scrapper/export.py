import json
import logging
from pathlib import Path

logger=logging.getLogger(__name__)

def download_pdf(event_dict:dict,output_dir):
    import requests,datetime

    categories=event_dict.get("categories")
    if not categories:
        return
    
    from src.event_scrapper.eventscrapper_filename import EventscrapperFilenameFactory
    generator = EventscrapperFilenameFactory().from_json(event_dict)
    
    for category in categories:
        generator.cat=category["category"]

        segments = category.get("segment")
        if not segments:
            continue
        for segment in category.get("segment"):
            generator.segment=segment["segment"]
            generator.add_segmentdate(segment.get("date") )

            pdf_url=segment.get("pdf_url")
            if not pdf_url:
                continue

            with requests.get(pdf_url,stream=True) as r:
                r.raise_for_status()

                filename= generator.event_segment_pdf
                with open(Path(output_dir,filename),"wb") as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: 
                            f.write(chunk)
                    logger.info(f"PDF downloaded at {Path(output_dir,filename)}")
            
            generator.reset_segment()
        
        generator.reset_category()


def create_output_directory(event_dict):
    import os

    from src.event_scrapper.eventscrapper_filename import EventscrapperFilenameFactory
    generator = EventscrapperFilenameFactory().from_json(event_dict)
    
    cwd=Path(__file__).parent.parent.parent.resolve()
    output_dir=Path(cwd,"Data",generator.event_dir)
    
    os.mkdir(output_dir)
    logger.info(f"Output directory Created : {output_dir}")
    return output_dir

def init_finc(url,dl_pdf:bool=False,output=None):
    from src.event_scrapper.domain_builders import EventBuidler

    event=EventBuidler.from_url(url).build()
    logger.info("Event finished built.")

    event_dict=event.to_dict()

    if not output:
        output=create_output_directory(event_dict)
    
    output_file=event.filename
    with open(Path(output,output_file),"w",encoding="utf8") as f:
        json.dump(event_dict,f,indent=4,ensure_ascii=False)
    logger.info(f"JSON generated under name : {output}")

    if dl_pdf:
        download_pdf(event_dict,output)
        
    return event.to_dict()

