import json

class Config:
    poestack_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI4Njg0ZDQ5MC00OTVjLTQ5NGYtOTJlOS0yZDNjZTgzOTNlZDUiLCJwb2VQcm9maWxlTmFtZSI6ImFzYW1hcGxlIiwiaWF0IjoxNjgyOTA2OTgzfQ.04UZUscVc6ByX4rMbqVbxp6r8KLCeHa4jAp0tAWAb0w"
    datadog_options = {
        'statsd_host':'127.0.0.1',
        'statsd_port':8125
    }
    league = "Ancestor"
    trade_api_headers = {
        'Cookie': 'POESESSID=8499042a30412c275f9fe0204fa8b823',
        'user-agent': 'Maple-testing-trade-api-queries',
    }

    _LISTING_CONFIDENCE_MIN = 20

    def __init__(self):
        return


class Templates:
    __HTML_REFRESH_TEMPLATE = """
    <!DOCTYPE html>
    <html>
     
    <head>
        <title>Gems Alpha List</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
        <meta http-equiv="refresh" content="10">
    </head>
     
    <body>
        <div class="container-xl" style="font-size: x-small;">
          <div class="row">
            <div class="col-md-3">
              %s
            </div>
            <div class="col-md-3">
              %s
            </div>
            <div class="col-md-3">
              %s
            </div>
            <div class="col-md-3">
              %s
            </div>
          </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ENjdO4Dr2bkBIFxQpeoTz1HIcje39Wm4jDKdf19U8gI4ddQ3GYNS7NTKfAdVQSZe" crossorigin="anonymous"></script>
    </body>
     
    </html>"""

    __HTML_TABLE_TEMPLATE = """<table class="table table-sm">%s</table>"""
    __HTML_TABLE_ROW_TEMPLATE_PRIM = """<tr class="table-primary"><th style="font-weight: normal;">%s</th><th>%s</th><th>%d</th></tr>"""
    __HTML_TABLE_ROW_TEMPLATE_SEC = """<tr class="table-secondary"><th style="font-weight: normal;">%s</th><th>%s</th><th>%d</th></tr>"""

    _METRIC_POESTACK = "poestack.econprice.%s.%d"
    _METRIC_POENINJA = "poeninja.econprice.%s"

    _METRIC_STRAT_CORRUPTION_TEMPLE_GEM = "poeninja.corruption.temple.gem"
    _METRIC_STRAT_CORRUPTION_VAAL_GEM = "poeninja.corruption.vaal.gem"
    _METRIC_STRAT_LENS_GEM = "poeninja.lens.gem"

    @classmethod
    def econ_price_metric(cls, tag, bulk):
        return cls._METRIC_POESTACK % (cls.sanitize_for_metric(tag), bulk)

    @classmethod
    def ninja_price_metric(cls, tag):
        return cls._METRIC_POENINJA % (cls.sanitize_for_metric(tag))

    @classmethod
    def sanitize_for_metric(cls, s):
        return s.replace(" ", "_")



