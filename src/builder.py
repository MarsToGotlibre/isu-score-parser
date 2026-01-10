import numpy as np
import pandas as pd
import re
import datetime

def nan_to_none(x):
    if not isinstance(x,list) and pd.isna(x):
        return None
    if isinstance(x,(np.integer,np.floating)):
        return x.item()
    return x

from src.domain import Team,Scores,TechnicalElement,ProgramComponents,Results
from src.domain import Deduction,MetaInfo,VoteSignals,AdditionalInfo,CompetitionInfo

class TeamBuilder:
    def from_df(df:pd.DataFrame) -> Team:
        name=df["Name"].iloc[0]
        
        country=df.get("Nation") 
        if country is None:
            country=df.get("NOC Code")
        country=country.iloc[0]
        
        starting_number=df.get("Starting Number")
        if starting_number is not None:
            starting_number=int(starting_number.iloc[0])
        return Team(name,country,starting_number)
    

class ScoresBuilder:
    def from_df(gen_info:pd.DataFrame,tech_resume:pd.DataFrame) -> Scores:
        rank=int(gen_info["Rank"].iloc[0])
        total_segment_score=float(gen_info["Total Segment Score"].iloc[0])
        total_technical=float(gen_info["Total Element Score"].iloc[0])
        base_value=float(tech_resume["Base Value"].iloc[0])

        components=gen_info.get("Total Program Component Score (factored)")
        if components is None:
            components=gen_info.get("Total Program Component Score (factorized)")
        components=float(components.iloc[0])
        ded=float(gen_info["Total Deductions"].iloc[0])
        deductions=-abs(ded) if ded >0 else ded
        return Scores(rank,total_segment_score,total_technical,base_value,components,deductions)
    
class TechnicalElementBuilder :
    def from_df(df:pd.DataFrame)-> list[TechnicalElement]:
        elements=[]

        for elem in df.itertuples():
            elements.append(
                TechnicalElement(
                    order=elem.Order,
                    element=elem.Executed_Elements,
                    base_value=elem.Base_Value,
                    goe=elem.GOE,
                    panel_score=elem.Scores_of_Panel,
                    J1=nan_to_none(getattr(elem,"J1",None)),
                    J2=nan_to_none(getattr(elem,"J2",None)),
                    J3=nan_to_none(getattr(elem,"J3",None)),
                    J4=nan_to_none(getattr(elem,"J4",None)),
                    J5=nan_to_none(getattr(elem,"J5",None)),
                    J6=nan_to_none(getattr(elem,"J6",None)),
                    J7=nan_to_none(getattr(elem,"J7",None)),
                    J8=nan_to_none(getattr(elem,"J8",None)),
                    J9=nan_to_none(getattr(elem,"J9",None)),
                    J10=nan_to_none(getattr(elem,"J10",None)),
                    J11=nan_to_none(getattr(elem,"J11",None)),
                    J12=nan_to_none(getattr(elem,"J12",None)),
                    ref=nan_to_none(getattr(elem,"Ref",None)),
                    info=nan_to_none(getattr(elem,"Info",None)),
                    elm_ded=nan_to_none(getattr(elem,"Elm_Ded",None)),
                    bonus=nan_to_none(getattr(elem,"BV_Bonus",None))
                )
            )
        return elements
        
class ComponentsBuilder:
    def from_df(df:pd.DataFrame) -> list[ProgramComponents]:
        components=[]

        i=1
        for comp in df.itertuples():
            
            if pd.isna(comp.Program_Components):
                Program_comp=f"Unamed Component {i}"
                i+=1
            else :
                Program_comp=comp.Program_Components
            components.append(
                ProgramComponents(
                    name=Program_comp,
                    factor=comp.Factor,
                    panel_score=comp.Scores_of_Panel,
                    J1=getattr(comp,"J1",None),
                    J2=getattr(comp,"J2",None),
                    J3=getattr(comp,"J3",None),
                    J4=getattr(comp,"J4",None),
                    J5=getattr(comp,"J5",None),
                    J6=getattr(comp,"J6",None),
                    J7=getattr(comp,"J7",None),
                    J8=getattr(comp,"J8",None),
                    J9=getattr(comp,"J9",None),
                    J10=getattr(comp,"J10",None),
                    J11=getattr(comp,"J11",None),
                    J12=getattr(comp,"J12",None),
                )
            )
        return components

