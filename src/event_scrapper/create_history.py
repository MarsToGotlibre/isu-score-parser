import json
import logging

logger= logging.getLogger(__name__)

def create_json_history(json_path):
    with open(json_path) as f:
        d= json.load(f)
        history={}

    categories=d.get("categories")
    if not categories:
        return
    
    from src.event_scrapper.eventscrapper_filename import EventscrapperFilenameFactory
    generator = EventscrapperFilenameFactory().from_json(d)
    
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

            filename= generator.event_segment_pdf

            history[filename]=pdf_url
            
            generator.reset_segment()
        
        generator.reset_category()
    return history