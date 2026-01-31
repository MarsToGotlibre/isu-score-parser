from src.event_scrapper.domain_builders import EventBuidler
import json
import logging

logger=logging.getLogger(__name__)

def init_finc(url):
    event=EventBuidler.from_url(url).build()
    logger.info("Event finished built.")
    
    with open(event.filename,"w",encoding="utf8") as f:
        json.dump(event.to_dict(),f,indent=4,ensure_ascii=False)
    logger.info(f"JSON generated under name : {event.filename}")
    return event.to_dict()

