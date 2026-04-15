import argparse
import logging
from pathlib import Path 
import os


logger = logging.getLogger(__name__)

def init_logging(level: str="INFO")-> logging.Logger:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="[%(levelname)s] %(name)s - %(message)s"
    )

def build_parser():
    parser = argparse.ArgumentParser(description="Score PDF to JSONS")
    subparser= parser.add_subparsers(dest="module", required=True)

    pdf_parser=subparser.add_parser("pdf", help="Extract the PDF score for each teams into a JSON")
    pdf_subparser=pdf_parser.add_subparsers(dest="action",required=True)

    pdf_manual=pdf_subparser.add_parser("manual",help="Manual PDF extraction")
    
    pdf_manual.add_argument('-p', '--pdf',type=str, help="PDF File path",required=True)
    pdf_manual.add_argument("-y","--yaml",type=str,help="YAML file path",default=None)
    pdf_manual.add_argument("-b","--begin",type=int,help="First page parsed",required=True)
    pdf_manual.add_argument("-e","--end",type=int,help="Last page parsed")
    pdf_manual.add_argument("-o","--output",type=str,help="Output directory")

    pdf_auto=pdf_subparser.add_parser("auto",help="Auto detects the PDFs in a folder in and extract them")
    pdf_auto.add_argument("event_folder")

    pdf_verify=pdf_subparser.add_parser("verify",help="Generates a page to view the pdf next to its extracted data")
    pdf_verify.add_argument('-p', '--pdf',type=str, help="PDF File path",required=True)
    pdf_verify.add_argument("-d","--data",type=str,help="Extracted data directory", required=True)
    pdf_verify.add_argument("--port",type=int,help="Port of the server",default=5000)

    event_parser= subparser.add_parser("event", help="Extract the event data from event page")
    event_subparser=event_parser.add_subparsers(dest="action",required=True)

    event_scrape_parser= event_subparser.add_parser("scrape",help="Scrape the web page")
    event_scrape_parser.add_argument("page_event")
    event_scrape_parser.add_argument("-d","--download-pdf",action="store_true", help= "Dowload the scores PDF found during the scrapping")
    event_scrape_parser.add_argument("-o","--output-dir",help="output directory", default=None)


    event_dl_pdf = event_subparser.add_parser("dl", help= "Download the pdf scraped in the event JSON")
    event_dl_pdf.add_argument("event_json")
    event_dl_pdf.add_argument("-o","--output-dir",help="output directory", default=None)

    event_fullpipeline =event_subparser.add_parser("fullpipeline", help="Generates event json, downloads pdf, extract the scores from pdfs.")
    event_fullpipeline.add_argument("page_event_url")

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
    """ if not Path(cwd,"PDF").exists():
        logger.info("PDF folder not found.")
        os.mkdir(Path(cwd,"PDF"))
        logger.info(f"PDF Folder Created at {Path(cwd,"YAML")}")
    if not Path(cwd,"YAML").exists():
        logger.info("YAML folder not found.")
        os.mkdir(Path(cwd,"YAML"))
        logger.info(f"YAML Folder Created at {Path(cwd,"YAML")}") """

def directory_output(path:Path):
    cwd = Path(__file__).parent.resolve()
    if not path:
        return
    if path.exists():
        return path.absolute()
    else:
        os.mkdir(Path(cwd,"Data",path).absolute())
        return Path(cwd,"Data",path).absolute()

def pdf_manual_pipeline_init(args):
    from src.pdf_parser.parser import parser

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
    #print(f"filename={pdf.absolute()}, beginpage={args.begin}, endpage={end}, yaml_file={yaml}, dir={path}")
    #print(type(pdf.name))
    parser(filename=pdf.absolute(), beginpage=args.begin, endpage=end, yaml_file=yaml, dir=path)


def event_pipeline(args):

    match args.action :
        case "scrape":
            output=directory_output(args.output_dir)
            from src.event_scrapper.export import init_finc
            init_finc(args.page_event,dl_pdf=args.download_pdf,output=output)
        case "dl":
            path=Path(args.event_json).resolve()
            check_extention(path,".json")
            check_file_exists(path)

            with open(path) as f:
                import json
                d=json.load(f)
            
            output= directory_output(args.output_dir) or path.parent

            from src.event_scrapper.export import download_pdf
            download_pdf(d,output)
        case "fullpipeline":
            from src.pipeline_web_pdf.pipeline import Event_pdf_pipeline
            pipeline=Event_pdf_pipeline(url=args.page_event_url)
            pipeline.build_web_pipeline()

            pipeline.run()


def pdf_pipeline(args):
    verify_structure()
    match args.action:
        case "manual":
            pdf_manual_pipeline_init(args)
        case "auto":
            from src.pipeline_web_pdf.pipeline import Event_pdf_pipeline
            pipeline=Event_pdf_pipeline(relative_dir=Path(args.event_folder).resolve())
            pipeline.build_from_folder()
            pipeline.run()
        case "verify":
            pdf_file=Path(args.pdf).resolve()
            folder=Path(args.data).resolve()
            check_file_exists(pdf_file)
            check_extention(pdf_file,".pdf")

            from src.web_viz.app import run_server

            run_server(event_dir=folder,pdf_path=pdf_file,port=args.port)


def pipeline(args):
    verify_structure()
    match args.module:
        case "pdf":
            pdf_pipeline(args)
        case "event":
            event_pipeline(args)


        


if __name__ == "__main__":
    init_logging()
    term_parser=build_parser()
    arg= term_parser.parse_args()
    print(arg)
    print(arg.module)
    pipeline(arg)