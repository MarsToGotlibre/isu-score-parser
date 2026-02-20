from dataclasses import dataclass 
import pandas as pd
from datetime import date

from src.event_scrapper.eventscrapper_filename import FilenameGenerator

@dataclass
class Panel:
    first_name:str
    last_name:str
    gender:str
    function:str
    nation:str

    def to_dict(self):
        return {
            "nation":self.nation,
            "function":self.function,
            "name":{
                "first_name":self.first_name,
                "last_name":self.last_name,
                **({"gender":self.gender} if self.gender else {})
            }
        }

@dataclass 
class Entries:
    no:int
    name:str
    nation:str
    club:str | None=None

    def to_dict(self):
        return{
            "number":self.no,
            "name":self.name,
            "nation":self.nation,
            **({"club":self.club} if pd.notna(self.club) else {})
        }

@dataclass 
class SegmentPlace:
    segment:str
    place:int

    def to_dict(self):
        return {
            "segment":self.segment,
            "place":self.place
        }

@dataclass
class Results:
    
    name:str
    nation:str
    
    status:str
    places:list[SegmentPlace] | None = None
    points:float | None = None
    finalplace:int | None = None
    club:str | None = None

    def to_dict(self):
        return {
            **({"finalplace":self.finalplace} if pd.notna(self.finalplace) else {}),
            "name":self.name,
            **({"club":self.club} if pd.notna(self.club) else {}),
            "nation":self.nation,
            **({"totalpoints":self.points} if pd.notna(self.points) else {}),
            **({"places":[segmentplace.to_dict() for segmentplace in self.places]} if self.places else {}),
            "status":self.status
        }

@dataclass
class PcsParts:
    name:str
    score:float

    def to_dict(self):
        return {
            "pcs":self.name,
            "score":self.score
        }

@dataclass
class DetailResults:
    place:int
    name:str
    nation:str
    tss:float
    tes:float
    pcs:float
    detail_pcs:list[PcsParts]
    ded:float
    starting_number:int
    club:str | None=None

    def to_dict(self):
        return {
            "place":self.place,
            "name":self.name,
            "nation":self.nation,
            "tss":self.tss,
            "tes":self.tes,
            "pcs":self.pcs,
            "detailed_pcs":[pcs.to_dict() for pcs in self.detail_pcs],
            "deduction":self.ded,
            "starting_number":self.starting_number,
            **({"club":self.club} if pd.notna(self.club) else {})

        }

@dataclass 
class Segment:
    name:str
    pdf_url:str
    date:str | None = None
    time:str | None = None
    panel:list[Panel] | None = None
    detailed_results:list[DetailResults] | None = None

    def to_dict(self):
        return {
            "segment":self.name,
            **({"date":self.date} if self.time else {}),
            **({"time":self.time} if self.time else {}),
            **({"panel":[
                panel.to_dict() for panel in self.panel
            ]} if self. panel else {}),
            **({"detailed_results":[
                detailResults.to_dict() for detailResults in self.detailed_results
            ]} if self.detailed_results else {}),
            "pdf_url":self.pdf_url
        }

@dataclass
class Category:
    name:str
    entries:list[Entries] | None = None
    results:list[Results] | None = None
    segments:list[Segment] | None = None

    def to_dict(self):
        return {
            "category":self.name,
            **({"entries":[
                entry.to_dict() for entry in self.entries
            ]} if self.entries else {}),
            **({"results":[
                result.to_dict()  for result in self.results
            ]} if self.results else {} ),
            **({"segment":[
                segment.to_dict() for segment in self.segments
            ]} if self.segments else {})
        }

@dataclass
class Event:
    event_url:str
    event_name:str
    categories:list[Category] | None = None
    start_date:date  | None = None
    end_date:date | None = None
    timezone_raw:str | None = None
    timezone_offset:str | None = None
    timezone_minutes:int | None = None
    timezone_standard:str | None = None
    place:str | None = None
    
    city:str | None = None
    country:str | None = None
    raw_location:str | None = None
    extraction_metadata:dict | None = None

    name_generator:FilenameGenerator | None = None

    @property
    def filename(self):
        return self.name_generator.event_json

    def to_dict(self):
        return {
            **({"_extraction_metadata": self.extraction_metadata} if self.extraction_metadata else {}),
            "event_url":self.event_url,
            "name":self.event_name,
            "start_date":self.start_date.isoformat() if self.start_date else None,
            "end_date":self.end_date.isoformat() if self.end_date else None,
            **({"timezone":{
                **({"raw":self.timezone_raw} if self.timezone_raw else {}),
                **({"offset":self.timezone_offset} if self.timezone_offset else {}),
                **({"minutes":self.timezone_minutes} if self.timezone_minutes else {}),
                **({"standard":self.timezone_standard} if self.timezone_standard else {})
            }} if self.timezone_raw or self.timezone_standard or self.timezone_minutes or self.timezone_offset else {}),
            "arena":self.place,
            "location":{
                **({"raw_location":self.raw_location} if self.raw_location else {}),
                **({"city":self.city} if self.city else {}),
                **({"country":self.country} if self.country else {})
            },
            "categories":[ category.to_dict() for category in self.categories]
        }