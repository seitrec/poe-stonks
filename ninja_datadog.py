import requests
import argparse
import time
from bs4 import BeautifulSoup
import json
from datadog import initialize, statsd
from constants import *
from handlers import *
from query_builder import *


    



_LISTING_CONFIDENCE_MIN = 4
_DORYANI_TEMPLE_VALUE = 100
_LOCUS_TEMPLE_VALUE = 60
_PRIME_REGRADING_VALUE = 40
_SECONDARY_REGRADING_VALUE = 140

__METRIC_SCARAB_PRICE = "ninja.price.scarab"
__METRIC_DELI_PRICE = "ninja.price.deliorb"
__METRIC_DIV_PRICE = "ninja.price.div"
__METRIC_INVIT_PRICE = "ninja.price.invit"
__METRIC_FOSSIL_PRICE = "ninja.price.fossil"
__METRIC_RESONATOR_PRICE = "ninja.price.resonator"
__METRIC_BEAST_PRICE = "ninja.price.beast"
__METRIC_ESSENCE_PRICE = "ninja.price.essence"
__METRIC_COMPASS_PRICE = "ninja.price.compass"
__METRIC_COMPASS_VOLUME = "ninja.volume.compass"
__METRIC_GEM_BASE = "ninja.price.gem.base"
__METRIC_GEM_TEMPLE = "ninja.price.gem.temple"
__METRIC_GEM_VAAL = "ninja.price.gem.vaal"
__METRIC_GEM_ALT = "ninja.price.gem.altvalues"
__METRIC_GEM_ALT_SORTABLE = "ninja.price.gem.altvalues.sortable"
__METRIC_POESTACK_ECON = "poestack.econprice.%s"
METRIC_POESTACK_ECON_BEST_EFFORT = "poestack.econprice.%s.best_effort"

DEBUG_FLAG = False

def print_if_debug(*prints):
    if DEBUG_FLAG:
        print(" ".join(str(s) for s in prints))

def print_and_return_avg(cat, prices_by_name):
    print_if_debug("="*50)
    print_if_debug(" "*int((50-len(cat))/2), cat)
    print_if_debug("="*50)
    for key, val in prices_by_name.items():
        print_if_debug("%s: %.2f" % (key, val))
    return sum(val for val in prices_by_name.values())/len(prices_by_name)

def print_essences(cat, prices_by_name):
    avg = print_and_return_avg(cat, prices_by_name)
    print_if_debug("-> %s Avg: %.2f" % (cat, avg))

def essence_stuff():
    ess = requests.get(Resources._URLS["Essence"]).json()
    ess_prices = {n['name']:n['chaosValue'] for n in ess['lines']}
    for e,v in ess_prices.items():
        parts = e.split(" ")
        tags = []
        if "Deafening" in e or "Shrieking" in e or "Remnant" in e:
            tags += ["tier:" + parts[0], "type:" + parts[-1]]
        elif "Horror" in e or "Delirium" in e or "Hysteria" in e or "Insanity" in e:
            tags += ["tier:Corruption", "type:" + parts[-1]]
        else:
            continue

        statsd.gauge(__METRIC_ESSENCE_PRICE, v, tags=tags)
    deaf = {key:val for key, val in ess_prices.items() if 'Deaf' in key}
    shriek = {key:val for key, val in ess_prices.items() if 'Shriek' in key}
    corru = {key:val for key, val in ess_prices.items() if 'Hyster' in key or 'Insan' in key or 'Deliri' in key or 'Horror' in key}
    print_essences("Deafening Essences", deaf)
    print_essences("Shrieking Essences", shriek)
    print_essences("Corrupted Essences", corru)

def print_scarabs(cat, prices_by_name):
    avg = print_and_return_avg(cat, prices_by_name)
    print_if_debug("-> %s Avg for 12: %.2f" % (cat, 12*avg))
    print_if_debug("-"*int((50-len("Reroll"))/2), "Reroll", "-"*int((50-len("Reroll"))/2))
    for key, val in prices_by_name.items():
        diff = avg - 2*val+0.2
        if diff > 0:
            print_if_debug("%s: %.2f" % (key, diff))

