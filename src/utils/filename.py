from dataclasses import dataclass
from datetime import date
@dataclass
class FilenameGenerator:
    
    discipline:str | None=None
    name:str | None=None
    country:str | None =None
    segment:str | None =None
    compet:str | None=None
    div:str | None=None
    year:str | None = None
    cat:str |None =None
    place:str | None = None
    begindate:date | None =  None

    @property
    def pdf_results_directory(self):
        parts = [ self.compet, self.year,self.segment,self.cat, self.div, self.discipline]
        directory="_".join(p for p in parts if p) if any(parts) else ""
        return directory
    
    @property
    def json_filename(self):
        
        
        parts = [self.cat, self.div, self.discipline, self.compet, self.year]
        optional = "_" + "_".join(p for p in parts if p) if any(parts) else ""
        
        info=f"{self.name}_{self.country}_{self.segment}"
        return f"{info}{optional}.json"
    
    @property
    def event_json(self):
        return f"{self.begindate.isoformat()}_{"-".join(self.compet.lower().split()).strip()}"