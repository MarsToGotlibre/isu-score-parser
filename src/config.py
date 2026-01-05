from dataclasses import dataclass,field

@dataclass
class TableConfig:
    profile_id:str
    camelot_args:dict[str,dict]
    header_row:dict[str,int]= field(default_factory=dict)
    deduction_table:bool | None =None
    
    @classmethod
    def isu_2005(cls):
        return cls(profile_id="isu_2005",
            camelot_args=
            {"general_info":{"row_tol":30},
            "technical_score":{"layout_kwargs":{'detect_vertical': False}},
            "PCS":{},
            "deductions":{}},
            header_row={
            "general_info":1,
            "technical_score":2,
            "PCS":1},
            deduction_table=True
        )

    @classmethod
    def isu_2007(cls):
        return cls(profile_id="isu_2007",
            camelot_args=
            {"general_info":{"row_tol":30},
            "technical_score":{"row_tol":8},
            "PCS":{},
            "deductions":{"columns":["90,550"]}},
            header_row={
            "general_info":1,
            "technical_score":2,
            "PCS":1}
        )

    @classmethod
    def isu_2014(cls):
        return cls(
            profile_id="isu_2014",
            camelot_args=
            {"general_info":{"row_tol":20},
            "technical_score":{"row_tol":8},
            "PCS":{},
            "deductions":{"columns":["90,550"]}},
            header_row={
            "general_info":1,
            "technical_score":2,
            "PCS":1}
            )
    @classmethod
    def isu_2018(cls):
        return cls(
            profile_id="isu_2018",
            camelot_args=
            {"general_info":{"row_tol":30},
            "technical_score":{"row_tol":8},
            "PCS":{},
            "deductions":{"columns":["97,528"]}},
            header_row={
            "general_info":1,
            "technical_score":2,
            "PCS":1})
    
    @classmethod
    def isu_2022(cls):
        return cls(
            profile_id="isu_2022",
            camelot_args=
            {"general_info":{"row_tol":20},
            "technical_score":{"row_tol":8},
            "PCS":{},
            "deductions":{"columns":["90,550"]}})
    @classmethod
    def find_era(cls,patern):
        match patern:
            case 2005:
                return cls.isu_2005()
            case 2007:
                return cls.isu_2007()
            case 2014:
                return cls.isu_2014()
            case 2018:
                return cls.isu_2018()
            case 2022:
                return cls.isu_2022()