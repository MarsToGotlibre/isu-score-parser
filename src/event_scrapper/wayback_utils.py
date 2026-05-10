import re
from urllib.parse import urlsplit,urljoin
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging

logger = logging.getLogger(__name__)

_RE_WAYBACK = re.compile(r'^/web/(\d{14})\w*/(https?://.+)$')

@dataclass
class ExtendedUrl:
    split: object

    original_url:    str
    wayback_ts_raw:  Optional[str]       
    wayback_dt:      Optional[datetime]  
    archived_url:    Optional[str]       

    
    @property
    def scheme(self):   return self.split.scheme
    @property
    def netloc(self):   return self.split.netloc
    @property
    def path(self):     return self.split.path
    @property
    def hostname(self): return self.split.hostname
    @property
    def query(self):    return self.split.query
    @property
    def fragment(self): return self.split.fragment

    def geturl(self):   return self.split.geturl()
    @property
    def is_wayback(self) : return self.hostname=="web.archive.org" or self.hostname=="archive.org"
    
    @property
    def url(self): return self.original_url if not self.archived_url else self.archived_url

@dataclass
class URLResolution:
    relative_url: str                     
    original_url: str                    
    resolved_url: str                     
    is_wayback: bool                      
    wayback_timestamp: Optional[str] = None

class URLResolver:
    def __init__(self,base_url):
        self.base=wayback_urlsplit(base_url)
        self.is_wayback_context=self.base.is_wayback
        self._resolution_history: list[URLResolution] = []
    
    def resolve(self,relative_url:str):
        if not relative_url:
            return
        
        if not self.is_wayback_context:
            return urljoin(self.base.original_url,relative_url)
        
        orginal_base = self.base.archived_url
        target_originel = urljoin(orginal_base,relative_url)

        closest=closest_archive(target_originel)
        if closest:
            self._resolution_history.append(
                URLResolution(
                    relative_url=relative_url,
                    original_url=target_originel,
                    resolved_url=closest,
                    is_wayback=True,
                    wayback_timestamp=wayback_urlsplit(closest).wayback_dt.isoformat()
                    )
                )

        return closest
    
    def export_resolution_map(self):
        if len(self._resolution_history)<1:
            return None
        resolution_map={}

        for resolution in self._resolution_history:
            resolution_map[resolution.relative_url] = {
                "original":resolution.original_url,
                "resolved":resolution.resolved_url,
                "timestamp":resolution.wayback_timestamp
            }
        
        return resolution_map

# this splits the url and regognises if it's a web archive link or not and if the case resolve what the archived url is.
def wayback_urlsplit(url: str) -> ExtendedUrl:
    split = urlsplit(url)

    m = _RE_WAYBACK.match(split.path)
    if m:
        ts_raw      = m.group(1)
        archived    = m.group(2)
        dt          = datetime.strptime(ts_raw, "%Y%m%d%H%M%S")
    else:
        ts_raw = archived = dt = None

    return ExtendedUrl(
        split         = split,
        original_url  = url,
        wayback_ts_raw= ts_raw,
        wayback_dt    = dt,
        archived_url  = archived,
    )


def get_cdx_session():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=7,
        backoff_factor=4,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def list_archive(url):
    import pandas as pd
    url_request=f"http://web.archive.org/cdx/search/cdx?url={url}&output=json&filter=statuscode:200&limit=4&fl=timestamp,original,length"
    session = get_cdx_session()
    try :
        response = session.get(url_request)
        response.raise_for_status()
    except Exception as e :
        logger.warning(f"Failed to found url : {url} on wayback machine cdx api")
        response = None
    if not response:
        return 
    if len(response.json())<2:
        return
    df=pd.DataFrame(response.json()[1:],columns=response.json()[0])
    df.length=pd.to_numeric(df.length)
    L=[]
    for link in df.sort_values(by="length",ascending=False).itertuples():
        L.append(f"https://web.archive.org/web/{link.timestamp}/{link.original}")
    return L


def closest_archive(url):
    cdx_archive = list_archive(url)
    if cdx_archive:
        return cdx_archive[0]
    return None