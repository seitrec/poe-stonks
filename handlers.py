from constants import *
from query_builder import *
from utils import *
import json
import time

from datadog import statsd

# class Value_Handler:
#     def __init__(self, raw):
#         self.mono_value = 
#         self.bulk_values = []
#         self.all_listings = {}


class Market_Handler:
    def __init__(self, tag, key, key_tags):
        self.tag = tag
        self.key = key
        self.hashString = ""
        self.properties = ""
        self.key_tags = key_tags
        self.properties_tags = []
        self.properties_key = ""
        self.display_name = ""
        self.values = {1: -1, 25: -1}
        self.listings = {}
        self.stocks = {1: 0, 25: 0}
        self.total_stock = 0
        return

    @classmethod
    def sanitize(cls, raw):
        return str(raw).lower().replace(",", "_").replace(":", ".").replace("\n", "_")

    @classmethod
    def parse_properties_poestack(cls, raw_item, key_tags):
        raw_properties = raw_item["itemGroup"]["properties"]
        properties = {prop["key"]: prop["value"] for prop in raw_properties}
        properties_tags = ["%s:%s" % (Market_Handler.sanitize(pk), Market_Handler.sanitize(pv)) 
        for pk, pv in properties.items()]
        properties_key = "|".join(properties_tags)
        return properties, properties_tags, properties_key

    def update(self, raw_item):
        self.hashString = raw_item["itemGroup"]["hashString"]
        self.properties, self.properties_tags, self.properties_key = Market_Handler.parse_properties_poestack(raw_item, self.key_tags)
        self.display_name = raw_item["itemGroup"]["displayName"]
        self.process_values(raw_item)
        return

    def process_values(self, raw_item):
        if raw_item["valuation"]:
            self.store_listings(1, raw_item["valuation"])
            self.total_stock = sum(listing["quantity"] for listing in self.listings[1])
        if raw_item["stockValuation"]:
            self.store_listings(25, raw_item["stockValuation"])

    def store_listings(self, count, raw_values):
        self.listings[count] = raw_values["validListings"]
        self.values[count] = raw_values["value"]
        self.stocks[count] = sum(listing["quantity"] for listing in self.listings[count] if listing["quantity"] <= self.values[count])

    def match_property(self, name, value):
        return name in self.properties and self.properties[name] == value

    def print(self):
        print(self.toCSV())
        return 

    def get_combined_tags(self):
        return self.key_tags + self.properties_tags

    def toCSV(self):
        return "%s, %s, %s, %d, %d" % (self.tag, self.key, self.properties_key, self.values[1], self.stocks[1])

    def write_as_csv(self, f, volume):
        if self.values[volume] <= 0:
            return
        # "Tag, Key, Properties, Value, Spend, Return
        csv_tags = "|".join(self.get_combined_tags())
        f.write("%s, %d, %s, %s, %s, %s, %d, , \n" % (self.tag, volume, Templates.econ_price_metric(self.tag, volume), self.key, csv_tags, "", self.values[volume]))

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    def report(self):
        if self.values[1] != -1:
            statsd.gauge(Templates.econ_price_metric(self.tag, 1), self.values[1], tags=self.get_combined_tags())
        if self.values[25] != -1:
            statsd.gauge(Templates.econ_price_metric(self.tag, 25), self.values[25], tags=self.get_combined_tags())
        return

class Gem_Market_Handler(Market_Handler):
    def update(self, raw_ninja):
        self.hashString = "no hash string in ninja"
        self.properties, self.properties_tags, self.properties_key = self.parse_gem_properties(raw_ninja)
        self.display_name = self.key # TODO maybe mix properties
        self.process_values(raw_ninja)

    def process_values(self, raw_ninja):
        self.stocks[1] = raw_ninja['listingCount']
        self.values[1] = raw_ninja['chaosValue']

    @classmethod
    def parse_gem_properties(cls, raw_item):
        vaal = "vaal" in raw_item['detailsId']
        variant = (("v" if vaal else "") + raw_item['variant']) if 'variant' in raw_item else "?"
        properties = {
            "corrupted": raw_item['corrupted'] if 'corrupted' in raw_item else "False", 
            "gem_level": raw_item['gemLevel']if 'gemLevel' in raw_item else "1", 
            "quality": raw_item['gemQuality']if 'gemQuality' in raw_item else "1", 
            "short": variant, 
            "vaal": vaal,
        }
        properties_tags = ["%s:%s" % (pk, pv) for pk, pv in properties.items()]
        properties_key = "|".join(properties_tags)
        return properties, properties_tags, properties_key

    def compare_short(self, short):
        return self.properties["short"] == short



