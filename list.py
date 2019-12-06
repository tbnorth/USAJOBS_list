"""
list.py - List USAJOBS positions in .csv for easy review of new postings.

Fairly trivial.

 - set env. var. YOUR_EMAIL to your email
 - set env. var. AUTH_KEY to an auth. key you get here:
   https://developer.usajobs.gov/APIRequest/Index
 - Department / Agency codes are here (no auth. needed):
   https://data.usajobs.gov/api/codelist/agencysubelements
   save and peruse that file for codes, ';' separated EPA codes used below
 - would need to handle pagination for more than 500 results

Usage:

  python list.py 20191115.json

gets current results, then

  python list.py --parse 20191115.json

creates a corresponding .csv file.

Terry N. Brown terrynbrown@gmail.gov Sat Nov 16 22:42:43 UTC 2019
"""
import argparse
import csv
import json
import os
import requests

# fields from grab from MatchedObjectDescriptor
TLF = [
    'PositionLocationDisplay',
    'PositionTitle',
    'PublicationStartDate',
    'ApplicationCloseDate',
    'DepartmentName',
    'PositionID',
]


def make_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="""Get a list of jobs from USAJOBS.com""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--parse",
        action='store_true',
        help="Convert .json file to .csv, extracting target fields.",
    )
    parser.add_argument('filename', help="Fetch jobs and store in .json file.")
    return parser


def get_options(args=None):
    """
    get_options - use argparse to parse args, and return a
    argparse.Namespace, possibly with some changes / expansions /
    validations.

    Client code should call this method with args as per sys.argv[1:],
    rather than calling make_parser() directly.

    Args:
        args ([str]): arguments to parse

    Returns:
        argparse.Namespace: options with modifications / validations
    """
    opt = make_parser().parse_args(args)

    # modifications / validations go here

    return opt


def get_data(opt):
    """
    get_data - Return dict of fetched job data.

    Args:
        opt (argparse.Namespace): command line options
    Returns:
        dict: data from USAJOBS.gov
    """
    url = (
        "https://data.usajobs.gov/api/Search?"
        "ResultsPerPage=500&Organization=EP00;EPJF;EPR1&WhoMayApply=All"
    )
    request = requests.get(
        url,
        headers={
            'Host': 'data.usajobs.gov',
            'User-Agent': os.environ['YOUR_EMAIL'],
            'Authorization-Key': os.environ['AUTH_KEY'],
        },
    )
    return request.json()


def parse_data(opt):
    """
    parse_data - Return list of lists, tabular data extracted from JSON input

    Args:
        opt (argparse.Namespace): command line options
    Returns:
        list: rows of extracted data
    """
    data = json.load(open(opt.filename))
    # first yield field names
    yield ['MatchedObjectId'] + TLF + ['ApplyOnlineUrl']
    for item in data['SearchResult']['SearchResultItems']:
        yield (
            [item['MatchedObjectId']]
            + [item['MatchedObjectDescriptor'][f] for f in TLF]
            + [
                item['MatchedObjectDescriptor']['UserArea']['Details'][
                    'ApplyOnlineUrl'
                ]
            ]
        )


def main():
    opt = get_options()
    if opt.parse:
        with open(
            opt.filename.replace('.json', '.csv'), 'w', newline=''
        ) as out:
            writer = csv.writer(out)
            writer.writerows(parse_data(opt))
    else:
        with open(opt.filename, 'w') as out:
            json.dump(get_data(opt), out, indent=4)


if __name__ == "__main__":
    main()
