from dataclasses import dataclass,field
import pdfplumber
import re
import logging
from src.config import TableConfig
import camelot

logger = logging.getLogger(__name__)



            


@dataclass
class ContextParser:
    info_single_line:bool = False
    noc:bool = False
    no_judges:bool = False
    ded_table:bool = False
    
    ded_infos:bool = False

    comp_found:bool = False
    fst_tbl_passed:bool = False
    no_more_lines:bool = False

    signals:dict = field(default_factory=dict)

    def table_config(self):
        if not self.info_single_line:
            return  TableConfig.isu_2022()
        if self.ded_table:
            return TableConfig.isu_2005()
        if self.noc:
            return TableConfig.isu_2007()
        if self.no_judges:
            return TableConfig.isu_2014()
        return TableConfig.isu_2018()
    
    def signal_add(self,key,dict):
        entry=self.signals.get(key)
        if entry:
            entry.append(dict)
        else:
            self.signals[key]=[]
            self.signals[key].append(dict)


class TableMask:
    def __init__(self,generalinfo:tuple[float],techincal_score:tuple[float],PCS:tuple[float],deduction:tuple[float]):
        self.general_info=dict(zip(["y1","y0"],generalinfo))
        self.technical_score=dict(zip(["y1","y0"],techincal_score))
        self.pcs=dict(zip(["y1","y0"],PCS))
        self.deduction=dict(zip(["y1","y0"],deduction))
    
    def __str__(self):
        return (f"TableMask(\n"
                f"  general_info=    {self.general_info},\n"
                f"  technical_score= {self.technical_score},\n"
                f"  pcs=             {self.pcs},\n"
                f"  deduction=       {self.deduction}\n"
                f")")
    def __repr__(self):
        return (f"TableMask(\n"
                f"  general_info=    {self.general_info},\n"
                f"  technical_score= {self.technical_score},\n"
                f"  pcs=             {self.pcs},\n"
                f"  deduction=       {self.deduction}\n"
                f")")

