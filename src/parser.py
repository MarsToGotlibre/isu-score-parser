from src.clean import ScoreDocument
from src.domain import CompetitionInfo
from src.builder import ScoreSheetBuilder,yamlHandle
from src.export import FilenameFactory
from pathlib import Path

import os
import json
import logging
logger = logging.getLogger(__name__)

def validate_tables(tables):
    if tables==None:
        return
    
    required = {"general_info", "technical_score", "PCS","deduction"}
    missing=required-tables.keys()
    if missing :
        raise NameError(f"A table hasn't been found : {missing}")
    if len(tables["technical_score"]) == 0:
        raise IndexError("Empty technical score table")
    gen_info_col=tables["general_info"].columns
    if gen_info_col[0]!="Rank" or len(gen_info_col)<7:
        raise NameError("Parsing went wrong, recreating a mask for this page is necessary")

def parse_page(
    scoredoc: ScoreDocument,
    page: int,
    compinfo: CompetitionInfo,
    addinfo,
    scoredoc_override=None,
):
    scoredocument = scoredoc_override or scoredoc

    results = []
    for table_idx in range(scoredocument.page_mask.number_of_tables):
        tables = scoredocument.clean_tableData(
            table_idx=table_idx,
            page=page
        )
        if not tables:
            continue
        validate_tables(tables.tables)

        logger.info(f"Table extracted p{page}, index {table_idx}")

        json_dict = ScoreSheetBuilder.build(
            page_number=page,
            tables=tables,
            scoreDocument=scoredocument,
            table_idx=table_idx,
            compinfo=compinfo,
            addInfo=addinfo,
            **({"layout_strategy":"local"}if scoredoc_override else {})
        )
        logger.info(f"Json completed for Team/skater : {json_dict["results"]["team"]["name"]}")
        results.append(json_dict)

    return results

def write(results,directory):
    for result in results:
        if result:
            filename=FilenameFactory().from_dict(result).filename
            with open(Path(directory,filename),"w") as f :
                json.dump(result,f,indent=4)

def ensure_unique(dir_path: Path) -> Path:
    if not dir_path.exists():
        return dir_path
    

    i = 1
    while True:
        candidate = Path(f"{dir_path}_{i}")
        if not candidate.exists():
            return candidate
        i += 1


def create_dir(dir,compinfo:CompetitionInfo):
    if not dir:
        cwd=Path(__file__).parent.parent.resolve()
        
        dir_fact=FilenameFactory().from_conp_info(compinfo=compinfo)
        if CompetitionInfo.name:

            dir_name=ensure_unique(Path(cwd,"Data",dir_fact.directory))
        else:
            event=0
            with os.scandir(Path(cwd,"Data")) as it:
                for entry in it:
                    if entry.is_dir() and entry.name.startswith("EVENT_"):
                        number=int(entry.name.split("_")[1]) if entry.name.split("_")[1].isdigit() else event
                        if number>event :
                            event= number 

            dir_name=Path(cwd,"Data",f"EVENT_{(event+1):02d}_{dir_fact.directory}")
        os.mkdir(dir_name)
    else:
        dir_name=dir
    
    return dir_name
    
                        

            
    
def parser(filename,beginpage:int,endpage:int, dir,yaml_file=None,):
    addinfo=None
    if yaml_file:
        addinfo=yamlHandle.from_file(yaml_file)
    
    scoredoc=ScoreDocument.fromFile(filename=filename,page=beginpage)
    compinfo=CompetitionInfo.from_scoredoc(scoredoc).merge_config(addinfo)
    dir=create_dir(dir,compinfo=compinfo)
    for page in range(beginpage,endpage+1):
        try:
            results=parse_page(scoredoc, page, compinfo, addinfo)
            write(results,dir)
        except:
            logging.warning(f"Page {page}: layout mismatch, retrying with local PageMask")
            local_scoredoc=ScoreDocument.fromFile(filename=filename,page=page)
           
            results = parse_page(scoredoc,page,compinfo,addinfo,scoredoc_override=local_scoredoc)
            write(results,dir)