from dataclasses import dataclass
@dataclass
class FilenameGenerator:
    
    discipline:str | None=None
    name:str | None=None
    country:str | None =None
    segment:str | None =None
    compet:str | None=None
    div:str | None=None
    date:str | None = None
    cat:str |None =None


    @property
    def filename(self):
        
        
        parts = [self.cat, self.div, self.discipline, self.compet, self.date]
        optional = "_" + "_".join(p for p in parts if p) if any(parts) else ""
        
        info=f"{self.name}_{self.country}_{self.segment}"
        return f"{info}{optional}.json"
        

class FilenameFactory:

    def normalize(self,text: str) -> list[str]:
        return text.lower().replace("-", " ").split()
    
    def discipline_from_team_name(self,team_name: str) -> str | None:
        if not team_name:
            return None

        words = team_name.split()
        if words and words[0] == "Team":
            return "sys"

        return None



    def detect_category(self,words: list[str]) -> str | None:
        if "junior" in words:
            return "junior"
        if "senior" in words:
            return "senior"
        if "adult" in words or "adults" in words:
            return "adult"
        if "novice" in words:
            if "basic" in words:
                return "novice_basic"
            if "advanced" in words:
                return "novice_advanced"
            return "novice"
        if "juvenile" in words:
            if "pre" in words:
                return "pre_juvenile"
            return "juvenile"
        if "mixed" in words and "age" in words:
            return "mixed_age"
        return None
    
    def detect_discipline(self,words: list[str]) -> str | None:
        if "synchronized" in words or "team" in words or "teams" in words:
            return "sys"
        if "dance" in words:
            return "dance"
        if "pairs" in words:
            return "pairs"
        if "women" in words or "ladies" in words:
            return "women"
        if "men" in words:
            return "men"
        
        return None

    def apply_exceptions(self,words, category, discipline):
        text = " ".join(words)

        if "synchronized skating" == text:
            return category or "senior", "sys"

        if text == "ice dance":
            return category or "senior", "dance"

        return category, discipline

    
        
    def comp_name_red(self,name:str):
        if not name:
            return

        
        name=name.lower()
        if name[:3]=="isu":
            name=name[3:].strip()
        
        SPECIAL = {
        "world synchronized skating championships": "wsysc",
        "world junior synchronized skating championships": "wjsysc",
        "world championships": "wc",
        "world junior championships": "wjc",
        }

        if name in SPECIAL:
            return SPECIAL[name]
        
        words = name.split()
        if len(name) < 20 or len(words) < 3:
            return "_".join(words)

        return "".join(word[0] for word in words)

    def find_segment(self,segment):
        match segment:
            case "short program":
                return "SP"
            case "free skating":
                return "FS"
            
            case "rythm dance":
                return "SP"
            case "free dance":
                return "FS"
        return segment.replace(" ","_")
    
    def find_discipline_cat(self,data: dict) -> tuple[str | None, str]:
        raw_cat = data["competition"]["category"]
        team_name = data["results"]["team"]["name"]

        words = self.normalize(raw_cat)

        discipline = self.discipline_from_team_name(team_name)

        if discipline is None:
            discipline = self.detect_discipline(words)

        category = self.detect_category(words)

        category, discipline = self.apply_exceptions(words, category, discipline)

        if discipline is None:
            return None, "_".join(words)

        return category, discipline


    def from_dict(self,jsondict:dict):
        gen=FilenameGenerator()
        gen.name=jsondict["results"]["team"]["name"].lower().replace(" ","_").replace("/","")
        gen.cat,gen.discipline=(self.find_discipline_cat(jsondict))
        gen.country=jsondict["results"]["team"]["country"]
        gen.div=jsondict["competition"].get("division")

        date=jsondict["competition"].get("date")
        if date:
            gen.date=date[:4]
        gen.compet=self.comp_name_red(jsondict["competition"].get("name"))
        gen.segment=self.find_segment(jsondict["competition"]["segment"])
        return gen