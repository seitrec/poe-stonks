import requests
import argparse
import time
from bs4 import BeautifulSoup
import json
from datadog import initialize, statsd
from ninja_datadog import *
from collections import defaultdict

_TIMESERIES_DICT_TEMPLATE = {
    "viz": "timeseries",
    "requests": [
        {
            "style": {
                "palette": "dog_classic",
                "type": "solid",
                "width": "normal"
            },
            "type": "line",
            "formulas": [],
            "queries": [],
            "response_format": "timeseries"
        }
    ]
}

_FORMULA_TEMPLATE = {
        "formula": "(56 * (4 * query5 + query6 + query7 + query8 + query9 + query10 / 4 + query11 / 4 + query12 / 4 + query13 / 4) - (query1 + query2 + query3 + query4) * 14) / 56"
    }

_QUERY_TEMPLATE = "avg:%s{%s}"


def parse_csv_table():
    with open("downloaded_table.csv", 'r') as file:
        strat_name = str(file.readline().split(",")[1]).replace("\n", "")
        run_count = int(file.readline().split(",")[1])
        file.readline() # ignore the titles line
        spend_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        ret_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for line in file:
            econ_type, name, tags, value, spend, ret = line.split(",")[0:6]
            tags = tags.replace(";", ",")
            value = float(value)
            spend = int(spend)
            ret = int(ret)
            print_if_debug(econ_type, name, tags, value, spend, ret)
            if spend != 0:
                spend_data[econ_type][name][tags] = spend
            if ret != 0:
                ret_data[econ_type][name][tags] = ret
    return strat_name, run_count, spend_data, ret_data

def join_name_and_clean_tags(tags, econ_name):
    subtags = "type:"+ econ_name
    if tags != "":
        subtags += "," + tags
    return subtags.replace(" ", "_").replace("<", "_").replace("+", "").replace("'", "_").lower()

def get_queries(spend_data, ret_data):
    query_count = 1
    spend_queries = []
    for econ_type, econ_data in spend_data.items():
        for name, name_data in econ_data.items():
            for tags, spend in name_data.items():
                spend_queries += [(spend, {
                    "name": "query" + str(query_count),
                    "data_source": "metrics",
                    "query": _QUERY_TEMPLATE % (METRIC_POESTACK_ECON_BEST_EFFORT % econ_type, join_name_and_clean_tags(tags, name))
                })]
                query_count += 1
    ret_queries = []
    for econ_type, econ_data in ret_data.items():
        for name, name_data in econ_data.items():
            for tags, ret in name_data.items():
                ret_queries += [(ret, {
                    "name": "query" + str(query_count),
                    "data_source": "metrics",
                    "query": _QUERY_TEMPLATE % (METRIC_POESTACK_ECON_BEST_EFFORT % econ_type, join_name_and_clean_tags(tags, name))
                })]
                query_count += 1
    return spend_queries, ret_queries

def build_formulae(run_count, spend_queries, ret_queries):
    formula = ""
    for query_tuple in ret_queries:
        formula += "+%d*%s" % (query_tuple[0], query_tuple[1]["name"])
    for query_tuple in spend_queries:
        formula += "-%d*%s" % (query_tuple[0], query_tuple[1]["name"])
    print_if_debug(formula)
    return [{"formula": "(%s)/%d" % (formula, run_count)}]

def build_total_returl_tile_json(strat_name, spend_queries, ret_queries, formulae):
    tile = _TIMESERIES_DICT_TEMPLATE.copy()
    tile["requests"][0]["formulas"] += formulae
    tile["requests"][0]["queries"] += [tup[1] for tup in spend_queries]
    tile["requests"][0]["queries"] += [tup[1] for tup in ret_queries]
    with open("%s.json" % strat_name, 'w') as file:
        file.write(json.dumps(tile, indent=4))

if __name__ == "__main__":
    options = {
        'statsd_host':'127.0.0.1',
        'statsd_port':8125
    }

    initialize(**options)
    parser = argparse.ArgumentParser(description='Build Jsons')
    parser.add_argument('-d', '--debug', type=bool, default=False)
    args = parser.parse_args()
    if args.debug:
        DEBUG_FLAG = True
    strat_name, run_count, spend_data, ret_data = parse_csv_table()

    spend_queries, ret_queries = get_queries(spend_data, ret_data)
    formulae = build_formulae(run_count, spend_queries, ret_queries)
    tile = build_total_returl_tile_json(strat_name, spend_queries, ret_queries, formulae)




