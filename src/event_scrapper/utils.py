from datetime import datetime as datetime
import pandas as pd
import requests
import re
import logging

logger=logging.getLogger(__name__)

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

def found_timezone_date(soup,dic):
    date = re.compile(r"(\d{2}\.\d{2}\.\d{4}) - (\d{2}\.\d{2}\.\d{4})")
    for td in soup.find_all("td"):
        d= date.match(td.text.strip())
        if d :
            assert len(d.groups())==2
            dic["start_date"] = return_iso_date(d.groups()[0])
            dic["end_date"] = return_iso_date(d.groups()[1])
            continue
        if "Local Time" in td.text:
            timezone=td.text.strip("()").split(",")
            if len(timezone)>1:
                dic["timezone"] = timezone[1].strip()
            return

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
        

def safe_fetch_html(url: str) -> str:
    resp = requests.get( url, timeout=10 )
    resp.raise_for_status()

    try:
        return resp.text
    except UnicodeDecodeError:
        pass

    resp.encoding = resp.apparent_encoding
    try:
        return resp.text
    except UnicodeDecodeError:
        pass

    resp.encoding = "latin-1"
    return resp.text

def extract_tables_from_html(html: str, extract_links="body") -> list[pd.DataFrame]:
    import io

    try:
        dfs = pd.read_html( io.StringIO(html), extract_links=extract_links, flavor="lxml" )
    except ValueError:
        return []

    cleaned = []
    for df in dfs:
        if df.shape[1] <= 1:
            continue

        df = df.map(empty_cell_to_nan).dropna(how="all", axis=0).reset_index(drop=True)
        cleaned.append(df)

    return cleaned

        
def get_correct_tables(url,extract_links="body"):
    html=safe_fetch_html(url)
    tables=extract_tables_from_html(html=html,extract_links=extract_links)

    if not tables:
        logger.warning(f"No tables found at :{url}")
    
    return tables