def scarab_stuff():
    sca = requests.get(Resources._URLS["Scarabs"]).json()
    sca_prices = {n['name']:n['chaosValue'] for n in sca['lines']}

    for scarab,v in sca_prices.items():
        parts = scarab.split(" ")
        tags = []
        tags += ["tier:" + parts[0], "type:" + parts[1]]

        statsd.gauge(__METRIC_SCARAB_PRICE, v, tags=tags)

    gilded = {key:val for key, val in sca_prices.items() if 'Gilded' in key}
    polished = {key:val for key, val in sca_prices.items() if 'Polished' in key}
    rusted = {key:val for key, val in sca_prices.items() if 'Rusted' in key}
    print_scarabs("Gilded Scarabs", gilded)
    print_scarabs("Polished Scarabs", polished)
    print_scarabs("Rusted Scarabs", rusted)

def delirium_stuff():
    deli = requests.get(Resources._URLS["Delirium"]).json()
    deli_prices = {n['name'].split(" ")[0]:n['chaosValue'] for n in deli['lines']}

    for name, v in deli_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_DELI_PRICE, v, tags=tags)

def div_stuff():
    div = requests.get(Resources._URLS["Div"]).json()
    div_prices = {n['name']:n['chaosValue'] for n in div['lines'] if n['chaosValue'] > 20}

    for name, v in div_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_DIV_PRICE, v, tags=tags)

def invit_stuff():
    invit = requests.get(Resources._URLS["Invitations"]).json()
    invit_prices = {n['name']:n['chaosValue'] for n in invit['lines']}

    for name, v in invit_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_INVIT_PRICE, v, tags=tags)

def fossil_stuff():
    fossil = requests.get(Resources._URLS["Fossils"]).json()
    fossil_prices = {n['name']:n['chaosValue'] for n in fossil['lines']}

    for name, v in fossil_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_FOSSIL_PRICE, v, tags=tags)

def resonator_stuff():
    resonator = requests.get(Resources._URLS["Resonators"]).json()
    resonator_prices = {n['name']:n['chaosValue'] for n in resonator['lines']}

    for name, v in resonator_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_RESONATOR_PRICE, v, tags=tags)

def beast_stuff():
    beast = requests.get(Resources._URLS["Beasts"]).json()
    beast_prices = {n['name']:n['chaosValue'] for n in beast['lines'] if n['chaosValue'] > 10}

    for name, v in beast_prices.items():
        tags = []
        tags += ["type:" + name]
        statsd.gauge(__METRIC_BEAST_PRICE, v, tags=tags)

def gems_compute_and_print_values(alt, name, gems):
    clean_low = int(gems["1"]) if "1" in gems else 0
    statsd.gauge(__METRIC_GEM_BASE, clean_low, tags=["gem:"+name])

    plus_level_mq = gems["21c"] if "21c" in gems else 0
    plus_level_mq_contrib_temple = int(0.04167*plus_level_mq)

    plus_level = gems["21/20c"] if "21/20c" in gems else plus_level_mq
    plus_level_contrib_temple = int(0.166666*plus_level)
    plus_level_contrib_vaal = int(0.125*plus_level)

    plus_qual = gems["20/23c"] if "20/23c" in gems else 0
    plus_qual_contrib_temple = int(0.166666*plus_qual)
    plus_qual_contrib_vaal = int(0.091*plus_qual)

    plus_plus = gems["21/23c"] if "21/23c" in gems else max(plus_level, plus_qual)
    plus_plus_contrib = int(0.0375*plus_plus)

    temple_return = plus_level_mq_contrib_temple + plus_level_contrib_temple + plus_qual_contrib_temple + plus_plus_contrib - _DORYANI_TEMPLE_VALUE - clean_low

    # TODO: fix vaal odds
    if clean_low != 0:
        statsd.gauge(__METRIC_GEM_TEMPLE, temple_return, tags=["name:"+name])
        if temple_return > 30:
            print_if_debug("="*50)
            print_if_debug(" "*int((50-len(name))/2), name, " Temple")
            print_if_debug("="*50)
            print_if_debug("Clean: ", clean_low, (8-len(str(clean_low)))*" ", "- Return: ", temple_return)
            if plus_plus_contrib > 0:
                print_if_debug("21/23: ", plus_plus, (8-len(str(plus_plus)))*" ", "~ ", plus_plus_contrib)
            if plus_level_contrib_temple > 0:
                print_if_debug("21/20: ", plus_level, (8-len(str(plus_level)))*" ", "~ ", plus_level_contrib_temple)
            if plus_level_mq_contrib_temple > 0:
                print_if_debug("21/--: ", plus_level_mq, (8-len(str(plus_level_mq)))*" ", "~ ", plus_level_mq_contrib_temple)
            if plus_qual_contrib_temple > 0:
                print_if_debug("20/23: ", plus_qual, (8-len(str(plus_qual)))*" ", "~ ", plus_qual_contrib_temple)

    vaal_return = plus_level_contrib_vaal + plus_qual_contrib_vaal - clean_low

    if clean_low != 0:
        statsd.gauge(__METRIC_GEM_VAAL, vaal_return, tags=["name:"+name])
        if vaal_return > 30:
            print_if_debug("="*50)
            print_if_debug(" "*int((50-len(name))/2), name, " Vaal")
            print_if_debug("="*50)
            print_if_debug("Clean: ", clean_low, (8-len(str(clean_low)))*" ", "- Return: ", vaal_return)
            if plus_plus_contrib > 0:
                print_if_debug("21/23: ", plus_plus, (8-len(str(plus_plus)))*" ", "~ ", plus_plus_contrib)
            if plus_level_contrib_temple > 0:
                print_if_debug("21/20: ", plus_level, (8-len(str(plus_level)))*" ", "~ ", plus_level_contrib_temple)
            if plus_level_mq_contrib_temple > 0:
                print_if_debug("21/--: ", plus_level_mq, (8-len(str(plus_level_mq)))*" ", "~ ", plus_level_mq_contrib_temple)
            if plus_qual_contrib_temple > 0:
                print_if_debug("20/23: ", plus_qual, (8-len(str(plus_qual)))*" ", "~ ", plus_qual_contrib_temple)

