import requests
from constants import *

class POE_Stack_Querier:
    def __init__(self, Config):
        self.league = Config.league
        self.auth = Config.poestack_token
        self.url = "https://api.poestack.com/graphql"
        return

    def query_poe_stack(self, query, variables):
        headers = { "Authorization" : self.auth }

        request = requests.post(self.url, json={'query': query, "variables": variables}, headers=headers)
        if request.status_code == 200:
            return request.json()
        else:
            print('Query failed. return code is {}.     {}'.format(
                request.status_code, query))
            # raise Exception('Query failed. return code is {}.     {}'.format(
            #     request.status_code, query))
            return []

    def summary(self, tag, quantityMin=25, offSet=0, searchString=""):
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
                  }
                  valuation {
                    value
                    validListingsLength
                    listingPercent
                    quantity
                    valueIndex
                    validListings {
                      listedValue
                      quantity
                    }
                  }
                  stockValuation {
                    listingPercent
                    value
                    validListingsLength
                    quantity
                    valueIndex
                    validListings {
                      quantity
                      listedValue
                      listedAtTimestamp
                    }
                  }
                }
              }
            }
        """
        variables = {
            "search": {
                "league": self.league,
                "offSet": offSet,
                "searchString": searchString,
                "tag": tag,
                "quantityMin": quantityMin,
            }
        }
        res = self.query_poe_stack(query, variables)["data"]["livePricingSummarySearch"]["entries"]
        return res

    def tft_compasses(self, compass_type):
        query = """
        query TftLiveListingSearch($search: TftLiveListingSearch!) {
          tftLiveListingSearch(search: $search) {
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
        }
        """

        variables = {
          "search": {
            "tag": "compasses",
            "propertyFilterGroups": [
              {
                "filters": [
                  {
                    "key": "compasses,%s,quantity" % (compass_type),
                    "value": "1"
                  }
                ]
              }
            ]
          }
        }
        return self.query_poe_stack(query, variables)


class POE_Ninja_Querier:
    def __init__(self, Config):
        self.league = Config.league
        return

    def json_summary(self, url_template):
        return requests.get(url_template % self.league).json()


class Trade_API_Querier:
    def __init__(self, Config):
        self.league = Config.league
        self.headers = Config.trade_api_headers
        self.search_url = "https://www.pathofexile.com/api/trade/search/%s" % self.league
        self.fetch_url = "https://www.pathofexile.com/api/trade/fetch/%s?query=%s"
        return

    def json_summary(self, variables):
        resp = requests.post(self.search_url, json=variables, headers=self.headers).json()
        listings_url = self.fetch_url % (",".join(resp["result"][0:10]), resp["id"])

        return requests.get(listings_url, headers=self.headers).json()

    def make_query_filter(self, name, option):
        return {
            "id": name,
            "value": {
                "option": option
            },
            "disabled": False
        }


    def make_query_vars(self, key, filters):
        return {
          "query": {
            "status": {
              "option": "online"
            },
            "type": key,
            "stats": [
              {
                "type": "and",
                "filters": filters,
                "disabled": False
              }
            ]
          },
          "sort": {
            "price": "asc"
          }
        }

    def poestack_ify(self, key, properties, json_resp, currency_summary):
        listings = [{
            "listedValue": currency_summary.convert_to_chaos(l['listing']['price']['currency'] + " orb", l['listing']['price']['amount']),
            "quantity": 1,
        } for l in json_resp['result']]
        avg = sum(l["listedValue"] for l in listings)/len(listings)
        estimate = min(v["listedValue"] for v in listings if v["listedValue"] > 0.9*avg)
        poestack_json = [{
            "itemGroup": {
                "hashString": "",
                "key": key,
                "properties": properties,
                "icon": "",
                "displayName": "",
            },
            "valuation": {
                "value": estimate,
                "validListingsLength": 10,
                "listingPercent": 10,
                "quantity": 1,
                "valueIndex": 1,
                "validListings": listings
            },
            "stockValuation": ""
        }]
        return poestack_json



    def get_temple_gem3(self, currency_summary):
        query_filter = self.make_query_filter("pseudo.pseudo_temple_gem_room_3", 1)
        variables = self.make_query_vars("Chronicle of Atzoatl", [query_filter])
        properties = [{
            "key": "room",
            "value": "doryani institute",
        }]
        trade_resp = self.json_summary(variables)
        return self.poestack_ify("Chronicle of Atzoatl", properties, trade_resp, currency_summary)

    def get_temple_corru3(self, currency_summary):
        query_filter = self.make_query_filter("pseudo.pseudo_temple_corruption_room_3", 1)
        variables = self.make_query_vars("Chronicle of Atzoatl", [query_filter])
        properties = [{
            "key": "room",
            "value": "locus of corruption",
        }]
        trade_resp = self.json_summary(variables)
        return self.poestack_ify("Chronicle of Atzoatl", properties, trade_resp, currency_summary)
        





