import pandas as pd
from dataclasses import dataclass,field
from urllib.parse import urljoin
import logging

from src.event_scrapper.utils import get_correct_tables
from src.event_scrapper.domains import Panel,Entries,SegmentPlace,Results,PcsParts,DetailResults,Segment,Category
from src.event_scrapper.main_tables import MainPageTables,Category_idx


class PanelBuilder:
    @staticmethod
    def name_parts(name):
        import regex
        m=regex.match(r"(Mr?s?)\.\s((?:[\p{Lu}][\p{Ll}]+\s?)+)\s([-\s\p{Lu}]+)",name)
        
        return m.groups() if m else (None,None,None)
    
    @staticmethod
    def gender(string):
        match string:
            case "Ms":
                return "Women"
            case "Mr":
                return "Men"
        return
            
    
    def from_url(self,url):
        dfs=get_correct_tables(url,extract_links=None)
        panel_df=[]
        for df in dfs :
            if (df.columns == ["Function","Name","Nation"]).all():
                
                panel_df=df
                break
            elif (df.iloc[0] == ["Function","Name","Nation"]).all():
                
                panel_df=df
                panel_df.drop(0,inplace=True)
                panel_df.reset_index(drop=True,inplace=True)
                break
        
        assert isinstance(panel_df,pd.DataFrame)

        panel_list=[]
        
        for panel in panel_df.itertuples():
            gen,first_name,last_name=self.name_parts(panel.Name)
            panel_list.append(
                Panel(first_name=first_name,
                      last_name=last_name,
                      gender=self.gender(gen),
                      function=panel.Function,
                      nation=panel.Nation)
            )
        return panel_list

class EntriesBuilder:

    @staticmethod
    def strip_col(column):
        return column.str.strip(".").str.strip()

    def from_url(self,url):
        dfs=get_correct_tables(url,extract_links=None)

        entry_df=[]
        for df in dfs :
            if (df.columns[:2] == ['No.', 'Name']).all():
                entry_df=df
                entry_df.columns=self.strip_col(entry_df.columns)
                break
            if (df.iloc[0,:2] == ['No.', 'Name']).all():
                entry_df=df
                entry_df.columns=self.strip_col(entry_df.columns)
                entry_df.drop(0,inplace=True)
                entry_df.reset_index(drop=True,inplace=True)
                break

        assert isinstance(entry_df,pd.DataFrame)

        entry_list=[]
        for entry in entry_df.itertuples():
            entry_list.append(
                Entries(no=entry.No,
                        name=entry.Name,
                        nation= entry.Nation)
            )
        return entry_list
    

@dataclass #Resultsparts
class ResultsParts:
    ranked:pd.DataFrame | None = None
    finalnotreached:pd.DataFrame | None = None
    withdrawn:pd.DataFrame | None= None

    @staticmethod
    def _transform_int(x):
        if pd.isna(pd.to_numeric(x,errors="coerce") ):
            return x
        if isinstance(x,str):
            return pd.to_numeric(x)
        
        if int(x)==x:
            return int(x)
        else :
            return x
        
    def _not_ranked(self,df):
        if (df["Name"] == "Final Not Reached").any():
            index_not_ranked=df[df["Name"]=="Final Not Reached"].index[0]
            
        else:
            index_not_ranked=self.ranked.index[-1]
        notranked_df=df[ df.index > index_not_ranked].reset_index(drop=True)
        if notranked_df.shape[0]==0:
            return None
        return notranked_df
    
    def _fill_place(self,not_ranked_df):
        mask=not_ranked_df["FPl"].isna()
        if mask.sum()>0:
            initnumer=self.ranked["FPl"].iloc[-1]+1
            
            not_ranked_df.loc[mask,"FPl"]=range(initnumer,initnumer+mask.sum())
        return not_ranked_df
    
    def _withdrawn_df(self,df):
        wd_df= df[df["FPl"]=="WD"].map(self._transform_int).map(lambda x: None if x=="WD" else x).reset_index(drop=True)
        if wd_df.shape[0]==0:
            return None
        return wd_df
    
    def _fnr_df(self,df):
        fnr_df=df[df["FPl"]!="WD"].dropna(axis="columns").dropna(ignore_index=True,axis="index").map(self._transform_int).map(lambda x: None if x=="FNR" else x)
        if fnr_df.shape[0]==0:
            return None
        return fnr_df
    
    @staticmethod
    def _columns_droppable(columns):
        return [ col for col in columns if col != "Club"]

    def from_df(self,df:pd.DataFrame):
        if sum(df.columns.isin(["FPl","Name","Nation"])) < 2:
            raise TypeError("Not good type of df : {df.columns}")
        df.rename(columns={"FPl.":"FPl"},errors="ignore",inplace=True)
        
        self.ranked=df.dropna(ignore_index=True,subset=self._columns_droppable(df.columns)).map(self._transform_int)
        
        not_ranked_df= self._not_ranked(df)
        if not isinstance(not_ranked_df,pd.DataFrame):
            return self
        
        not_ranked_df=self._fill_place(not_ranked_df)

        self.finalnotreached=self._fnr_df(not_ranked_df)
        
        self.withdrawn=self._withdrawn_df(not_ranked_df)
        return self


 