def parse_ninja_alt_gems_values():
    gem = requests.get(Resources._URLS["Skill Gems"]).json()
    gem_data_per_alt = {}
    html_gem_data_per_alt = {}
    gem_prices_alt_lists = {}
    for alt in ["Divergent", "Anomalous", "Phantasmal"]:
        gem_data_per_alt[alt] = [n for n in gem['lines'] if alt in n['name']]
        gem_prices_alt_lists[alt] = {}
        for gem_variant in gem_data_per_alt[alt]:
            # TODO: Handle vaal gracefully 
            if gem_variant['count'] < _LISTING_CONFIDENCE_MIN or "Vaal" in gem_variant['name']:
                continue
            if gem_variant['name'] in gem_prices_alt_lists[alt]:
                gem_prices_alt_lists[alt][gem_variant['name']][gem_variant['variant']] = gem_variant['chaosValue']
                continue
            gem_prices_alt_lists[alt][gem_variant['name']] = {gem_variant['variant']:gem_variant['chaosValue']}
    for altgems in gem_prices_alt_lists.values():
        for name, variants in altgems.items():
            if "1" in variants and variants["1"] > 20:
                html_gem_data_per_alt[name] = variants["1"]
    table_content = []
    for name, val in html_gem_data_per_alt.items():
        alt = name.split(" ")[0]
        tags = ["name:" + name, "alt:"+alt]
        statsd.gauge(__METRIC_GEM_ALT, val, tags=tags)
        table_content += [(" ".join(name.split(" ")[1:]), name.split(" ")[0], val)]
        
        cleaned_name = '_'.join(name.split(' ')[1:])
        sortable_tags = ["name:" + cleaned_name + "[" + alt + "]", "alt:"+alt, "init:" + cleaned_name[0]]
        statsd.gauge(__METRIC_GEM_ALT_SORTABLE, val, tags=sortable_tags)


    page = ""
    tables = []
    line_var = Templates.__HTML_TABLE_ROW_TEMPLATE_PRIM
    table_content.sort(key=lambda x: x[0])
    for col in [1,2,3,4]:
        table_rows = ""
        for c in table_content[int(len(table_content)*(col-1)/4):int(len(table_content)*col/4)]:
            table_rows += line_var % c
            line_var = Templates.__HTML_TABLE_ROW_TEMPLATE_PRIM if line_var == Templates.__HTML_TABLE_ROW_TEMPLATE_SEC else Templates.__HTML_TABLE_ROW_TEMPLATE_SEC
        tables += [Templates.__HTML_TABLE_TEMPLATE%table_rows]
 
    with open("gems_html.html", 'w') as file:
        file.write(Templates.__HTML_REFRESH_TEMPLATE%(tables[0], tables[1], tables[2], tables[3]))
                

    return gem_prices_alt_lists

def gem_stuff_ninja():
    gem_prices_alt_lists = parse_ninja_alt_gems_values()
    
    for alt, gems_by_alt in gem_prices_alt_lists.items():
        for name, gems in gems_by_alt.items():
            gems_compute_and_print_values(alt, name, gems)

