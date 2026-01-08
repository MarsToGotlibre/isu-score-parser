# isu-score-parser

A tool to extract score tables from synchro skating score PDFs using python.
The extracted tables are stored into json files, and can be completed with adding a yaml file to the parser. This parser also support other artistic disciplines.

**Features**:

- Retrocompatible (Up to 2005)
- Multiple discipline support
  - base value bonus support
- Deduction votes support
- No call support

> [!INFO]
> This parser aims mostly to parse synchro skating PDFs. The maintenance will mostly be done for this discipline. Most other disciplines PDF can be parsed correctly but I can't garantee today it will work for every PDF if they are too far away from the expected structure.

## Installation

Requires :

- Python 3.10+
- Python dependencies :

  - pandas (2.3.3)
  - camelot-py (1.0.9)
  - pdfplumber (0.11.9)
  - PyYaml (6.0.3)

```sh
pip install pandas "camelot-py[base]" pdfplumber pyyaml
```

## Usage

Use the following options to parse your pdf:

 | Options | Required | Descriptions |
 | --- | --- | --- |
 | `-p`, `--pdf` | yes | PDF file path |
 | `-y`, `--yaml` | no | YAML file path to complete the competition info |
 | `-b`, `--begin` | yes | First page to parse |
 | `-e`, `--end` | no | Last page to parse. If not specified only the first page entered will be parsed |
 | `-o`, `--output` | no | Output directory. If it doesnt exists it will be created, if not specified a generical output directory will be created to put the jsons generated. |

Usage :

```sh
python3 main.py [OPTIONS]
```

### Add info to the jsons generated

With the a YAML file following this patern:

```yaml
schema_version: 1
competition:
  name: ISU World Synchronized Skating Championships
  location:
    country: SWE
    city: Stockholm
  date: 2018-04-06
season: 2017-2018
source_url: example.org
```

None of the entries (except `shema_version`) or required when parsing. You can remove some of them if data is missing.

## Futur Objectvies

- Scrape competition info from page events.
- Possibility to parse multiple pdfs at a time.