@dataclass
class ResultsBuilder:

    result_list:list = field(default_factory=list)

    def listBuilder(self,df,status):
        if not isinstance(df,pd.DataFrame) :
            return self
        
        points_idx=df.columns.get_loc("Points")+1
        for result in df.itertuples():
            segment_list=[]
            for i,segmentPl in enumerate(result[points_idx+1:],start=points_idx):
                if pd.notna(segmentPl):
                    segment_list.append(SegmentPlace(segment=df.columns[i],place=segmentPl))
            self.result_list.append(
                Results(finalplace=result.FPl,
                        name=result.Name,
                        club=getattr(result,"Club",None),
                        nation=result.Nation,
                        points=result.Points,
                        places=segment_list,
                        status=status)

            )
        return self


    def from_url(self,url):
        dfs=get_correct_tables(url,extract_links=None)

        results_df=[]
        for df in dfs :
            if (df.columns[:5].isin(['FPl.', 'Name', 'Club', 'Nation', 'Points'])).any():
                
                results_df=df
                results_df.rename(columns={"FPl.":"FPl","Nat.":"Nation"},inplace=True)
                break
            elif (df.iloc[0][:5].isin(['FPl.', 'Name', 'Club', 'Nation', 'Points'])).any():
                results_df=df
                results_df.columns=results_df.iloc[0]
                results_df.drop(0,inplace=True)
                results_df.reset_index(drop=True,inplace=True)
                results_df.rename(columns={"FPl.":"FPl","Nat.":"Nation"},inplace=True)
                break
        
        assert isinstance(results_df,pd.DataFrame)
        resultsparts=ResultsParts().from_df(results_df)
        
        self.listBuilder(resultsparts.ranked,"RANKED")
        self.listBuilder(resultsparts.finalnotreached,"FINAL NOT REACHED")
        self.listBuilder(resultsparts.withdrawn,"WITHDRAW")

        return self.result_list


@dataclass
class DetailResultsBuilder:
    legend:dict | None= None
    det_results_df:pd.DataFrame | None=None

    @staticmethod
    def clean_columns(columns):
        new_columns=columns.str.strip("+").str.strip("=").str.strip("-").str.strip().str.strip(".")
        return new_columns
    
    @staticmethod
    def negative_value(number):
        if not isinstance(number,float):
            return number
        if number>0:
            return (-number)
        return number
    
    @staticmethod
    def to_numeric(df):
        for col in df.columns:
            try:
                numeric=pd.to_numeric(df[col])
                df[col]=numeric
            except ValueError:
                print("not numeric")
        return df
    
    @staticmethod
    def starting_number(string):
        return int(string[1:])

    def from_url(self,url):

        dfs=get_correct_tables(url,extract_links=None)

        for df in dfs:
            if len(df.columns)>3:
                if (df.columns[:4].isin(['Pl.', 'Name', 'Club', 'Nation'])).any():
                    self.det_results_df=df
                    self.det_results_df.columns=self.clean_columns(df.columns)
                    self.det_results_df=self.to_numeric(self.det_results_df)
                    
                elif (df.iloc[0][:4].isin(['Pl.', 'Name', 'Club', 'Nation'])).any():
                    self.det_results_df=df
                    self.det_results_df.columns=self.clean_columns(df.iloc[0])
                    self.det_results_df.drop(0,inplace=True)
                    self.det_results_df.reset_index(drop=True,inplace=True)
                    self.det_results_df=self.to_numeric(self.det_results_df)
                   
            else :
                if df.iloc[0,0]=="Legend":
                    self.legend=dict(zip(df.iloc[1:,0],df.iloc[1:,1]))
        return self

    def build(self):

        det_res_list=[]
        
        detailed_pcs_columns=self.det_results_df.drop(["Pl","Name","Nation","Club","TSS","TES","PCS","Ded","StN","Qual"],axis="columns",errors="ignore").dropna(axis="columns").columns
        for result in self.det_results_df.itertuples():
            
            PcsParts_list=[]
            for col in detailed_pcs_columns:
                if self.legend.get(col):
                    PcsParts_list.append(
                        PcsParts(
                            name=self.legend.get(col),
                            score=getattr(result,col)
                        )
                    )
            det_res_list.append(
                DetailResults(
                    place=getattr(result,"Pl"),
                    name=getattr(result,"Name"),
                    club=getattr(result,"Club",None),
                    nation=getattr(result,"Nation"),
                    tss=getattr(result,"TSS"),
                    tes=getattr(result,"TES"),
                    pcs=getattr(result,"PCS"),
                    detail_pcs=PcsParts_list,
                    ded= self.negative_value(getattr(result,"Ded")),
                    starting_number=self.starting_number(result.StN)
                    
                )
            )
        return det_res_list


@dataclass 
class CategoryBuilder:
    category_idx:list[Category_idx]
    schedule_idx:dict
    base_url:str

    @classmethod
    def from_main_page_table(cls,mainpagetable:MainPageTables,base_url):
        return cls(
            category_idx=mainpagetable.category_index(),
            schedule_idx=mainpagetable.schedule_index(),
            base_url=base_url
        )
    
    def complete_url(self,url):
        return urljoin(self.base_url,url)
    
    def segments_builder(self,category:Category_idx):
        segment_list=[]
        
        for segment in category.segments:
            schedule_idx=self.schedule_idx[category.category].get(segment.segment) if self.schedule_idx[category.category].get(segment.segment) else self.schedule_idx[category.category].get(segment.detail_class)
            segment_list.append(
                Segment(
                    name=segment.segment,
                    date=schedule_idx["date"],
                    time=schedule_idx["time"],
                    panel=PanelBuilder().from_url(self.complete_url(segment.panel)),
                    detailed_results=DetailResultsBuilder().from_url(self.complete_url(segment.detail_class)).build(),
                    pdf_url=self.complete_url(segment.pdf)
                )
            )
        return segment_list


    def build(self ):
        category_list=[]
        print(self.category_idx)
        print(self.schedule_idx)
        for category in self.category_idx:
            category_list.append(
                Category(
                    name=category.category,
                    entries=EntriesBuilder().from_url(self.complete_url(category.entries)),
                    results=ResultsBuilder().from_url(url=self.complete_url(category.result)),
                    segments=self.segments_builder(category)

                )
            )
        return category_list