class Key_Handler():
    def __init__(self, tag, key):
        self.tag = tag
        self.key = key
        self.variants = {}
        self.ninja_value = -1
        self.key_tags = []
        self.key_tags = self.parse_tags(tag, key)
        return

    def update(self, raw_item):
        properties, properties_tags, properties_key = Market_Handler.parse_properties_poestack(raw_item, self.key_tags)
        if not properties_key in self.variants:
            self.variants[properties_key] = Market_Handler(self.tag, self.key, self.key_tags)
        self.variants[properties_key].update(raw_item)

    def update_ninja(self, ninja_value):
        self.ninja_value = ninja_value
        if len(self.variants) == 0:
            self.variants[""] = Market_Handler(self.tag, self.key, self.key_tags)

    def parse_tags(self, tag, key):
        key_tags = ["%s:%s" % ("key", self.key)]
        if tag == "essence":
            if "horror" in key or "delirium" in key or "hysteria" in key or "insanity" in key:
                key_tags.append("tier:corrupted")
            else:
                key_tags.append("tier:" + key.split(" ")[0])
        elif tag == "scarab":
            key_tags.append("tier:" + key.split(" ")[0])
        elif tag == "map":
            if "ravaged" in key:
                key_tags.append("mapset:" + "blight_ravaged")
            elif "blighted" in key:
                key_tags.append("mapset:" + "blighted")
            elif any(conq in key for conq in ["baran", "veritania", "drox", "hezmin"]):
                key_tags.append("mapset:" + "conqueror")
            elif any(shap in key for shap in ["minotaur", "phoenyx", "chimera", "hydra"]):
                key_tags.append("mapset:" + "shaper")
            elif any(eld in key for eld in ["eradicator", "purifier", "constrictor", "enslaver"]):
                key_tags.append("mapset:" + "elder")
            else:
                key_tags.append("mapset:" + "basic")
        return key_tags
        # elif tag == "scarab":
        #     self.key_tags.append(["tier:" + key.split(" ")[0]])
        # elif tag == "scarab":
        #     self.key_tags.append(["tier:" + key.split(" ")[0]])
        # elif tag == "scarab":
        #     self.key_tags.append(["tier:" + key.split(" ")[0]])
        # elif tag == "scarab":
        #     self.key_tags.append(["tier:" + key.split(" ")[0]])

    def find_property_match(self, name, value):
        return [variant for variant in self.variants.values() if variant.match_property(name, value)]

    def toCSV(self):
        csv = ""
        for handler in self.variants.values():
            csv = csv + "%s, %s, %s, %d, %d, %d\n" % (handler.tag, handler.key, handler.properties_key, self.ninja_value, handler.values[1], handler.stocks[1])
        return csv

    def write_as_csv_no_filters(self, f):
        for variant in self.variants.values():
            for volume in [1, 25]:
                variant.write_as_csv(f, volume)

    def print(self):
        print(self.toCSV(), end="")
        # for handler in self.variants.values():
        #     handler.print()
        # print("NINJA VALUE: %s" % self.ninja_value)

    def report(self):
        for handler in self.variants.values():
            handler.report()
        if self.ninja_value != -1:
            statsd.gauge(Templates.ninja_price_metric(self.tag), self.ninja_value, tags=self.key_tags)

