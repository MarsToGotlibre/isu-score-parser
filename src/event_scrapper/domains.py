from dataclasses import dataclass 
import pandas as pd

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

@dataclass # segment category
class Segment:
    name:str
    date:str
    time:str
    panel:list[Panel]
    detailed_results:list[DetailResults]
    pdf_url:str

    def to_dict(self):
        return {
            "segment":self.name,
            "date":self.date,
            "time":self.time,
            "panel":[
                panel.to_dict() for panel in self.panel
            ],
            "detailed_results":[
                detailResults.to_dict() for detailResults in self.detailed_results
            ],
            "pdf_url":self.pdf_url
        }

@dataclass
class Category:
    name:str
    entries:list[Entries]
    results:list[Results]
    segments:list[Segment]

    def to_dict(self):
        return {
            "category":self.name,
            "entries":[
                entry.to_dict() for entry in self.entries
            ],
            "results":[
                result.to_dict()  for result in self.results
            ],
            "segment":[
                segment.to_dict() for segment in self.segments
            ]
        }