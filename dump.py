import requests
import argparse
import time
from bs4 import BeautifulSoup
import json
from datadog import initialize, statsd
from constants import *
from handlers import *
from query_builder import *

_DEBUG_FLAG = False

if __name__ == "__main__":
    initialize(**Config.datadog_options)
    parser = argparse.ArgumentParser(description='Crawl ninja market')
    parser.add_argument('-t', '--type', type=str, default="")
    parser.add_argument('-d', '--debug', type=bool, default=False)
    args = parser.parse_args()

    if args.debug:
        _DEBUG_FLAG = True
        
    store = Economy_Store(Config, [t.replace("_", " ") for t in args.type.split(",")] if args.type != "" else [])
    store.dump()