class Gem_Handler(Key_Handler):
    # def __init__(self, tag, key):
    #     Key_Handler.__init__(self, tag, key)
    fallback_map = {
        "1": ("", 1),
        "20/20": ("1", 1),
        "20/20c": ("20/20", 0.5),
        "21/20c": ("20/20", 10),
        "20/23c": ("20/20", 1.5),
        "21c": ("21/20c", 0.5),
        "21/23c": ("20/23c", 10),

        "v20/20c": ("20/20c", 1.5),
        "v21/20c": ("v20/20c", 10),
        "v20/23c": ("v20/20c", 1.5),
    }

    def update_ninja(self, ninja_raw):
        properties, properties_tags, properties_key = Gem_Market_Handler.parse_gem_properties(ninja_raw)
        if properties["short"] == "1":
            self.ninja_value = ninja_raw["chaosValue"]
        if not properties_key in self.variants:
            self.variants[properties_key] = Gem_Market_Handler(self.tag, self.key, self.key_tags)
        self.variants[properties_key].update(ninja_raw)

    def parse_tags(self, tag, key):
        key_tags = ["key:%s" % (self.key)]
        if "divergent" in key or "anomalous" in key or "phantasmal" in key or "awakened" in key:
            key_tags.append("variant:" + key.split(" ")[0])
        else: 
            key_tags.append("variant:superior")
        return key_tags

    def get_variant(self, short):
        for variant in self.variants.values():
            if variant.compare_short(short):
                return variant
        return {}

    def get_variant_status(self, short):
        variant = self.get_variant(short)
        if variant:
            return variant.values[1], variant.stocks[1]
        return 0, 0

    def get_variant_value(self, short):
        variant = self.get_variant(short)
        if variant:
            return variant.values[1]
        return 0

    def get_variant_stock(self, short):
        variant = self.get_variant(short)
        if variant:
            return variant.stocks[1]
        return 0

    def get_fallback_value(self, short, use_fallback_multipler = False):
        if not short:
            return 1
        value, stock = self.get_variant_status(short)

        if stock <= Config._LISTING_CONFIDENCE_MIN:
            if not short in Gem_Handler.fallback_map:
                print("error unknown gem variant to fallback to %s" % short)
                return 0
            fallback_name, fallback_multiplier = Gem_Handler.fallback_map[short]
            if not use_fallback_multipler:
                fallback_multiplier = 1
            return fallback_multiplier * self.get_fallback_value(fallback_name, use_fallback_multipler)
        return value

    def get_predicted_value(self, short):
        return self.get_fallback_value(short, True)


    def get_extrapolated_values(self, short):
        value, stock = self.get_variant_status(short)

        return {
            "unsafe": value,
            "conservative": self.get_fallback_value(short),
            "predicted": self.get_predicted_value(short),
            "minimal": value if stock > Config._LISTING_CONFIDENCE_MIN else 0,
        }

    def has_vaal_version(self):
        return(any(variant.properties["vaal"] for variant in self.variants.values()))

    def submit_vaal_returns(self, vaal_value):
        price_2020 = self.get_fallback_value("20/20")

        outcome_odds = 1/8.
        # odds_trash = outcome_odds * 2 (ignored, considered value = 0
        odds_v2020 = outcome_odds * 2

        odds_2020 = outcome_odds * (2 + 1*0.2)
        odds_2120 = outcome_odds * 1
        odds_2023 = outcome_odds * 1*0.8

        if self.has_vaal_version():
            estimations_v2020 = self.get_extrapolated_values("v20/20c")
        else:
            odds_2020 += odds_v2020

        part_v2020 = 0

        estimations_2020c = self.get_extrapolated_values("20/20c")
        estimations_2120 = self.get_extrapolated_values("21/20c")
        estimations_2023 = self.get_extrapolated_values("20/23c")

        for estimation in ["unsafe", "conservative", "predicted", "minimal"]:
            if self.has_vaal_version():
                part_v2020 = estimations_v2020[estimation] * odds_v2020

            part_2020c = estimations_2020c[estimation] * odds_2020
            part_2120 = estimations_2120[estimation] * odds_2120
            part_2023 = estimations_2023[estimation] * odds_2023


            vaal_return = int(part_v2020 + part_2020c + part_2120 + part_2023 - price_2020 - vaal_value)

            if vaal_return > 50:
                statsd.gauge(Templates._METRIC_STRAT_CORRUPTION_VAAL_GEM, vaal_return, tags=self.key_tags + ["estimation:%s" % estimation])


    def submit_temple_returns(self, temple_value):
        price_2020 = self.get_fallback_value("20/20")

        outcome_odds = 1/48.
        # odds_trash = outcome_odds * 10 (ignored, considered value = 0
        odds_v2020 = outcome_odds * (12 + 4*0.2)
        odds_v2120 = outcome_odds * 4
        odds_v2023 = outcome_odds * 4*0.8

        odds_2020 = outcome_odds * (4 + 6*0.2)
        odds_21 = outcome_odds * 2
        odds_2120 = outcome_odds * (4+2*0.2)
        odds_2023 = outcome_odds * 6*0.8
        odds_2123 = outcome_odds * 2*0.8

        if self.has_vaal_version():
            estimations_v2020 = self.get_extrapolated_values("v20/20c")
            estimations_v2120 = self.get_extrapolated_values("v21/20c")
            estimations_v2023 = self.get_extrapolated_values("v20/23c")
        else:
            odds_2020 += odds_v2020
            odds_2120 += odds_v2120
            odds_2023 += odds_v2023

        part_v2020, part_v2120, part_v2023 = 0,0,0

        estimations_2020c = self.get_extrapolated_values("20/20c")
        estimations_21 = self.get_extrapolated_values("21c")
        estimations_2120 = self.get_extrapolated_values("21/20c")
        estimations_2023 = self.get_extrapolated_values("20/23c")
        estimations_2123 = self.get_extrapolated_values("21/23c")

        for estimation in ["unsafe", "conservative", "predicted", "minimal"]:

            if self.has_vaal_version():
                part_v2020 = estimations_v2020[estimation] * odds_v2020
                part_v2120 = estimations_v2120[estimation] * odds_v2120
                part_v2023 = estimations_v2023[estimation] * odds_v2023

            part_2020c = estimations_2020c[estimation] * odds_2020
            part_21 = estimations_21[estimation] * odds_21
            part_2120 = estimations_2120[estimation] * odds_2120
            part_2023 = estimations_2023[estimation] * odds_2023
            part_2123 = estimations_2123[estimation] * odds_2123

            temple_return = int(part_v2020 + part_v2120 + part_v2023 + part_2020c + part_21 + part_2120 + part_2023 + part_2123 - price_2020 - temple_value)

            if temple_return > 50:
                # print(estimation, self.key, "base value= ", price_2020, "temple_return= ", temple_return)
                statsd.gauge(Templates._METRIC_STRAT_CORRUPTION_TEMPLE_GEM, temple_return, tags=self.key_tags + ["estimation:%s" % estimation])