class DeductionBuilder:
    def from_df(df:pd.DataFrame) -> list[Deduction]:
        ded_list=[]
        if not pd.isna(df.iloc[0,1]):
            pattern=re.compile(r"((?:[A-Za-z-&]+\s?)+):?\s(-\d+\.\d{2})\s?(?:\((\d+)\))?")
            m=pattern.findall(df.iloc[0,1])
            #print(m)
            for deduction in m:
                name,ded,amount=deduction
                ded_list.append(Deduction(
                    type=name,
                    deduction=float(ded),
                    amount=int(amount) if amount!="" else None
                ))
        return ded_list

from src.clean import ScoreDocument
class VoteBuilder: 

    @staticmethod
    def _add(dict,key,obj):
        entry=dict.get(key)
        if entry:
            entry.append(obj)
        else:
            dict[key]=[]
            dict[key].append(obj)

    def from_scoredoc(self,scoreDoc:ScoreDocument,table_idx):
        signals_dict=scoreDoc.page_mask.signals
        if not signals_dict:
            return[]
        vote_list=[]
        poped=[]
        for i,vote in enumerate(signals_dict.get("deduction_vote")):
            if vote["table_idx"]==table_idx:
                for elem in vote["vote"]:
                    arg,for_vote,voters=elem
                    vote_list.append(VoteSignals(
                        arg,int(for_vote),int(voters)
                    )) 
                poped.append(i)
        for i in poped:
            signals_dict["deduction_vote"].pop(i)
        if len(signals_dict["deduction_vote"])==0:
            signals_dict={}
        return vote_list
                    
        

class MetaInfoBuilder:
    def build(sourcefile,page,number_of_tables,table_idx,layout_strategy="global",vote=[],source_url=None):
        return MetaInfo(
            sourcefile=sourcefile.name,
            page=page,
            date_parsing= datetime.date.today().isoformat(),
            number_of_tables=number_of_tables,
            table_idx=table_idx,
            layout_strategy=layout_strategy,
            parser_version="1.0",
            shema_version="1.0",
            vote=vote,
            source_url=source_url
        )
    def build_from_scoreDoc(scoredoc:ScoreDocument,page,table_idx,layout_strategy="global",addinfo:AdditionalInfo=None):
        vb=VoteBuilder()
        return MetaInfo(
            sourcefile=scoredoc.filename.name,
            page=page,
            date_parsing=datetime.date.today().isoformat(),
            number_of_tables=scoredoc.page_mask.number_of_tables,
            table_idx=table_idx,
            layout_strategy=layout_strategy,
            parser_version="1.0",
            shema_version="1.0",
            vote= vb.from_scoredoc(scoreDoc=scoredoc,table_idx=table_idx),
            source_url=addinfo.source_url if addinfo else None
            )
    
class ResultsBuilder:
    def from_tables(tables):
        general_df=tables["general_info"]
        tes_df=tables["technical_score"]
        pcs_df=tables["PCS"]
        deduction_df=tables["deduction"]
        tes_resume_df=tables["technical_resume"]
        pcs_resume_df=tables["PCS_resume"]
        return Results(
            team=TeamBuilder.from_df(general_df),
            result=ScoresBuilder.from_df(general_df,tes_resume_df),
            technical_elements=TechnicalElementBuilder.from_df(tes_df),
            components=ComponentsBuilder.from_df(pcs_df),
            deductions=DeductionBuilder.from_df(deduction_df))

class yamlHandle:
    def from_file(yaml_file):
        import yaml
        with open(yaml_file,"r",encoding="utf-8") as f:
            raw=yaml.safe_load(f)
        version=raw.get("schema_version")

        if not version:
            raise ValueError("Schema version not found")

        if version!=1:
            raise ValueError(f"Version of the yaml config not supported : {version}")
        
        return AdditionalInfo.from_yaml(raw)

class ScoreSheetBuilder:
    def build(page_number,tables,table_idx,scoreDocument:ScoreDocument,addInfo=None,compinfo=None,**kwargs):
        metainfo=MetaInfoBuilder.build_from_scoreDoc(scoredoc=scoreDocument,page=page_number,table_idx=table_idx,addinfo=addInfo,**kwargs)
        if not compinfo:
            compinfo=CompetitionInfo.from_scoredoc(scoreDocument).merge_config(addInfo)
        result=ResultsBuilder.from_tables(tables)
        return {
            "meta":metainfo.to_dict(),
            "competition":compinfo.to_dict(),
            "results":result.to_dict()
        }