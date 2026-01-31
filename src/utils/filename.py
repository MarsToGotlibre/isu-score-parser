from dataclasses import dataclass
@dataclass
class FilenameGenerator:
    
    discipline:str | None=None
    name:str | None=None
    country:str | None =None
    segment:str | None =None
    compet:str | None=None
    div:str | None=None
    date:str | None = None
    cat:str |None =None

    @property
    def pdf_results_directory(self):
        parts = [ self.compet, self.date,self.segment,self.cat, self.div, self.discipline]
        directory="_".join(p for p in parts if p) if any(parts) else ""
        return directory
    
    @property
    def json_filename(self):
        
        
        parts = [self.cat, self.div, self.discipline, self.compet, self.date]
        optional = "_" + "_".join(p for p in parts if p) if any(parts) else ""
        
        info=f"{self.name}_{self.country}_{self.segment}"
        return f"{info}{optional}.json"