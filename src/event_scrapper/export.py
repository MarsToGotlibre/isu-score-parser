from bs4 import BeautifulSoup

from src.event_scrapper.utils import found_timezone_date,safe_fetch_html
from src.event_scrapper.domain_builders import CategoryBuilder
from src.event_scrapper.main_tables import MainPageTables

class EventPage:
    def __init__(self,url):
        self.url=url
        self.html= safe_fetch_html(url)
        self.soup= BeautifulSoup(self.html,"html.parser")

def init_finc(url):
    page=EventPage(url)

    event_dict={
        "event_url":url,
        "name":page.soup.title.text.strip()
    }
    
    found_timezone_date(page.soup,event_dict)

    maintables=MainPageTables().from_url(url)
    event_dict["place"],event_dict["location"]=maintables.return_location()
    
    event_dict["categories"]=[category.to_dict() for category in CategoryBuilder.from_main_page_table(maintables,url).build()]
    
    return event_dict