class Resources:
    
    @classmethod
    def _MARKET_TYPES_TEST(cls, tags):
        return {
            tag: cls._MARKET_TYPES[tag] for tag in tags
        }

    _MARKET_TYPES = {
        "currency": {
            "ninja": "https://poe.ninja/api/data/currencyoverview?league=%s&type=Currency",
            "stack": True,
        },
        "fragment": {
            "ninja": "https://poe.ninja/api/data/currencyoverview?league=%s&type=Fragment",
            "stack": True,
        },
        "scarab": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Scarab",
            "stack": True,
        },
        "compass": {
            "ninja": "",
            "stack": True,
        },
        "card": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=DivinationCard",
            "stack": True,
        },
        "artifacts": {
            "ninja": "",
            "stack": True,
        },
        "oil": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Oil",
            "stack": True,
        },
        "incubator": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Incubator",
            "stack": True,
        },
        "unique": {
            "ninja": "",
            "stack": True,
        },
        "cluster": {
            "ninja": "",
            "stack": True,
        },
        "atlas Memory": {
            "ninja": "",
            "stack": True,
        },
        "beast": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Beast",
            "stack": True,
        },
        "blueprint": {
            "ninja": "",
            "stack": True,
        },
        "catalyst": {
            "ninja": "",
            "stack": True,
        },
        "contract": {
            "ninja": "",
            "stack": True,
        },
        "delirium Orb": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=DeliriumOrb",
            "stack": True,
        },
        "essence": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Essence",
            "stack": True,
        },
        "fossil": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Fossil",
            "stack": True,
        },
        "gem": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=SkillGem",
            "stack": False,
        },
        "invitation": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Invitation",
            "stack": True,
        },
        "logbook": {
            "ninja": "",
            "stack": True,
        },
        "map": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Map",
            "stack": True,
        },
        "misc": {
            "ninja": "",
            "stack": True,
        },
        "resonator": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=Resonator",
            "stack": True,
        },
        "scouting Report": {
            "ninja": "",
            "stack": True,
        },
        "vial": {
            "ninja": "",
            "stack": True,
        },
        "unique accessory": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueAccessory",
            "stack": False,
        },
        "unique armour": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueArmour",
            "stack": False,
        },
        "unique weapon": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueWeapon",
            "stack": False,
        },
        "unique flask": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueFlask",
            "stack": False,
        },
        "unique jewel": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueJewel",
            "stack": False,
        },
        "unique map": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=UniqueMap",
            "stack": False,
        },
        "enchant": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=HelmetEnchant",
            "stack": False,
        },
        "base": {
            "ninja": "https://poe.ninja/api/data/itemoverview?league=%s&type=BaseType",
            "stack": False,
        },
    }


    _SEXTANTS = {
        "awakened": ["Strongbox Corrupted", "Unidentified Map", "Magic Pack Size", "Chaos Monsters", "Alluring", "Abyss", "Alva", "Blight", "Breach", "Einhar", "Essence", "Gloom Shrine", "Cold Monsters", "Fire Monsters", "Lightning Monsters", "Physical Monsters", "Sacred Grove", "Smuggler's Cache", "Hunted Traitors", "Jun", "Legion", "Metamorph", "Mysterious Barrels", "Niko", "Resonating Shrine", "Ritual Altars", "Tormented Graverobber", "Tormented Heretic", "Rogue Exiles", "Beyond", "Oils Tier", "Bodyguards", "Boss Drop Vaal", "Conqueror Map", "Elder Guardian", "Shaper Guardian", "Boss Drop Unique", "Chayula", "Esh", "Tul", "Uul-Netol", "Xoph", "Copy of Beasts", "Delirium Reward", "Runic Monster Markers", "Mysterious Harbinger", "Blue Plants", "Purple Plants", "Yellow Plants", "Contracts Implicit", "Invasion Boss", "Vaal Monsters Items Corrupted", "Splinters Emblems Duplicate", "Reflected", "Flasks Instant", "8 Modifiers", "Map 20% Quality", "Catalysts Duplicate", "Mirror of Delirium", "Convert Monsters", "Gilded Scarab", "Polished Scarab", "Rusted Scarab", "Map Quality to Rarity", "Rare Map Rare Packs", "Ritual Rerolling", "Strongbox Enraged", "Syndicate Intelligence", "Unique Monsters Drop Corrupted", "Soul Gain Prevention", "Mortal/Sacrifice Fragment", "Vaal Soul on Kill"],
        "elevated": ["25% Unidentified Map", "3 Strongboxes Corrupted", "30% Magic Pack Size", "8 Packs Cold Monsters", "8 Packs Fire Monsters", "8 Packs Lightning Monsters", "8 Packs Physical Monsters", "Flasks Instant 8 Packs", "8 Packs Convert Monsters", "Mortal/Sacrifice Fragment 8 Packs", "Soul Gain Prevention 8 Packs", "Vaal Monsters Items 30% Corrupted", "Gloom Shrine +1 Shrine", "35 Mysterious Barrels", "Resonating Shrine +1 Shrine", "2 Abysses", "2 Breaches", "2 Essences", "35% Beyond", "Bodyguards 2 Maps Drop", "Boss Drop 3 Vaal", "Reflected 5 Packs", "Winged Scarab", "Rare Map 5 Rare Packs", "Strongbox Enraged 600%"],
    }

class ALT_GEMS_DATA:
    def __init__(self):
        with open("gems_weights.json", 'r') as file:
            self.gems_weights = json.loads(file.read())
        return

    def get(self, base_name):
        return self.gems_weights(base_name) if base_name in self.gems_weights else {}

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
                alts[res[i].text.strip([" "])] = int(res[i+2].text)
        return alts

    def get_alt_gem(base_name):
        if not base_name in gems_weights:
            gems_weights[base_name] = lookup_alt_gem(base_name)
            with open("gems_weights.json", 'w') as file:
                file.write(json.dumps(gems_weights, indent=4))
        return gems_weights[base_name]