from clean import ScoreDocument
from domain import CompetitionInfo
from builder import ScoreSheetBuilder,yamlHandle
from export import FilenameFactory

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
    pagemask_override=None,
):
    pagemask = pagemask_override or scoredoc.page_mask

    results = []
    for table_idx in range(pagemask.number_of_tables):
        tables = scoredoc.clean_tableData(
            table_idx=table_idx,
            page=page
        )
        validate_tables(tables.tables)
        

        json_dict = ScoreSheetBuilder.build(
            page_number=page,
            tables=tables,
            scoreDocument=scoredoc,
            table_idx=table_idx,
            compinfo=compinfo,
            addInfo=addinfo,
            **({"layout_strategy":"local"}if pagemask_override else {})
        )
        results.append(json_dict)

    return results

def write(results):
    for result in results:
        filename=FilenameFactory().from_dict(result).filename
        with open(filename,"w") as f :
            json.dump(result,f,indent=4)
    
def parser(filename,beginpage:int,endpage:int, yaml_file=None):
    addinfo=None
    if yaml_file:
        addinfo=yamlHandle.from_file(yaml_file)
    
    scoredoc=ScoreDocument.fromFile(filename=filename,page=beginpage)
    compinfo=CompetitionInfo.from_scoredoc(scoredoc).merge_config(addinfo)
    for page in range(beginpage,endpage+1):
        try:
            results=parse_page(scoredoc, page, compinfo, addinfo)
            write(results)
        except:
            logging.warning(f"Page {page}: layout mismatch, retrying with local PageMask")
            local_pagemask=scoredoc.page_mask.from_file(file=filename,page=page)
            
           
            results = parse_page(scoredoc,page,compinfo,addinfo,pagemask_override=local_pagemask)
            write(results)