class ScrapperError(Exception):
    pass

class NoValidLink(ScrapperError):
    def __init__(self, *args):
        super().__init__(f"No valid link for this page")