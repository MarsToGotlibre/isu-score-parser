from datetime import datetime as datetime
import pandas as pd
import requests

def return_iso_date(str_date):
    date=""
    try:
        date=datetime.strptime(str_date.strip(),"%d.%m.%Y").date().isoformat()
    except ValueError:
        try:
            date=datetime.strptime(str_date.strip(),"%d/%m/%Y").date().isoformat()
        except ValueError:
            date=str_date.strip()
                #logging.warning(f""Couldn't put date into iso format, falling back to extracted date.")
    return date

def empty_cell_to_nan(x):
    if not isinstance(x,tuple):
        if x =="":
            return pd.NA

        return x
    else:
        if not x[1] and x[0]=="":
            return pd.NA
        elif not x[1]:
            return x[0]
        else:
            return x
        
def get_correct_tables(url,extract_links="body"):
    try:
        dlt = pd.read_html(url,extract_links=extract_links,flavor="lxml")
    except UnicodeDecodeError:
        response=requests.get(url)
        response.encoding="latin-1"
        import io
        dlt=pd.read_html(io.StringIO(response.text),extract_links=extract_links,flavor="lxml")

    L=[]
    for i,table in enumerate(dlt):
        if table.shape[1]>1 : #and not table.isna().all().any()

            L.append(dlt[i].map(empty_cell_to_nan).dropna(inplace=False,how='all',axis='index',ignore_index=True) )
    
         
    return L