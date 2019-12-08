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

creates a corresponding .csv and .html file.

Terry N. Brown terrynbrown@gmail.gov Sat Nov 16 22:42:43 UTC 2019
"""
import argparse
import csv
import json
import os
import requests
from lxml import etree
from lxml.builder import E

# fields from grab from MatchedObjectDescriptor
TLF = [
    'PositionLocationDisplay',
    'PositionTitle',
    'PublicationStartDate',
    'ApplicationCloseDate',
    'DepartmentName',
    'PositionID',
]

DTF = ['ApplyOnlineUrl', 'LowGrade', 'HighGrade', 'PromotionPotential']


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
    yield ['MatchedObjectId'] + TLF + DTF
    for item in data['SearchResult']['SearchResultItems']:
        yield (
            [item['MatchedObjectId']]
            + [item['MatchedObjectDescriptor'][f] for f in TLF]
            + [
                item['MatchedObjectDescriptor']['UserArea']['Details'][f]
                for f in DTF
            ]
        )


def url(text):
    """<a href='{text}'>link</a> if text starts with http, else text"""
    return (
        E.a("link", href=text, target='_blank')
        if text.startswith('http')
        else text
    )


def main():
    """Fetch data and save JSON or parse JSON to CSV / HTML with --parse flag
    """
    opt = get_options()
    if opt.parse:
        rows = parse_data(opt)
        hdr = next(rows)
        rows = list(rows)
        # save as CSV
        with open(
            opt.filename.replace('.json', '.csv'), 'w', newline=''
        ) as out:
            writer = csv.writer(out)
            writer.writerow(hdr)
            writer.writerows(rows)
        # save as HTML table
        with open(opt.filename.replace('.json', '.html'), 'w') as out:
            table = E.table()
            html = E.html(E.body(table))
            # header row
            table.append(E.tr(*[E.th(i) for i in hdr]))
            start = hdr.index('PublicationStartDate')
            rows.sort(key=lambda x: x[start], reverse=True)
            for row in rows:
                # convert ID number column to link address
                row[0] = "https://www.usajobs.gov/GetJob/ViewDetails/" + row[0]
                table.append(E.tr(*[E.td(url(i)) for i in row]))
            out.write(etree.tostring(html, pretty_print=True).decode('utf-8'))

    else:
        # fetch data to JSON
        with open(opt.filename, 'w') as out:
            json.dump(get_data(opt), out, indent=4)


if __name__ == "__main__":
    main()
