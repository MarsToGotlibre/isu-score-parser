from datetime import datetime as datetime
import pandas as pd
import requests
import logging
from requests import HTTPError
from functools import wraps
from typing import Callable
from src.event_scrapper.wayback_utils import closest_archive

logger=logging.getLogger(__name__)

def return_iso_date(str_date):
    date=""
    try:
        date=datetime.strptime(str_date.strip(),"%d.%m.%Y").date()
    except ValueError:
        try:
            date=datetime.strptime(str_date.strip(),"%d/%m/%Y").date()
        except ValueError:
            date=str_date.strip()
            logger.warning(f"Couldn't put date into iso format, falling back to raw extracted date.")
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
        

def safe_fetch_html(url: str) -> str:
    
    assert isinstance(url,str)
    resp = requests.get( url, timeout=10,headers={"User-Agent": "Chrome/92.0.4515.159 Safari/537.36"} )
    resp.raise_for_status()

    logger.info(f"Fetched url : {url}")
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
    from io import StringIO

    try:
        dfs = pd.read_html( StringIO(html), extract_links=extract_links, flavor="lxml" )
    except ValueError:
        return []

    cleaned = []
    for df in dfs:
        if df.shape[1] <= 1:
            continue

        df = df.map(empty_cell_to_nan).dropna(how="all", axis=0).reset_index(drop=True)
        cleaned.append(df)

    return cleaned

        
def get_correct_tables(source,extract_links="body"):
    if source.strip().lower().startswith("http"):
        html=safe_fetch_html(source)
    else:
        html = source
    tables=extract_tables_from_html(html=html,extract_links=extract_links)

    if not tables:
        logger.warning(f"No tables found")
    
    return tables



def optional_build(label: str):

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPError as e:
                logger.warning(f"[{label}] 404 — skipping: {e.url}")
                return None

            except AssertionError as e:
                logger.warning(f"[{label}] Unexpected page structure — skipping: {e}")
                return None
            except Exception as e:
                logger.error(f"[{label}] Unexpected error — skipping: {e}", exc_info=True)
                return None
        return wrapper
    return decorator