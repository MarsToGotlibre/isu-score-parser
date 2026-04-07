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
    segmentdate:date | None = None

    @property
    def date(self):
        return self.segmentdate or self.begindate

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
        return f"{self.begindate.isoformat()}_{self.clean_string(self.compet)}.json"
    
    @property 
    def event_segment_pdf(self):
        return f"{self.date.isoformat()}_{self.clean_string(self.compet)}_{self.clean_string(self.cat)}_{self.clean_string(self.segment)}.pdf"
    
    @property
    def event_dir(self):
        return f"{self.begindate.isoformat()}_{self.clean_string(self.compet)}"

    def reset_segment(self):
        self.segment=None
        self.segmentdate = None
    
    def reset_category(self):
        self.cat= None

    @staticmethod
    def convert_to_datetime(newdate):
        if not isinstance(newdate,date):
            return date.fromisoformat(newdate)
        
        return newdate

    def add_begindate(self,newdate):
        if not newdate:
            return
        self.begindate= self.convert_to_datetime(newdate)
    
    def add_segmentdate(self,newdate):
        if not newdate:
            return
        self.segmentdate = self.convert_to_datetime(newdate)

    @staticmethod
    def clean_string(longstring):
        return "-".join(longstring.lower().split()).strip()