class Economy_Tag_Summary:
    def __init__(self, poe_stack_querier, poe_ninja_querier, tag, markets):
        self.tag = tag
        self.markets = markets
        self.key_handlers = {}
        self.poe_stack_querier = poe_stack_querier
        self.poe_ninja_querier = poe_ninja_querier
        return

    def update_with_poestack(self, raw):
        for raw_item in raw:
            sanitized_key = Market_Handler.sanitize(raw_item["itemGroup"]["key"])
            if not sanitized_key in self.key_handlers:
                self.key_handlers[sanitized_key] = Key_Handler(self.tag, sanitized_key)
            self.key_handlers[sanitized_key].update(raw_item)
        

    def parse_ninja_raw_values(self, raw):
        # for line in raw['lines']:
        #     if Market_Handler.sanitize(line['name']) == "doryani's prototype":
        #         print(line)
        if self.tag == "currency" or self.tag == "fragment":
            return {Market_Handler.sanitize(n['currencyTypeName']):n['chaosEquivalent'] for n in raw['lines']}
        else:
            return {Market_Handler.sanitize(n['name']):n['chaosValue'] for n in raw['lines']}

    def update_with_poeninja(self, raw):
        ninja_values = self.parse_ninja_raw_values(raw)
        for key, ninja_value in ninja_values.items():
            if not key in self.key_handlers:
                self.key_handlers[key] = Key_Handler(self.tag, key)
            self.key_handlers[key].update_ninja(ninja_value)

    def update(self):
        if self.markets["stack"]:
            try:
                raw_poe_stack = self.poe_stack_querier.summary(self.tag)
                self.update_with_poestack(raw_poe_stack)
            except KeyboardInterrupt:
                exit()
            except Exception as e:
                print(e)
                print("failed to query poestack for %s" % self.tag)
        if self.markets["ninja"]:
            try:
                raw_poe_ninja = self.poe_ninja_querier.json_summary(self.markets["ninja"])
                self.update_with_poeninja(raw_poe_ninja)
            except KeyboardInterrupt:
                exit()
            except Exception as e:
                print(e)
                print("failed to query poeninja for %s" % self.tag)
        self.print()

    def get_ninja_value(self, key):
        sanitized_key = Market_Handler.sanitize(key)
        if sanitized_key in self.key_handlers:
            return self.key_handlers[sanitized_key].ninja_value
        return -1

    def convert_to_chaos(self, currency, amount):
        # print("converting to chaos: ", currency, amount)
        return self.swap_currency("chaos orb", currency, amount)

    def swap_currency(self, target_currency, currency, amount):
        if self.tag != "currency":
            print("Incorrect use of non currency Market Summary: %s" % self.tag)
            exit()
        target_value_c = self.get_ninja_value(target_currency) if target_currency != "chaos orb" else 1
        value_c = self.get_ninja_value(currency) if currency != "chaos orb" else 1
        if target_value_c == -1 or value_c == -1:
            print("Tried to convert %s(%d) to %s(%d) but values are not usable" % (currency, value_c, target_currency, target_value_c))
        
        return int(amount*value_c/target_value_c)

    def write_as_csv_ninja(self, f):
        volume = 1
        for key_handler in self.key_handlers.values():
            csv_tags = "|".join(key_handler.key_tags)
            f.write("%s, %d, %s, %s, %s, %s, %d, , \n" % (self.tag, volume, Templates.ninja_price_metric(self.tag), key_handler.key, csv_tags, "all", key_handler.ninja_value))

    def write_as_csv_aggr(self, f, aggr, tagset):
        csv_tags = "|".join(tagset)
        volume = 1
        f.write("%s, %d, %s, %s, %s, %s, , , \n" % (self.tag, volume, Templates.econ_price_metric(self.tag, volume), "Group", csv_tags, aggr))

    def write_as_csv_no_filters(self, f):
        for key_handler in self.key_handlers.values():
            key_handler.write_as_csv_no_filters(f)

    def write_as_csv(self, f):
        if not Resources._MARKET_TYPES[self.tag]["include_in_strat_csv"]:
            return

        variant_tag_set = set([key.split(":")[0] 
            for key_handler in self.key_handlers.values()
            for variant in key_handler.variants.values()
            for key in variant.get_combined_tags()])

        relevant_groups = Resources._MARKET_TYPES[self.tag]["grouping_stack_tags"]
        aggr_groups = variant_tag_set.difference(relevant_groups)
        csv_aggr_tags = "|".join(aggr_groups)

        tag_options_map = {}
        for key in relevant_groups:
            for key_handler in self.key_handlers.values():
                for variant in key_handler.variants.values():
                    for tag in variant.get_combined_tags():
                        k, v = tag.split(":")
                        if k in relevant_groups:
                            if k not in tag_options_map:
                                tag_options_map[k] = set()
                            tag_options_map[k].add(tag)

        tag_options_list = list(tag_options_map.values())
        unpacked_tagsets = unpack_tagsets(tag_options_list)

        for tagset in unpacked_tagsets:
            self.write_as_csv_aggr(f, csv_aggr_tags, tagset)

        if Resources._MARKET_TYPES[self.tag]["grouping_ninja"]:
            self.write_as_csv_ninja(f)

        self.write_as_csv_no_filters(f)

    def print(self):
        for _, key_handler in self.key_handlers.items():
            key_handler.print()
        return

    def report(self):
        for _, key_handler in self.key_handlers.items():
            key_handler.report()
        return