def lookup_alt_gem(name):
    url_name = name.replace(" ", "_")
    lens = requests.get("https://poedb.tw/us/" + url_name).content
    soup = BeautifulSoup(lens, "html.parser")
    res = soup.body.find_all("div", class_="table-responsive")[0].table.find_all("td")
    alts = {}
    if len(res) != 6 and len(res) != 9 and len(res) != 12:
        return {}
    for i in range(len(res)):
        if i % 3 == 0:
            alts[res[i].text] = int(res[i+2].text)
    return alts

def process_valuable_alt_gem(base_name, gems_weights, gem_prices_alt_lists):
    if not base_name in gems_weights:
        gems_weights[base_name] = lookup_alt_gem(base_name)
        with open("gems_weights.json", 'w') as file:
            file.write(json.dumps(gems_weights, indent=4))

    altvalues = {"Superior ":1}

    for alt in gems_weights[base_name]:
        if alt[:-1] != "Superior":
            altvalues[alt] = gem_prices_alt_lists[alt[:-1]][alt + base_name]['1']
            # print_if_debug(alt, base_name, altvalues[alt])

    # hack ninja
    if base_name == "Soulrend":
        altvalues["Phantasmal "] = 1158
    #####

    total_weight = sum(int(s) for s in gems_weights[base_name].values())
    esps = {}
    lens_cost = _SECONDARY_REGRADING_VALUE if "Support" in base_name else _PRIME_REGRADING_VALUE
    for alt in gems_weights[base_name]:
        esps[alt] = {"name":alt}
        esp = 0
        relative_weight = total_weight - int(gems_weights[base_name][alt])
        for altroll in gems_weights[base_name]:
            if altroll != alt:
                esps[alt]["val"] = int(altvalues[altroll] * int(gems_weights[base_name][altroll]) / relative_weight) - lens_cost
    if any(esps[alt]["val"] > 0 for alt in esps):
        print_if_debug("="*50)
        print_if_debug(" "*int((50-len(base_name))/2), base_name)
        print_if_debug("="*50)
        for alt in esps:
            if esps[alt]["val"] > 0:
                print_if_debug("Hit ", esps[alt]["name"], ": ", esps[alt]["val"])


def lens_stuff():
    gems_weights = ""
    with open("gems_weights.json", 'r') as file:
        gems_weights = json.loads(file.read())
    
    gem_prices_alt_lists = parse_ninja_alt_gems_values()

    for alt, gems_by_alt in gem_prices_alt_lists.items():
        for name, gems in gems_by_alt.items():
            if "1" in gems and gems["1"] > 50:
                base_name = " ".join(name.split(" ")[1:])
                process_valuable_alt_gem(base_name, gems_weights, gem_prices_alt_lists)


def compass_stuff():
    for level in Resources._SEXTANTS:
        for sext in Resources._SEXTANTS[level]:
            tags = ["name:" + sext, "level:"+ level]
            query_compass(sext, 40, tags)
    # query_compass("Conqueror Map", 20, ["name:" + "Conqueror Map", "level:"+"awakened"])

def query_compass(compass_name, volume, tags):
    query = """query TftLiveListingSearch($listingSearch: TftLiveListingSearch!) {
        tftLiveListingSearch(search: $listingSearch) {
            channelId
            messageId
            userDiscordId
            userDiscordName
            userDiscordDisplayRole
            userDiscordHighestRole
            userDiscordDisplayRoleColor
            updatedAtTimestamp
            delistedAtTimestamp
            tag
            properties
            __typename
          }
      }"""
    variables = {
    "listingSearch":{
        "tag":"compasses",
        "propertyFilterGroups":[{
                "filters":[{
                    "key":"compasses,%s,quantity" % compass_name,
                    "value":"5"
                }]
            }]
        }
    }


    compass_resp = query_poe_stack(query, variables)
    # print_if_debug(compass_resp)
    if compass_resp == "":
        return

    sorted_listings = sorted(compass_resp['data']['tftLiveListingSearch'], key=lambda listing: listing['properties']['compasses'][compass_name]['value'])
    # print_if_debug("---- Listings for %s" % compass_name)
    # for listing in sorted_listings:
    #     print_if_debug(listing['properties']['compasses'][compass_name])
    
    found = 0
    cost = 0
    cursor = 0
    if len(sorted_listings) == 0:
        print_if_debug("---- No listed price for %s" % compass_name)
        return
    while found < volume and cursor < len(sorted_listings):
        l = sorted_listings[cursor]['properties']['compasses'][compass_name]
        use = volume - found if found + l['quantity'] > volume else l['quantity']

        found += use
        cost += use*l['value']
        # print_if_debug(found, cost)
        cursor += 1


    print_if_debug("---- Listed price for %s with min volume %d: %.2f" % (compass_name, found, float(cost)/found))

    statsd.gauge(__METRIC_COMPASS_PRICE, float(cost)/found, tags=tags)

    # max_price = sorted_listings[-1]['properties']['compasses'][compass_name]['value']
    # tenth = int(max_price//10)
    # price_distro = { tenth*i:0 for i in range(10) }
    # for l in sorted_listings:
    #     listing = l['properties']['compasses'][compass_name]
    #     price_distro[listing['value']//10] += listing['quantity']
    # for key, vol in price_distro.items():
    #     statsd.gauge(__METRIC_COMPASS_VOLUME, vol, tags=tags+["slice:%d", key])

