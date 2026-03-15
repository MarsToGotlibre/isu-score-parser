from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup
import re

from src.event_scrapper.layout_extractor import OldDisplayExtractor,TableDisplayExtractor

import logging
logger=logging.getLogger(__name__)

class LayoutType(Enum):
    OLD_DISPLAY = "old_display"
    TABLE_DISPLAY = "table_display"
    UNKNOWN = "unknown"

class HTMLLayout:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self.layout_type: LayoutType = LayoutType.UNKNOWN
        self.main_div: Optional[BeautifulSoup] = None
    
    @classmethod
    def from_html(cls,html):
        return cls(soup=BeautifulSoup(html,"lxml"))
    
    def detect(self) -> LayoutType:
        if not self.soup.body:
            logger.warning("No <body> found in HTML")
            return LayoutType.UNKNOWN
        
        main_divs = []
        table_sur = []
        
        for tag in self.soup.body.children:
            if not tag.name:
                continue
            
            #old event pages in classic html
            if tag.name == "div":
                #web.archive search captures div
                if tag.get("id") and re.match(r"wm-ipp",tag.get("id")):
                    continue
                else:
                    main_divs.append(tag)
            #classic ISU table display
            elif tag.name == "table":
                if tag.get("class") and "MainTab" in tag.get("class"):
                    table_sur.append(tag)
        
        if len(table_sur) == 1:
            self.layout_type = LayoutType.TABLE_DISPLAY
            logger.info("Layout detected: TABLE_DISPLAY")
            return self.layout_type
        
        if len(main_divs) == 1 and self._verify_main_div(main_divs[0]):
            self.layout_type = LayoutType.OLD_DISPLAY
            self.main_div = main_divs[0]
            logger.info("Layout detected: OLD_DISPLAY")
            return self.layout_type
        
        logger.warning("Could not detect layout type")
        return LayoutType.UNKNOWN
    
    @staticmethod
    def _verify_main_div(div: BeautifulSoup) -> bool:
        h2_list = div.find_all("h2")
        h3_list = div.find_all("h3")
        return len(h2_list) >= 1 and len(h3_list) >= 2
    
    def get_extractor(self):
        if self.layout_type == LayoutType.OLD_DISPLAY:
            return OldDisplayExtractor(self.main_div)
        elif self.layout_type ==LayoutType.TABLE_DISPLAY:
            return TableDisplayExtractor(self.soup)
        else :
            return None
