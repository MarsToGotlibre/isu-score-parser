from src.utils.filename import FilenameGenerator


class EventscrapperFilenameFactory:
    @staticmethod
    def clean_competition_name(name:str):
        name=name.lower().strip()
        if name[:3]=="isu":
            name=name[3:]
        if name[-4:].isnumeric():
            name=name[:-4].strip()
        return name


    def from_event(self,event):
        generator=FilenameGenerator()
        generator.begindate=event.start_date
        generator.compet=self.clean_competition_name(event.event_name)

        return generator
    
    def from_json(self,event_json):
        generator=FilenameGenerator()

        generator.add_begindate(event_json.get("start_date"))
        generator.compet=self.clean_competition_name(event_json.get("name"))

        return generator