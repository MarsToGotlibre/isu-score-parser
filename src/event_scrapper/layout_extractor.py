from dataclasses import dataclass
from typing import Optional
from datetime import date
from bs4 import BeautifulSoup
import pandas as pd
import logging
import re

from src.event_scrapper.utils import return_iso_date,get_correct_tables


logger=logging.getLogger(__name__)

@dataclass
class EventInfo:
    name: Optional[str] = None
    arena: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone_raw: Optional[str] = None
    timezone_standard: Optional[str] = None
    timezone_offset:Optional[str]  = None
    timezone_minutes:Optional[int]  = None
    raw_location: Optional[str] = None


@dataclass
class ExtractedPageData:
    eventinfo:EventInfo
    categories_df:pd.DataFrame | None = None
    schedule_df:pd.DataFrame | None = None
    layout_type:str="unknown"

class OldDisplayExtractor:
    def __init__(self,main_div :BeautifulSoup):
        self.main_div=main_div

    def extract(self,html):
        tables=self._extract_tables(html)

        return ExtractedPageData(
            eventinfo= self._extract_event_info(),
            categories_df=tables.get("categories"),
            schedule_df=tables.get("schedule"),
            layout_type="old_display"
        )
    
    def _extract_event_info(self) -> EventInfo:
        h2_list = self.main_div.find_all("h2")
        h3_list = self.main_div.find_all("h3")
        
        event_info = EventInfo()
        
        if h2_list:
            name = h2_list[0].get_text(strip=True)
            m=re.search(r"\d{1,2}\.-\d{1,2}\.\d{1,2}\.(\d{4})$",name)
            if m:
                name=name[:m.start()].strip() + f" {m.group(1)}"
            if name.upper()==name:
                name=name.title()
            event_info.name=name
        
        if len(h3_list) >= 3:
            event_info.city = h3_list[0].get_text(strip=True)
            
            dates_text = h3_list[1].get_text(strip=True)
            dates_match = re.match(
                r"(\d{1,2}[./]\d{1,2}[./]\d{4})\s*-\s*(\d{1,2}[./]\d{1,2}[./]\d{4})",
                dates_text
            )
            if dates_match:
                event_info.begin_date = return_iso_date(dates_match.group(1))
                event_info.end_date = return_iso_date(dates_match.group(2))
            
            arena_text = h3_list[2].get_text(strip=True)
            if arena_text:
                event_info.arena = arena_text
        
        return event_info
    
    def _extract_tables(self,html) -> dict: 
        list_table=get_correct_tables(html)

        result={}

        for table in list_table:
        
            if (table.columns[:2].isin(['Category', 'Segment'])).all():
                logger.info("Category table found")
                result["categories"]=table
                continue
            if (table.columns.isin(['Date', 'Time', 'Category', 'Segment'])).all():
                logger.info("Schedule table found")
                result["schedule"]=table
                continue
        
        return result


class TableDisplayExtractor:

    def __init__(self,soup:BeautifulSoup):
        self.soup=soup

    def extract(self,html,) ->ExtractedPageData:
        soup =self.soup
        tables= self._extract_tables(html=html)
        event_info= self._extract_event_info(location_df=tables.get("location"))

        return ExtractedPageData(
            eventinfo=event_info,
            categories_df=tables.get("categories"),
            schedule_df=tables.get("schedule"),
            layout_type="table_display"
        )

    def _extract_tables(self, html: str) -> dict:
        list_table=get_correct_tables(html)

        result={}
        
        for table in list_table:
            if table.shape==(1,2) and (table.columns==[0,1]).all():
                logger.info("Location table found")
                result["location"]=table
                continue
            if (table.columns[:2]==['Category', 'Segment']).all():
                logger.info("Category table found")
                result["categories"]=table
                continue
            if (table.columns==['Date', 'Time', 'Category', 'Segment']).all():
                logger.info("Schedule table found")
                result["schedule"]=table
                continue
        return result

    def _extract_event_info(self, location_df: Optional[pd.DataFrame]) -> EventInfo:
        event_info=EventInfo()

        self._extract_loc_df(location_df=location_df,event_info=event_info)
        self._find_timezone_date(event_info=event_info)
        event_info.name=self.soup.title.get_text(strip=True)
        
        return event_info


        
    def _extract_loc_df(self,location_df:pd.DataFrame,event_info:EventInfo):
        if not isinstance(location_df,pd.DataFrame):
            return
             
        event_info.arena=location_df.iloc[0,1].strip()

        location_str = location_df.iloc[0,0]
        locationsplit=location_str.split("/")

        if len(locationsplit)==2:
            
            event_info.city=locationsplit[0].strip()
            event_info.country=locationsplit[1].strip()
            
        else :
            event_info.raw_location=location_str.strip()
        
        

    def _find_timezone_date(self,event_info:EventInfo):
        soup=self.soup
        date = re.compile(r"(\d{1,2}[./]\d{1,2}[./]\d{4}) - (\d{1,2}[./]\d{1,2}[./]\d{4})")
        for td in soup.find_all("td"):
            d= date.match(" ".join(td.text.split()).strip())
            if d :
                assert len(d.groups())==2
                event_info.begin_date = return_iso_date(d.group(1))
                event_info.end_date = return_iso_date(d.group(2))
                continue
            if "Local Time" in td.text:
                timezone=td.text.strip("()").split(",")
                if len(timezone)>1:
                    event_info.timezone_raw = timezone[1].strip()
                    self.timezone_management(event=event_info)
                

    @staticmethod
    def timezone_management(event:EventInfo):
        if not event.timezone_raw:
            return
        
        m=re.match(r"(UTC|GMT)\s*([+-]\d{2}:\d{2})",event.timezone_raw)
        if m:
            event.timezone_standard = m.group(1)
            event.timezone_offset = m.group(2)

            sign= -1 if event.timezone_offset.startswith("-") else 1
            hours,minutes= map(int,m.group(2)[1:].split(":"))
            event.timezone_minutes = sign*(hours*60 + minutes)
 