class Economy_Gem_Summary(Economy_Tag_Summary):
    def __init__(self, poe_stack_querier, poe_ninja_querier, tag, markets):
        Economy_Tag_Summary.__init__(self, poe_stack_querier, poe_ninja_querier, tag, markets)
        self.alt_data = ALT_GEMS_DATA()

    def update_with_poeninja(self, raw):
        ninja_items = self.parse_ninja_raws(raw)
        for key, ninja_item in ninja_items:
            key = key.replace("vaal ", "")
            if not key in self.key_handlers:
                self.key_handlers[key] = Gem_Handler(self.tag, key)
            self.key_handlers[key].update_ninja(ninja_item)

    def parse_ninja_raws(self, raw):
        return [(Market_Handler.sanitize(n['name']),n) for n in raw['lines']]

    def submit_temple_returns(self, temple_price):
        for key, handler in self.key_handlers.items():
            # TODO: we hack remove "awakened" here because they're annoying to compute relative to their levels
            if not "awakened" in key:
                handler.submit_temple_returns(temple_price)
        pass

    def submit_vaal_returns(self, vaal_price):
        for key, handler in self.key_handlers.items():
            # TODO: we hack remove "awakened" here because they're annoying to compute relative to their levels
            if not "awakened" in key:
                handler.submit_vaal_returns(vaal_price)
        pass

    def submit_lens_returns(self, prime_value, secondary_value):
        for base_name, alts in self.alt_data.gems_weights.items():
            used_lens_value = secondary_value if "Support" in base_name else prime_value
            value_map = {
                alt_name: {
                        "weight": weight, 
                        "value": self.key_handlers[Market_Handler.sanitize(((alt_name + " ") if alt_name != "Superior" else "") + base_name)].get_fallback_value("1"),
                    }
                for alt_name, weight in alts.items()
            }
            
            for hit_alt in value_map:
                relative_weight = sum(alt_dict["weight"] for alt, alt_dict in value_map.items() if alt != hit_alt)
                hit_return = sum(
                        float(alt_dict["weight"])/relative_weight * alt_dict["value"]
                        for alt, alt_dict in value_map.items() if alt != hit_alt
                    )
                profit = hit_return - value_map[hit_alt]["value"] - used_lens_value
                if profit > 50:
                    statsd.gauge(Templates._METRIC_STRAT_LENS_GEM, profit, tags=["hit_quality:%s" % hit_alt, "base_name:%s" % base_name])

    def run_strats(self, curr_summary, misc_summary):
        # print(misc_summary.key_handlers)
        # print(misc_summary.key_handlers['chronicle of atzoatl'].find_property_match("room", "doryani institute")[0].values[1])
        dory_value = misc_summary.key_handlers['chronicle of atzoatl'].find_property_match("room", "doryani institute")[0].values[1] if 'chronicle of atzoatl' in misc_summary.key_handlers else 0
        if dory_value:
            self.submit_temple_returns(dory_value)
        self.submit_vaal_returns(1)
        prime_value = curr_summary.key_handlers['prime regrading lens'].ninja_value if 'prime regrading lens' in curr_summary.key_handlers else 0
        secondary_value = curr_summary.key_handlers['secondary regrading lens'].ninja_value if 'secondary regrading lens' in curr_summary.key_handlers else 0
        if prime_value and secondary_value:
            self.submit_lens_returns(prime_value, secondary_value)