def contract_stuff():
    return poestack_econ_query("contract")

def blueprint_stuff():
    return poestack_econ_query("blueprint")

def currency_stuff():
    return poestack_econ_query("currency")

def artifact_stuff():
    return poestack_econ_query("artifact")

def logbook_stuff():
    return poestack_econ_query("logbook")

def fragment_stuff():
    return poestack_econ_query("fragment")

def gem_stuff():
    return poestack_econ_query("gem")

def incubator_stuff():
    return poestack_econ_query("incubator")

def poestack_summary_query(econ_object):
    query = """
    query Query($search: LivePricingSummarySearch!) {
      livePricingSummarySearch(search: $search) {
        entries {
          itemGroup {
            hashString
            key
            properties
            icon
            displayName
            __typename
          }
          valuation {
            value
            validListingsLength
            __typename
          }
          stockValuation {
            listingPercent
            value
            validListingsLength
            __typename
          }
          __typename
        }
        __typename
      }
    }
    """
    variables = {
        "search": {
            "league": "Crucible",
            "offSet": 0,
            "searchString": "",
            "tag": "oil",
            "quantityMin": 25
        }
    }
    poestack_econ_resp = query_poe_stack(query, variables)
    print(poestack_econ_resp["data"]["livePricingSummarySearch"]["entries"][2])


def poestack_econ_query(econ_object):
    econ_data_dict = {}
    query_percentiles = ["p10", "p20"]
    stock_starting_ranges = [0, 9, 18, 30]
    query = """query TftLiveListingSearch($search: ItemGroupValueTimeseriesSearchInput!) {
        itemGroupValueTimeseriesSearch(search: $search) {
            results {
                itemGroup {
                    tag
                    key
                    properties
                }
                series {
                    entries {
                      value
                    }
                    stockRangeStartInclusive
                    type
                }
            }
        }
      }"""



    variables = {
        "search": {
            "seriesTypes":query_percentiles,
            "stockStartingRanges":stock_starting_ranges,
            "itemGroupSearch":{
                "itemGroupHashStrings":[],
                "itemGroupHashKeys":[],
                "league":"Crucible",
                "skip":0,
                "limit":500,
                "sortDirection": -1,
                "itemGroupHashTags":[econ_object]
            }
        }
    }
    poestack_econ_resp = query_poe_stack(query, variables)["data"]["itemGroupValueTimeseriesSearch"]["results"]
    for i in range(len(poestack_econ_resp)):
        itemGroup = poestack_econ_resp[i]['itemGroup']
        group_dict = econ_data_dict.get(itemGroup['key'], {})
        # for item in poestack_econ_resp[i]['series']:
        #     print(item["stockRangeStartInclusive"])
        #     print(item["type"])
        stock = {
            stocksize: {
                p: [
                item for item in poestack_econ_resp[i]['series'] if item["stockRangeStartInclusive"] == stocksize and item["type"] == p
                ] 
                for p in query_percentiles}
            for stocksize in stock_starting_ranges
        }


        #     0: {p: [item for item in poestack_econ_resp[i]['series'] if item["stockRangeStartInclusive"] == 0 and item["type"] == p] for p in query_percentiles},
        #     9: {p: [item for item in poestack_econ_resp[i]['series'] if item["stockRangeStartInclusive"] == 9 and item["type"] == p] for p in query_percentiles},
        #     18: {p: [item for item in poestack_econ_resp[i]['series'] if item["stockRangeStartInclusive"] == 18 and item["type"] == p] for p in query_percentiles},
        #     30: {p: [item for item in poestack_econ_resp[i]['series'] if item["stockRangeStartInclusive"] == 30 and item["type"] == p] for p in query_percentiles}
        # }
        best_effort_price = 0
        for stocksize in sorted(stock_starting_ranges, reverse=True):
            for p, percentile_serie in stock[stocksize].items():
                if percentile_serie:
                    best_effort_price = percentile_serie[0]['entries'][0]["value"]
                    break
            if best_effort_price != 0:
                break
        

        print_if_debug("="*50)
        # print_if_debug(itemGroup['key'], itemGroup['properties'][0]["value"], itemGroup['properties'][1]["value"], itemGroup['properties'][2]["value"])
        print_if_debug(itemGroup['key'])
        properties_tags = ["%s:%s" % (str(item['key']), str(item['value'])) for item in itemGroup['properties']]
        tags = properties_tags + ["type:" + itemGroup['key']]
        group_dict[",".join(sorted(properties_tags))] = best_effort_price
        statsd.gauge(METRIC_POESTACK_ECON_BEST_EFFORT % econ_object, best_effort_price, tags=tags)
        
        for s in tags:
            print_if_debug(s)
        print_if_debug("-"*50)

        for count, timeseries in stock.items():
            for p, percentile_serie in timeseries.items():
                if percentile_serie:
                    subtags = tags + ["percentile:" + p, "stock:" + str(count)]
                    statsd.gauge(__METRIC_POESTACK_ECON % econ_object, percentile_serie[0]['entries'][-1]["value"], tags=subtags)

                    print_if_debug("min %d - %s: %s" % (count, p, percentile_serie[0]['entries'][-1]["value"]))
        print_if_debug("-"*50)
        print_if_debug(best_effort_price)

        econ_data_dict[itemGroup['key']] = group_dict
                
    return econ_data_dict




