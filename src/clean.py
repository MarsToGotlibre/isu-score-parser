import pandas as pd
from src.config import TableConfig
import logging
import pdfplumber
from src.pdf import PageMask,TableExtractor

logger = logging.getLogger(__name__)

class TableData:
    def __init__(self, tables: dict[str, pd.DataFrame]):
        self.tables = tables

    def __getitem__(self, key):
        return self.tables[key]

    def strip_df(self):
        for key in self.tables.keys():
            self.tables[key]=self.tables[key].map(lambda x:x.strip() if isinstance(x,str) else x)
        return self
    
    def clean_titles(self):
        self.tables["general_info"].iloc[0]=self.tables["general_info"].iloc[0].str.replace("+","")
        self.tables["general_info"].iloc[0]=self.tables["general_info"].iloc[0].str.replace("=","")
        self.tables["general_info"].iloc[0]=self.tables["general_info"].iloc[0].str.replace("-","")

        for keys in self.tables.keys():
            self.tables[keys].iloc[0]=self.tables[keys].iloc[0].str.replace(" \n"," ")
            self.tables[keys].iloc[0]=self.tables[keys].iloc[0].str.replace("\n"," ")
            self.tables[keys].iloc[0]=self.tables[keys].iloc[0].str.replace("  "," ")
            

        return self

    def insert_nan_values(self):
        for keys in self.tables.keys():
            self.tables[keys]=self.tables[keys].replace("",pd.NA)
        self.tables["technical_score"]=self.tables["technical_score"].replace("-",pd.NA)
        return self
    
    def set_column_name(self, key="PCS"):
        PCS_columns=self.tables[key].shape[1]
        #print(f"The number of juges is {PCS_columns-3} ")
        header=[f"J{i}" for i in range(1,PCS_columns-2)]+['Scores of Panel']
        self.tables[key].iloc[0,2:]=header
        return self
    
    def set_row_value(self,key,rowidx,column,value):
        self.tables[key].iloc[rowidx,column]=value
        return self
    
    def merge_rows(self,config:TableConfig):
        for key in config.header_row.keys():
            if config.camelot_args[key]==1:
                continue
            else:
                head=self.tables[key].iloc[0]
                for i in range(1,config.header_row[key]):
                    head+=" "+self.tables[key].iloc[i]
                self.tables[key].drop([i for i in range(1,config.header_row[key])],inplace=True)
                self.tables[key].reset_index(drop=True,inplace=True)
        return self
                
    def judge_cols(self,key):
        df=self.tables[key]
        judge_cols_list = [
            col for col in df.columns
            if (
                df.iloc[0, col] == "" or  df.iloc[0, col]==" "
                or "Judges Panel" in str(df.iloc[0, col])
            )
            and pd.to_numeric(df.iloc[1:, col], errors="coerce").notna().any()
        ]
        return judge_cols_list
    
    def fill_juges(self,key):
        judge_cols_list=self.judge_cols(key)
        if len(judge_cols_list)>0:
            self.tables[key].iloc[0,judge_cols_list]=[f"J{i}" for i in range(1,len(judge_cols_list)+1)]
        return self
    


    
    def set_headers(self,key):
        if self.tables[key].columns[0]==0:
            new_columns = self.tables[key].iloc[0]
            self.tables[key].drop(self.tables[key].index[0], inplace=True)
            self.tables[key].columns = new_columns
            self.tables[key].reset_index(drop=True, inplace=True)
        return self

    
    def separate_last_line(self,key,drop=True):
        
        last_df=self.tables[key].iloc[[-1]].dropna(axis=1).reset_index(drop=True)
        if drop:
            self.tables[key].drop(self.tables[key].index[-1],inplace=True)
        return last_df
    
    def total_pcs(self,key="PCS",drop=True):
        total_df=pd.DataFrame({self.tables[key]["Program Components"].iloc[-1]:[self.tables[key]["Scores of Panel"].iloc[-1]]})
        if drop:
            self.tables[key].drop(self.tables[key].index[-1],inplace=True)
        return total_df
    
    def display_tables(self,):
        #from IPython.display import display
        for keys in self.tables.keys():
            #display(self.tables[keys])
            pass
            
    
    def change_column(self,key,before,after):
        temp=self.tables[key].columns
        temp=temp.str.replace(before,after)
        self.tables[key].columns=temp
        return self
    
    def bv_bonus_handle(self,key="technical_score"):
        df=self.tables[key]
        bv_idx = df.columns.get_loc("Base_Value")

        mask_inline_x = (
        df.iloc[:,bv_idx].str.contains(r"\nx", na=False)
        )

        is_bonus_line=df.iloc[:,bv_idx+1].astype(str).str.fullmatch(r"x", case=False, na=False)
        if not mask_inline_x.any() and not is_bonus_line.any():
            return self
        elif mask_inline_x.any() and not is_bonus_line.any():
            df["BV_Bonus"]=mask_inline_x
            df.loc[mask_inline_x,"Base_Value"]=df.loc[mask_inline_x,"Base_Value"].str.replace(r"\nx", "", regex=True).str.strip()
            return self
        else:
            df.columns=["BV_Bonus" if i==bv_idx+1 else col for i,col in enumerate(df.columns)]
            df["BV_Bonus"]=is_bonus_line
            return self
    
    def df_to_numeric(self,key):
        df=self.tables[key]
        for col in df.columns:
            try:
                numeric=df[col].apply(lambda x: pd.to_numeric(x) if pd.notna(x) else x)
                df[col]=numeric
            except ValueError:
                logger.debug(f"{col} not a number")
        return self
    
    def tables_to_numeric(self):
        for key in self.tables.keys():
            self.df_to_numeric(key)
        return self
    
    def ded_string(self):
        
        if self.tables["deduction"].shape[1]<4:
            return self.tables["deduction"][1].iloc[0]
        
        ded=self.tables["deduction"]
        parts = []

        for i in range(1, ded.shape[1], 2):
            if i + 1 >= ded.shape[1]:
                break

            label_col = i
            value_col = i + 1

            mask = ded[value_col].notna() & (pd.to_numeric(ded[value_col]) != 0)

            for label, value in ded.loc[mask, [label_col, value_col]].itertuples(index=False):
                parts.append(f"{label} {value}")
        result=" ".join(parts).strip()
        if len(result)>0:
            return result
        else:
            return pd.NA

    def general_deduction(self,config:TableConfig):
        if not config or self.tables["deduction"].shape[1]<4:
            return self
        
        old_ded=self.tables["deduction"]
        ded_str=self.ded_string()
        ded_df=pd.DataFrame({0:[old_ded[0].iloc[0]],1:[ded_str],2:[old_ded[old_ded.columns[-1]].iloc[1]]})
        
        self.tables["deduction"]=ded_df
        return self

    def clean(self,config:TableConfig):
        self.merge_rows(config)
        
        self.clean_titles()
        self.strip_df()

        self.set_row_value("technical_score",0,0,"Order")
        self.set_row_value("PCS",0,-1,"Scores of Panel")
        self.fill_juges("PCS")
        self.fill_juges("technical_score")


        self.insert_nan_values()
        

        self.set_headers("PCS")
        self.set_headers("general_info")
        self.set_headers("technical_score")


        self.tables["technical_resume"] = self.separate_last_line("technical_score")
        self.tables["PCS_resume"] = self.total_pcs("PCS")

        self.change_column("PCS"," ","_")
        self.change_column("technical_score",".","")
        self.change_column("technical_score"," ","_")

        self.bv_bonus_handle()
        self.general_deduction(config=config)

        self.tables_to_numeric()
        return self
    