class Economy_Misc_Summary(Economy_Tag_Summary):
    def __init__(self, trade_api_querier, tag, currency_summary):
        self.tag = tag
        self.key_handlers = {}
        self.trade_api_querier = trade_api_querier
        self.currency_summary = currency_summary

    def update(self):
        try:
            postackified = self.trade_api_querier.get_temple_gem3(self.currency_summary)
            self.update_with_poestack(postackified)
        except Exception as e: 
            print(e)
            pass
        try:
            self.update_with_poestack(self.trade_api_querier.get_temple_corru3(self.currency_summary))
        except Exception as e: 
            print(e)
            pass
        
        # self.print()

class Economy_Store:
    def __init__(self, Config, custom_tags=[]):
        self.poe_stack_querier = POE_Stack_Querier(Config)
        self.poe_ninja_querier = POE_Ninja_Querier(Config)
        self.trade_api_querier = Trade_API_Querier(Config)
        self.groups = {}
        self.market_tags = Resources._MARKET_TYPES if not custom_tags else Resources._MARKET_TYPES_TEST(custom_tags) 
        print("Running Economy store with markets: %s" % ",".join(self.market_tags))
        self.create()
        return

    def create(self):
        for tag, markets in self.market_tags.items():
            if tag not in Resources._MARKET_TYPES:
                print("unknown market type")
                continue
            if tag == "gem":
                self.groups[tag] = Economy_Gem_Summary(self.poe_stack_querier, self.poe_ninja_querier, tag, markets)
            else:
                self.groups[tag] = Economy_Tag_Summary(self.poe_stack_querier, self.poe_ninja_querier, tag, markets)
        self.groups["misc"] = Economy_Misc_Summary(self.trade_api_querier, "misc", self.groups["currency"])

    def update(self):
        for tag, summary in self.groups.items():
            print("Updating %s" % tag)
            summary.update()

    def report(self):
        for summary in self.groups.values():
            summary.report()

    def run_gem_metrics(self):
        if 'gem' in self.groups and 'misc' in self.groups:
            self.groups['gem'].run_strats(self.groups["currency"], self.groups["misc"])

    def run(self):
        start = int(time.time())
        next_update = start
        while True:
            while int(time.time()) < next_update:
                print("==Sleep 60")
                time.sleep(60)
            next_update = next_update + 300
            self.update()
            self.report()
            self.run_gem_metrics()
            # print(self.groups['gem'].key_handlers['anomalous lightning strike'].print())

    def write_as_csv(self, f):
        for tag, summary in self.groups.items():
            summary.write_as_csv(f)


    def dump(self):
        self.update()
        with open("poedata_table.csv", 'w') as file:
            file.write("Stratname, placeholder\n")
            file.write("Runs, 0\n")
            file.write("Runs Per Hour, 0\n")
            file.write("Type, Volume, Metric, Key, Tag Filters, Aggr Tags, Value, Spend, Return\n")
            self.write_as_csv(file)

