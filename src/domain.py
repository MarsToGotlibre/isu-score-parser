from dataclasses import dataclass
import datetime
from dataclasses import field
@dataclass
class Team:
    name:str
    country:str
    starting_number:int | None= None

    def to_dict(self):
        return{
            "name":self.name,
            "country":self.country,
            **({"starting_number":self.starting_number} if self.starting_number else {})
        }

@dataclass
class Scores:
    rank:int
    total_segment_score:float
    total_technical:float
    base_value:float
    components:float
    deductions:float

    def to_dict(self):
        return{
            "rank":self.rank,
            "scores":{
                "total":self.total_segment_score,
                "technical":{
                    "total":self.total_technical,
                    "base_value":self.base_value,
                },
                "components":self.components,
                "deductions":self.deductions
            }
        }

@dataclass
class TechnicalElement:
    order:int
    element:str
    base_value:float
    goe:float
    panel_score:float
    J1:int | None = None
    J2:int | None = None
    J3:int | None = None
    J4:int | None = None
    J5:int | None = None
    J6:int | None = None
    J7:int | None = None
    J8:int | None = None
    J9:int | None = None
    J10:int | None = None
    J11:int | None = None
    J12:int | None = None
    
    info:str | None = None
    ref:str | None = None
    elm_ded:float | None = None
    bonus:bool | None=None

    def to_dict(self):
        return{
            "order":self.order,
            "element":self.element,
            "base_value":self.base_value,
            "goe":self.goe,
            "panel_score":self.panel_score,
            "judges":{
                f"J{i}": getattr(self, f"J{i}") 
                for i in range(1, 13)
                if getattr(self, f"J{i}") is not None
            },
            **({"info": self.info} if self.info is not None else {}),
            **({"ref": self.ref} if self.ref is not None else {}),
            **({"elm_ded": self.elm_ded} if self.elm_ded is not None else {}),
            **({"bonus": self.bonus} if self.bonus else {}),

        }

@dataclass
class ProgramComponents:
    name:str
    factor:float
    panel_score:float
    J1:float | None = None
    J2:float | None = None
    J3:float | None = None
    J4:float | None = None
    J5:float | None = None
    J6:float | None = None
    J7:float | None = None
    J8:float | None = None
    J9:float | None = None
    J10:int | None = None
    J11:int | None = None
    J12:int | None = None

    def to_dict(self):
        return{
            "name":self.name,
            "factor":self.factor,
            "panel_score":self.panel_score,
            "judges":{
                f"J{i}": getattr(self, f"J{i}") 
                for i in range(1, 13)
                if getattr(self, f"J{i}") is not None
            }
        }

@dataclass   
class Deduction:
    type:str
    deduction:float
    amount:int | None = None

    def to_dict(self):
        return{
            "type":self.type,
            "deduction":self.deduction,
            **({"amount":self.amount} if self.amount is not None else {})
        }
    
@dataclass 
class AdditionalInfo:
    name:str | None= None
    country:str | None= None
    city:str | None= None
    date:datetime.date | None= None
    season:str | None= None
    source_url:str | None = None

    @classmethod
    def from_yaml(cls,data:dict):
        comp=data.get("competition",{})
        loc=comp.get("location",{})
        raw_date=data.get("date")
        if  isinstance(raw_date,str):
            try:
                raw_date=datetime.date.fromisoformat(raw_date)
            except ValueError:
                raise ValueError(f"Invalid date format in YAML, expected YYYY-MM-DD")
        return cls(
            name=comp.get("name"),
            country=loc.get("country"),
            city=loc.get("city"),
            date=comp.get("date"),
            season=data.get("season"),
            source_url=data.get("source_url")
        )

from clean import ScoreDocument
@dataclass 
class CompetitionInfo:
    segment:str
    category:str
    division:str | None= None
    name:str| None= None
    country:str | None= None
    city:str | None= None
    date:datetime.date | None= None
    season:str | None= None

    @classmethod
    def from_scoredoc(cls,scoreDocument:ScoreDocument):
        return cls(scoreDocument.page_mask.program,scoreDocument.page_mask.category,scoreDocument.page_mask.division)
    @classmethod
    def from_page_mask(cls,page_mask):
        return cls(page_mask.program,page_mask.category,page_mask.division)

    def to_dict(self):
        
        return {
            "category":self.category,
            "segment":self.segment,
            **({"division": self.division} if self.division is not None else {}),
            **({"name": self.name} if self.name is not None else {}),
            **({"location":{
                **({"country": self.country} if self.country is not None else {}),
                **({"city": self.city} if self.city is not None else {})}
             } if self.country or self.city else {}),
            **({"season": self.season} if self.season is not None else {}),
            **({"date": self.date.isoformat()} if self.date is not None else {}),
        
        }
    
    def merge_config(self,addInfo:AdditionalInfo):
        if not addInfo:
            return self
        if addInfo.name:
            self.name=addInfo.name
        if addInfo.country:
            self.country=addInfo.country
        if addInfo.city:
            self.city=addInfo.city
        if addInfo.season:
            self.season=addInfo.season
        if addInfo.date:
            self.date=addInfo.date

@dataclass
class VoteSignals:
    vote:str
    for_vote:int
    voters:int

    def to_dict(self):
        return{
            "type":self.vote,
            "tally":{
                "in_favor":self.for_vote,
                "total":self.voters
            }
            
        }

@dataclass
class MetaInfo:
    sourcefile:str
    page:int
    date_parsing:str
    number_of_tables:int
    table_idx:int
    parser_version:str
    shema_version:str
    layout_strategy:str
    vote:list[VoteSignals] = field(default_factory=list)
    source_url:str | None = None

    def to_dict(self):
        return{
            "sourcefile":self.sourcefile,
            **({"source_url":self.source_url} if self.source_url else {}),
            "page":self.page,
            "date_parsing":self.date_parsing,
            "nbr_tables_per_page":self.number_of_tables,
            "table_index":self.table_idx,
            "parser_version":self.parser_version,
            "schema_version":self.shema_version,
            "layout_strategy":self.layout_strategy,
            **({"deduction_vote":[v.to_dict() for v in self.vote]} if len(self.vote)>0 else {})
            
        }


@dataclass
class Results:
    team:Team
    result:Scores
    technical_elements:list[TechnicalElement]
    components:list[ProgramComponents]
    deductions:list[Deduction] | list

    def to_dict(self):
        return{
            "team":self.team.to_dict(),
            **(self.result.to_dict()),
            "technical_elements":[ elem.to_dict() for elem in self.technical_elements],
            "components":[comp.to_dict() for comp in self.components],
            "deductions":[ded.to_dict() for ded in self.deductions]
        }