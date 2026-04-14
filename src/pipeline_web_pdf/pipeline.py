import logging
from pathlib import Path
from datetime import date
from dataclasses import dataclass
import re

logger= logging.getLogger(__name__)

from src.event_scrapper.create_history import create_json_history
from src.pdf_parser.domain import AdditionalInfo
from src.pdf_parser.parser import parser

def clean_parts(part):
    return " ".join(part.split("-")).title().strip()


@dataclass
class Event_pdf_pipeline:
    relative_dir:Path |None = None
    pdfs:list[Path] |None = None
    history:dict |None = None
    url:str |None = None

    @classmethod
    def from_url(cls,url,output_dir=None):
        return cls(
            relative_dir=output_dir,
            url=url
        )
    

    def get_pdfs_from_dir(self):
        self.pdfs= sorted(self.relative_dir.glob("*.pdf"))
    
    @staticmethod
    def name_is_normalised(name):
        m= re.match(r"(\d{4}-\d{2}-\d{2})_([a-z-]+)_([a-z-]+)_([a-z-]+)\.pdf",name)
        if m:
            return{
                "date":date.fromisoformat(m.group(1)),
                "competition":clean_parts(m.group(2)),
                #"category":clean_parts(m.group(3)),
                #"segment":clean_parts(m.group(4))
            }
        return False
    
    def addinfo(self,filename):
        norm=self.name_is_normalised(filename)

        add_info=AdditionalInfo()

        if self.history :
            add_info.source_url=self.history[filename]
        if norm:
            add_info.date=norm["date"]
            add_info.name=norm["competition"]
        
        return add_info
    
    def history_from_json_in_dir(self):
        temp=sorted(self.relative_dir.glob("*.json"))
        if len(temp)>1:
            logger.warning(f"Multiples jsons were found, the url wont be added to the metadatas")
            return
        
        self.history=create_json_history(temp[0])
    
    
    def run_parser(self, pdf_path):
        parser(
                filename=pdf_path,
                dir=None,
                relative_dir=self.relative_dir,
                addinfo=self.addinfo(pdf_path.name)
            )

               
    
    def build_web_pipeline(self):
        from src.event_scrapper.export import init_finc

        self.relative_dir,self.history=init_finc(self.url,dl_pdf=True,output=self.relative_dir)
        
        self.get_pdfs_from_dir()


    def build_from_folder(self):
        self.get_pdfs_from_dir()

        if not self.pdfs: 
            logger.warning(f"The Folder : {self.relative_dir} doesn't contain any pdfs")
            return

        self.history_from_json_in_dir()

    def run(self):
        for pdf_path in self.pdfs:
            self.run_parser(pdf_path=pdf_path)
        
        logger.info("Finished Parsing !")
