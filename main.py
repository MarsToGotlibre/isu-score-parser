import argparse
import logging
from pathlib import Path 
import os

from src.parser import parser

logger = logging.getLogger(__name__)

def init_logging(level: str="INFO")-> logging.Logger:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="[%(levelname)s] %(name)s - %(message)s"
    )

def build_parser():
    parser = argparse.ArgumentParser(description="Score PDF to JSONS")
    parser.add_argument('-p', '--pdf',type=str, help="PDF File path",required=True)
    parser.add_argument("-y","--yaml",type=str,help="YAML file path",default=None)
    parser.add_argument("-b","--begin",type=int,help="First page parsed",required=True)
    parser.add_argument("-e","--end",type=int,help="Last page parsed")
    parser.add_argument("-o","--output",type=str,help="Output directory")

    return parser

def check_extention(path,allowed_ext):
    logger.debug(f"{path.suffix.lower()}")
    if path.suffix.lower() != allowed_ext:
        raise ValueError(f"Invalid file type: {path.suffix}. Expected one of: {allowed_ext}")

def check_file_exists(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    
def verify_structure():
    cwd = Path(__file__).parent
    if not Path(cwd,"Data").exists():
        logger.info("Data folder not found.")
        os.mkdir(Path(cwd,"Data"))
        logger.info(f"Data Folder Created at {Path(cwd,"Data")}")
    if not Path(cwd,"PDF").exists():
        logger.info("PDF folder not found.")
        os.mkdir(Path(cwd,"PDF"))
        logger.info(f"PDF Folder Created at {Path(cwd,"YAML")}")
    if not Path(cwd,"YAML").exists():
        logger.info("YAML folder not found.")
        os.mkdir(Path(cwd,"YAML"))
        logger.info(f"YAML Folder Created at {Path(cwd,"YAML")}")

def directory_output(path:Path):
    cwd = Path(__file__).parent.resolve()
    if not path:
        return
    if path.exists():
        return path.absolute()
    else:
        os.mkdir(Path(cwd,"Data",path).absolute())
        return Path(cwd,"Data",path).absolute()

def pipeline_init(args):
    verify_structure()
    pdf=Path(args.pdf)
    check_file_exists(pdf)
    check_extention(pdf,".pdf")
    print(pdf.absolute())
    if args.yaml:
        yaml=Path(args.yaml)
        check_file_exists(yaml)
        check_extention(yaml,".yaml")
    else:
        yaml=None
    path=directory_output(args.output)

    end=args.end if args.end else args.begin
    print(f"filename={pdf.absolute()}, beginpage={args.begin}, endpage={end}, yaml_file={yaml}, dir={path}")
    print(type(pdf.name))
    parser(filename=pdf.absolute(), beginpage=args.begin, endpage=end, yaml_file=yaml, dir=path)


    

        


if __name__ == "__main__":
    init_logging()
    term_parser=build_parser()
    arg= term_parser.parse_args()
    print(arg)
    pipeline_init(arg)