@dataclass
class PageMask:
    height:float
    width:float
    number_of_tables:int
    tables:list[TableMask]
    program:str
    category:str
    division:str
    config:TableConfig
    signals:dict | None = None
    source_url:str | None = None
    
    @staticmethod
    def _invert_height(value,page_height):
        return (page_height-value)
    
    @classmethod
    def from_pdf(cls,page:pdfplumber.page.Page):
        
        PAGELINES=page.extract_text_lines(return_chars=False)
        
        #Fisrt marker and competition info
        COMPETITION_INFO=re.compile(r"(?:(N\d)\s)?(?:([A-Za-z\s]+)\s)(?:(\w+\s\w+))$")
        LEGACY_INFO=re.compile(r"(?:(N\d)\s)?(?:([A-Za-z\s]+)\s)(?:(\w+\s\w+)) JUDGES DETAILS PER SKATER")
        JUDGE_DETAILS=re.compile(r"(JUDGES DETAILS PER SKATER)")

        VOTE=re.compile(r"([A-Za-z\s&\-/\\]+):?\s*\((\d{1,2})\s+of\s+(\d{1,2})\)")
        
        # Multi era support

        # prior to 2018, judges were not displayed, only "Judge Panel" where mentioned. 
        # this lines help detect it to genereate the appropriate config object
        fst_tbl_passed=False
        NO_JUDGES=re.compile(r"The Judges Panel") 
        #Support for artistic competitions in mid 2010
        INFOS=re.compile(r"[<x=e\*q!]{1,2}\s?(?:[-\w\s]+\s?)")

        #Deduction in 2005 where group into a table
        DEDUCTIONS_05=re.compile(r"([A-Za-z\s&-]+):(?:\s+)?([0-9]{1,2}\.[0-9]{2})")
        #Nation was mentioned as NOC
        NOC=re.compile(r"NOC")
        
        ctx=ContextParser()
        BALISES =[
            {"pattern":re.compile(r"(\d+?)\s+?([\w\s\\]+)\s+([A-Z]{3})"),"balise":"bottom"},
            {"pattern":re.compile(r"(Program Components)"),"balise":"top"},
            {"pattern":re.compile(r"(Deductions)"),"balise":"top"}]
        i,n=0,len(BALISES)
        
        PAGE_HEIGHT=page.height

        y1,y0=PAGE_HEIGHT,0     #y1 is the top marker, y0 is the bottom marker
        number_of_tables=0

        Listtemp,tables=[],[]
        it=iter(PAGELINES)
        for line in it:

            #First marker is the "JUDGE DETAIL PER SKATER" line wich will define the top of the document
            #print(line["text"])
            if not ctx.comp_found:
                m = JUDGE_DETAILS.search(line["text"])
                if m:
                    if m.start() ==0:
                        prgrm_info=next(it)
                        current_display=COMPETITION_INFO.match(prgrm_info["text"]).groups()
                        if current_display:
                            ctx.fst_tbl_passed=True
                            division,category,program=current_display
                            logger.info(f"Found : {division} as division, {category} as category, {program} as program")
                            y1=cls._invert_height(prgrm_info["bottom"],PAGE_HEIGHT)
                    else: # in older sheets, the info is on the same line as "Judge detail per skater"
                        legacy_display=LEGACY_INFO.match(line["text"]).groups()
                        ctx.info_single_line=True
                        division,category,program=legacy_display
                        logger.info(f"Found : {division} as division, {category} as category, {program} as program as legacy display")
                        y1=cls._invert_height(line["bottom"],PAGE_HEIGHT)
                    ctx.comp_found = True
                continue

            # Once the first marker found we can keep continue on the other markers
            
            #This parts aims to detect a part of the config
            if not ctx.fst_tbl_passed:
                if not ctx.noc and NOC.search(line["text"]):
                    ctx.noc=True
                    logger.info("Old nation display")
                if NO_JUDGES.search(line["text"]):
                    ctx.no_judges=True
                    ctx.fst_tbl_passed=True
                    logger.info("Old judges display. No judges displayed in tables.")
                
            
            m=BALISES[i]["pattern"].match(line["text"])
            if m :
                
                y0=cls._invert_height(line[BALISES[i]["balise"]],PAGE_HEIGHT)
                Listtemp.append((y1,y0))
                
                y1=y0
                if i+1==n:
                    y0=cls._invert_height(line["bottom"],PAGE_HEIGHT)

                    try:
                        info_ded=next(it)
                        ded_05=DEDUCTIONS_05.match(info_ded["text"])
                        if ded_05 and ded_05.groups()[0]!="Printed":
                            y0=cls._invert_height(info_ded["bottom"],PAGE_HEIGHT)
                            ctx.ded_table=True
                            logger.info("2005 deduction tables")
                            info_ded=next(it)
                    except StopIteration:
                        logger.debug("No more lines to iterrate")
                        ctx.no_more_lines=True
                    

                    Listtemp.append((y1,y0))

                    if not ctx.no_more_lines: 
                        vote=VOTE.findall(info_ded["text"])
                        if vote:
                            y1=cls._invert_height(info_ded["bottom"],PAGE_HEIGHT)
                            ctx.signal_add("deduction_vote",{
                                "vote":vote,
                                "table_idx":number_of_tables
                            })
                            logger.info("Panel vote found")
                            try:
                                info_ded=next(it)
                            except StopIteration:
                                logger.debug("No more lines to iterrate")
                                ctx.no_more_lines=True
                    if not ctx.no_more_lines:    
                        info=  INFOS.match(info_ded["text"])
                        if info:
                            y1=cls._invert_height(info_ded["bottom"],PAGE_HEIGHT)
                    
                        if not info and not vote:
                            y1=y0
                    
                    number_of_tables+=1

                    tables.append(TableMask(*Listtemp))
                    Listtemp=[]
                    ctx.fst_tbl_passed=True
                    
                i=(i+1)%n
        assert ctx.comp_found==True
        logger.info(f"{number_of_tables} tables found on the page")
        return cls(PAGE_HEIGHT,page.width,number_of_tables,tables,program.lower(),category.lower(),division,config=ctx.table_config(),signals=ctx.signals)
    
    def from_file(self,file,page):
        with pdfplumber.open(file) as pdf:
                local_page = pdf.pages[page-1]
                local_pagemask=PageMask.from_pdf(local_page)
                return local_pagemask

class TableExtractor:
    def __init__(self, filename, page_width):
        self.filename = filename
        self.page_width = page_width

    def _extract_area(self, area, **kwargs):
        y1 = area["y1"]
        y0 = area["y0"]

        temp = camelot.read_pdf(
            self.filename,
            flavor="stream",
            table_areas=[f"0,{y1},{self.page_width},{y0}"],
            **kwargs
        )
        return temp[0].df


    def extract(self, table_mask: TableMask,config:TableConfig,page=1) -> dict:
        result = {}
        try:
            result["general_info"]=self._extract_area(area=table_mask.general_info,pages=str(page),**config.camelot_args["general_info"])
            
            result["technical_score"]=self._extract_area(table_mask.technical_score,pages=str(page),**config.camelot_args["technical_score"])
            result["PCS"]=self._extract_area(table_mask.pcs,pages=str(page),**config.camelot_args["PCS"])
        
        except :
            logger.warning(f"TableExtractor : a table have not been found page {page}.")
            return
        
        try:
            result["deduction"]=self._extract_area(table_mask.deduction, pages=str(page),**config.camelot_args["deductions"])
        except:
            logger.warning(f"TableExtractor : Deduction table not found")   
       
            
        return result