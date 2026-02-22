from dataclasses import dataclass,field
from collections import namedtuple
import pandas as pd
import logging

from src.event_scrapper.utils import return_iso_date,safe_fetch_html,get_correct_tables
from src.event_scrapper.layout_extractor import EventInfo
from src.event_scrapper.layout_detector import HTMLLayout


logger=logging.getLogger(__name__)

@dataclass
class Segment_idx:
    segment:str
    panel:str | None = None
    detail_class:str | None = None
    pdf:str | None = None

    def fill_entries(self,key,value):
        clean_key = " ".join(key.split()).strip()

        match clean_key:
            case 'Panel of Judges':
                self.panel=value
                return self
            case 'Officials':
                self.panel=value
                return self
            case 'Starting Order / Detailed Classification':
                self.detail_class=value
                return self
            case 'Starting Order / Result Detail':
                self.detail_class=value
                return self
            case "Starting Order / Result Details":
                self.detail_class=value
                return self
            case 'Judges Scores (pdf)':
                self.pdf=value
                return self
            case 'Judges Scores pdf':
                self.pdf=value
                return self
            case 'Judges Scores, pdf':
                self.pdf=value
                return self
            case 'Judges Scores (pdf) Randomized':
                self.pdf=value
                return self


@dataclass
class Category_idx:
    category:str
    entries:str | None = None
    result:str | None = None
    segments:list[Segment_idx] = field(default_factory=list)

    def fill_entries(self,key,value):
        match key:
            case 'Entries':
                self.entries=value
                return self
            case 'Result':
                self.result=value
                return self
            
    def add_segment(self,segment):
        self.segments.append(segment)



@dataclass
class MainPageTables:
    categories:pd.DataFrame | None = None
    schedule:pd.DataFrame | None = None
    event_info:EventInfo | None = None

    def from_url(self,url):
        html = safe_fetch_html(url)

        layout=HTMLLayout.from_html(html=html)
        layout_type=layout.detect()

        extractor = layout.get_extractor()

        if not extractor:
            logger.error("No extractor available for detected ayout")
            return self
        
        extracted_data=extractor.extract(html=html)
        self.event_info = extracted_data.eventinfo
        self.schedule = extracted_data.schedule_df
        self.categories = extracted_data.categories_df

        if isinstance(self.categories, pd.DataFrame):
            self.categories.Category = self.categories.Category.ffill()
        
        if isinstance(self.schedule, pd.DataFrame):
            self.schedule.Date = self.schedule.Date.ffill()
            self.schedule.dropna(ignore_index=True, inplace=True)
            
        logger.info(f"MainPageTables extracted with layout: {layout_type}")
        return self
    
    def category_index(self):
        assert isinstance(self.categories,pd.DataFrame)
            
        index_cat=[]
        for cat, group_cat in self.categories.groupby("Category"):
            category_idx=Category_idx(category=cat)

            segment_it=group_cat.itertuples()

            resume=next(segment_it)
            for key,value in resume[3:5]:
                category_idx.fill_entries(key=key,value=value)
            
            for segment in segment_it:
                segment_idx=Segment_idx(segment=segment.Segment)

                for key, url_value in segment[3:]:
                    segment_idx.fill_entries(key=key,value=url_value)
                
                category_idx.add_segment(segment_idx)

            index_cat.append(category_idx)
        
        return index_cat

    def schedule_index(self):
        if not isinstance(self.schedule,pd.DataFrame):
            return

        schedule_index={}
        for category, group_cat in self.schedule.groupby("Category"):
            schedule_index[category]={}

            for segment in group_cat.itertuples():
                child={}
                child["date"]=return_iso_date(segment.Date).isoformat()
                child["time"]=segment.Time
                schedule_index[category][segment.Segment[0]]=child
                if not schedule_index[category].get(segment.Segment[1]):
                    schedule_index[category][segment.Segment[1]]=child
        
        return schedule_index