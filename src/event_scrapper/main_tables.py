from dataclasses import dataclass,field
from collections import namedtuple
import pandas as pd

from src.event_scrapper.utils import get_correct_tables, return_iso_date

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
            case 'Starting Order / Detailed Classification':
                self.detail_class=value
                return self
            case 'Judges Scores (pdf)':
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
    location:pd.DataFrame | None = None
    categories:pd.DataFrame | None = None
    schedule:pd.DataFrame | None = None

    def from_url(self,url):
        self.from_list(get_correct_tables(url))
        return self

    
    def from_list(self,liste_table):
        for table in liste_table:
            if table.shape==(1,2) and (table.columns==[0,1]).all():
                self.location=table
                continue
            if (table.columns[:2]==['Category', 'Segment']).all():
                self.categories=table
                self.categories.Category=self.categories.Category.ffill()
                continue
            if (table.columns==['Date', 'Time', 'Category', 'Segment']).all():
                self.schedule= table
                self.schedule.Date=self.schedule.Date.ffill()
                self.schedule.dropna(ignore_index=True,inplace=True)
                continue
        
        return self
    
    def return_location(self):
        if not isinstance(self.location,pd.DataFrame):
            return 
        place=self.location.iloc[0,1].strip()

        location_str =self.location.iloc[0,0]
        locationsplit=location_str.split("/")

        location={}
        if len(locationsplit)==2:
            
            location["city"]=locationsplit[0].strip()
            location["country"]=locationsplit[1].strip()
            
        else :
            location["raw_location"]=location.strip()
        
        loc_tup=namedtuple("Loc_tup",["place","location_det"])
        return loc_tup(place=place,location_det=location)
    
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
                child["date"]=return_iso_date(segment.Date)
                child["time"]=segment.Time
                schedule_index[category][segment.Segment[0]]=child
                if not schedule_index[category].get(segment.Segment[1]):
                    schedule_index[category][segment.Segment[1]]=child
        
        return schedule_index