class ScoreDocument:
    def __init__(self,filename,page_mask:PageMask,extractor:TableExtractor,config:TableConfig):
        self.filename=filename
        self.page_mask=page_mask
        self.extractor=extractor
        self.config=config
    
    @classmethod
    def fromFile(cls,filename,page=1,auto_config=True):
        with pdfplumber.open(filename) as pdf:
            page = pdf.pages[page-1]
            page_mask=PageMask.from_pdf(page)
        if auto_config==True:
            config=page_mask.config
        else:
            config=auto_config
        return cls(filename,page_mask,TableExtractor(filename,page_mask.width),config)
    
    def tableData(self,table_idx=0,page=1,config_custom=False):
        if not config_custom:
            config_custom=self.config
        if table_idx>(self.page_mask.number_of_tables-1):
            raise IndexError(f"Index out of range: index from 0 to {self.page_mask.number_of_tables-1}, you entered {table_idx}")
        tables=self.extractor.extract(self.page_mask.tables[table_idx],page=page,config=config_custom)
        if tables:
            return TableData(tables)
        return
    
    def clean_tableData(self,config_custom=False,table_idx=0,page=1):
        table= self.tableData(table_idx,page)
        if not table:
            return
        
        if not config_custom:
            try:
                return table.clean(self.config)
            except:
                logger.warning("Clean: Unable to clean the data with default config")
                return table
        else:
            try:
                return table.clean(config_custom)
            except:
                logger.warning("Clean: Unable to the data with custom config")