_DATA_CRAWLING_FUNCS = {
    "gem": gem_stuff_ninja,
    "lens": lens_stuff,
    "essence": essence_stuff,
    "scarab": scarab_stuff,
    "compass": compass_stuff,
    "delirium": delirium_stuff,
    "div": div_stuff,
    "invit": invit_stuff,
    "fossil": fossil_stuff,
    "resonator": resonator_stuff,
    "beast": beast_stuff,
}

_DATA_CRAWLING_POESTACK_FUNCS = {
    "contract": contract_stuff,
    "blueprint": blueprint_stuff,
    "currency": currency_stuff,
    "artifact": artifact_stuff,
    "logbook": logbook_stuff,
    "fragment": fragment_stuff,
    "incubator": incubator_stuff,
    # "gem": gem_stuff,
}

def crawl_prices():
    for _,price_func in _DATA_CRAWLING_FUNCS.items():
        price_func()
    poestack_data = {}
    for econ_type,price_func in _DATA_CRAWLING_POESTACK_FUNCS.items():
        poestack_data[econ_type] = price_func()
    with open("poestack_data.json", 'w') as file:
        file.write(json.dumps(poestack_data, indent=4))
    with open("poestack_table.csv", 'w') as file:
        file.write("Stratname, placeholder\n")
        file.write("Runs, 0\n")
        file.write("Type, Name, Additional Info, Value, Spend, Return\n")
        for econ_type, type_data in poestack_data.items():
            for type_name, name_data in type_data.items():
                for name_tags, value in name_data.items():
                    file.write("%s, %s, %s, %s, 0, 0\n" % (econ_type, type_name, name_tags.replace(",", ";"), str(value)))


if __name__ == "__main__":
    # querier = POE_Stack_Querier(Config, "Crucible")

    initialize(**Config.datadog_options)
    parser = argparse.ArgumentParser(description='Crawl ninja market')
    parser.add_argument('-t', '--type', default="")
    parser.add_argument('-d', '--debug', type=bool, default=False)
    args = parser.parse_args()
    if args.debug:
        DEBUG_FLAG = True
    print_if_debug(args.type)
    if args.type != "":
        if args.type == "test":
            # poestack_summary_query(args.type)
            # print(querier.tft_compasses("Breach"))
            store = Economy_Store(Config)
        if args.type == "dump":
            crawl_prices()
            exit()
        # if _DATA_CRAWLING_FUNCS[args.type]:
        #     _DATA_CRAWLING_FUNCS[args.type]()
        # if _DATA_CRAWLING_POESTACK_FUNCS[args.type]:
        #     _DATA_CRAWLING_POESTACK_FUNCS[args.type]()
        exit()

    while True:
        crawl_prices()
        time.sleep(30)




