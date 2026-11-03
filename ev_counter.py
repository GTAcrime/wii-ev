# Console window with EV result. Pixel font renderer.
import json
import os
import struct
import sys
import tkinter as tk

# folder of the .exe (or of this script): config.json lives here, the sprite pack and ROMs may too
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(os.path.expanduser("~"), "ev", "ev_log.txt")
LIST_FILE = os.path.join(os.path.expanduser("~"), "ev", "ev_list.txt")
SAVE_DIR = r"C:\Users\HLAY1\Desktop\Ev Pro"   # folder with your .sav files (Emerald, FireRed...); the newest one is used
ROM_DIR = r"C:\Users\HLAY1\Desktop\Ev Pro"    # folder with your .gba ROMs (same games as on the Wii); sprites are read from them
SPRITE_PACK = r"C:\Users\HLAY1\Desktop\Ev Pro\Gen 3 Sprite Pack V1.0"   # folder with Graphics\Pokemon\Front etc.; used first, the ROM is the fallback
SPRITE_ZOOM = 2                  # 2 = 128x128 px, 3 = 192x192 px; 0 = no sprites
WII_IP = "192.168.0.74"                      # IP of your Wii, e.g. "192.168.1.50". Empty = use the mGBA script on this PC
# Used in Wii mode only (same meaning as in ev_licznik.lua):
STAT = "AUTO"                    # "AUTO" or "HP", "ATK", "DEF", "SPE", "SPA", "SPD"
FALLBACK_STAT = "HP"
TARGET = 240
MACHO_BRACE = 181
BASE_YIELD = 1
MAX_GAIN = 12
MENU_LINES = ["EV COUNTER", "1. LIST POKEMON EV (PARTY + BOXES)", "2. TRAINING EV", "PRESS 1 OR 2 (0 = BACK TO MENU)", "IN LIST: UP/DOWN, PGUP/PGDN OR MOUSE WHEEL = SCROLL"]
UPPERCASE = True                 # True = all uppercase
SCALE = 1                        # 1 = game size (small font)
MAX_LINES = 30                   # how many last lines to show
POLL_MS = 500
COL_NEW = "#e6edf3"              # text of the newest line (off-white)
COL_NEW_WRONG = "#ff7b72"        # red color when wrong Pokémon appears
COL_OLD = "#8b949e"              # text of older lines (muted gray)
NUM_NEW = "#f0883e"              # digits in the newest line (orange/gold)
NUM_OLD = "#9e6a03"              # digits in older lines
BG = "#0d1117"                   # dark background
PAD = 10
LINE_GAP = 4                     # gap between lines

# Training plans: when the first stat reaches its target the next one becomes the trained stat.
# Key = species name, value = [[stat, target], ...]. Edit them in config.json next to the app.
PLANS = {"Chansey": [["HP", 240], ["SPD", 240]]}

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
CONFIG_KEYS = ("WII_IP", "SAVE_DIR", "ROM_DIR", "SPRITE_PACK", "SPRITE_ZOOM", "STAT", "FALLBACK_STAT", "TARGET", "MACHO_BRACE", "PLANS")

def load_config():
    """config.json overrides the values above; it is created with the current values on the first start."""
    if not os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({k: globals()[k] for k in CONFIG_KEYS}, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
        return
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        for k in CONFIG_KEYS:
            if k in cfg:
                globals()[k] = cfg[k]
    except (OSError, ValueError) as e:
        print("config.json ignored:", e)

load_config()

GLYPH_ROWS = 13
CAP_TOP = 2
GLYPHS = {
    ' ': '.../.../.../.../.../.../.../.../.../.../.../.../...',
    '!': '..../.#../.#../.#../.#../.#../.#../.#../..../..../.#../..../....',
    '"': '##.##./##.##./.#..#./#..#../....../....../....../....../....../....../....../....../......',
    '#': '....../....../.#.#../.#.#../#####./.#.#../.#.#../#####./.#.#../.#.#../....../....../......',
    '[': '###./#.../#.../#.../#.../#.../#.../#.../#.../#.../#.../#.../###.',
    ']': '###./..#./..#./..#./..#./..#./..#./..#./..#./..#./..#./..#./###.',
    '_': '....../....../....../....../....../....../....../....../....../....../....../....../#####.',
    '$': '....../.###../.#..#./.#..#./.#..#./.###../.#..../####../.#..../####../.#..../....../......',
    '%': '....../###.#./#.#.#./#.##../##.#../..#.../..#.../.#.##./.##.#./#.#.#./#.###./....../......',
    '&': '......./......./..#..../.#.#.../.#.#.../..#..../..#.#../.#.#.../#..#.../#..#.../.##.#../......./.......',
    "'": '##./##./.#./#../.../.../.../.../.../.../.../.../...',
    '(': '.#../#.../#.../#.../#.../#.../#.../#.../#.../#.../#.../#.../.#..',
    ')': '.#../..#./..#./..#./..#./..#./..#./..#./..#./..#./..#./..#./.#..',
    '+': '....../....../....../....../..#.../..#.../#####./..#.../..#.../....../....../....../......',
    ',': '.../.../.../.../.../.../.../.../.../##./##./.#./#..',
    '-': '....../....../....../....../....../....../#####./....../....../....../....../....../......',
    '.': '.../.../.../.../.../.../.../.../.../##./##./.../...',
    '/': '....../....#./....#./...#../...#../..#.../..#.../.#..../.#..../#...../#...../....../......',
    '0': '....../....../.###../#...#./#...#./#...#./#...#./#...#./#...#./#...#./.###../....../......',
    '1': '....../....../.##.../..#.../..#.../..#.../..#.../..#.../..#.../..#.../.###../....../......',
    '2': '....../....../.###../#...#./....#./....#./...#../..#.../.#..../#...../#####./....../......',
    '3': '....../....../.###../#...#./....#./....#./..##../....#./....#./#...#./.###../....../......',
    '4': '....../....../..##../.#.#../#..#../#..#../#..#../#..#../#####./...#../...#../....../......',
    '5': '....../....../#####./#...../#...../#...../####../....#./....#./....#./####../....../......',
    '6': '....../....../.###../#...#./#...../#...../####../#...#./#...#./#...#./.###../....../......',
    '7': '....../....../#####./....#./....#./....#./...#../...#../...#../..#.../..#.../....../......',
    '8': '....../....../.###../#...#./#...#./#...#./.###../#...#./#...#./#...#./.###../....../......',
    '9': '....../....../.###../#...#./#...#./#...#./.####./....#./....#./#...#./.###../....../......',
    ':': '.../.../.../.../##./##./.../.../##./##./.../.../...',
    ';': '.../.../.../.../##./##./.../.../##./##./.#./#../...',
    '<': '....../....../....#./...#../..#.../.#..../#...../#...../.#..../..#.../...#../....#./......',
    '=': '......../......../......../......../......../.#####../......../......../.#####../......../......../......../........',
    '>': '....../....../#...../.#..../..#.../...#../....#./....#./...#../..#.../.#..../#...../......',
    '?': '....../.###../#...#./#...#./....#./...#../..#.../..#.../....../....../..#.../....../......',
    'A': '....../....../.###../#...#./#...#./#...#./#...#./#####./#...#./#...#./#...#./....../......',
    'B': '....../....../####../#...#./#...#./#...#./####../#...#./#...#./#...#./####../....../......',
    'C': '....../....../.###../#...#./#...../#...../#...../#...../#...../#...#./.###../....../......',
    'D': '....../....../####../#...#./#...#./#...#./#...#./#...#./#...#./#...#./####../....../......',
    'E': '....../....../#####./#...../#...../#...../####../#...../#...../#...../#####./....../......',
    'F': '....../....../#####./#...../#...../#...../####../#...../#...../#...../#...../....../......',
    'G': '....../....../.###../#...#./#...../#...../#...../#..##./#...#./#...#./.###../....../......',
    'H': '....../....../#...#./#...#./#...#./#...#./#####./#...#./#...#./#...#./#...#./....../......',
    'I': '....../....../#####./..#.../..#.../..#.../..#.../..#.../..#.../..#.../#####./....../......',
    'J': '....../....../....#./....#./....#./....#./....#./....#./....#./#...#./.###../....../......',
    'K': '....../....../#...#./#..#../#.#.../##..../##..../##..../#.#.../#..#../#...#./....../......',
    'L': '....../....../#...../#...../#...../#...../#...../#...../#...../#...../#####./....../......',
    'M': '....../....../#...#./##.##./##.##./#.#.#./#.#.#./#...#./#...#./#...#./#...#./....../......',
    'N': '....../....../#...#./##..#./##..#./#.#.#./#.#.#./#..##./#..##./#...#./#...#./....../......',
    'O': '....../....../.###../#...#./#...#./#...#./#...#./#...#./#...#./#...#./.###../....../......',
    'P': '....../....../####../#...#./#...#./#...#./#...#./####../#...../#...../#...../....../......',
    'Q': '....../....../.###../#...#./#...#./#...#./#...#./#...#./###.#./#..##./.###.#/....../......',
    'R': '....../....../####../#...#./#...#./#...#./#...#./####../#.#.../#..#../#...#./....../......',
    'S': '....../....../.###../#...#./#...../#...../.###../....#./....#./#...#./.###../....../......',
    'T': '....../....../#####./..#.../..#.../..#.../..#.../..#.../..#.../..#.../..#.../....../......',
    'U': '....../....../#...#./#...#./#...#./#...#./#...#./#...#./#...#./#...#./.###../....../......',
    'V': '....../....../#...#./#...#./#...#./#...#./#...#./.#.#../.#.#../..#.../..#.../....../......',
    'W': '....../....../#...#./#...#./#...#./#...#./#.#.#./#.#.#./##.##./##.##./#...#./....../......',
    'X': '....../....../#...#./#...#./.#.#../.#.#../..#.../.#.#../.#.#../#...#./#...#./....../......',
    'Y': '....../....../#...#./#...#./#...#./.#.#../.#.#../..#.../..#.../..#.../..#.../....../......',
    'Z': '....../....../#####./....#./...#../...#../..#.../.#..../.#..../#...../#####./....../......',
    'a': '....../....../....../....../....../.###../....#./.####./#...#./#...#./.####./....../......',
    'b': '....../....../#...../#...../#...../####../#...#./#...#./#...#./#...#./####../....../......',
    'c': '....../....../....../....../....../.###../#...#./#...../#...../#...#./.###../....../......',
    'd': '....../....../....#./....#./....#./.####./#...#./#...#./#...#./#...#./.####./....../......',
    'e': '....../....../....../....../....../.###../#...#./#####./#...../#...#./.###../....../......',
    'f': '....../....../...##./..#.../..#.../#####./..#.../..#.../..#.../..#.../..#.../....../......',
    'g': '....../....../....../....../....../.###../#...#./#...#./#...#./.####./....#./#...#./.###..',
    'h': '....../....../#...../#...../#...../####../#...#./#...#./#...#./#...#./#...#./....../......',
    'i': '..../..../.#../..../..../.#../.#../.#../.#../.#../.#../..../....',
    'j': '...../...../...#./...../...../...#./...#./...#./...#./...#./...#./#..#./.##..',
    'k': '....../....../#...../#...../#...../#...#./#..#../#.#.../###.../#..#../#...#./....../......',
    'l': '..../..../.#../.#../.#../.#../.#../.#../.#../.#../.#../..../....',
    'm': '....../....../....../....../....../####../#.#.#./#.#.#./#.#.#./#.#.#./#.#.#./....../......',
    'n': '....../....../....../....../....../####../#...#./#...#./#...#./#...#./#...#./....../......',
    'o': '....../....../....../....../....../.###../#...#./#...#./#...#./#...#./.###../....../......',
    'p': '....../....../....../....../....../####../#...#./#...#./#...#./####../#...../#...../#.....',
    'q': '....../....../....../....../....../.####./#...#./#...#./#...#./.####./....#./....#./....#.',
    'r': '...../...../...../...../...../#.##./##.../#..../#..../#..../#..../...../.....',
    's': '....../....../....../....../....../.###../#...#./.#..../..##../#...#./.###../....../......',
    't': '....../....../....../..#.../..#.../#####./..#.../..#.../..#.../..#.../...##./....../......',
    'u': '....../....../....../....../....../#...#./#...#./#...#./#...#./#...#./.####./....../......',
    'v': '....../....../....../....../....../#...#./#...#./#...#./.#.#../.#.#../..#.../....../......',
    'w': '....../....../....../....../....../#.#.#./#.#.#./#.#.#./#.#.#./#.#.#./.#.#../....../......',
    'x': '....../....../....../....../....../#...#./.#.#../..#.../..#.../.#.#../#...#./....../......',
    'y': '....../....../....../....../....../#...#./#...#./#...#./#...#./.####./....#./#...#./.###..',
    'z': '....../....../....../....../....../#####./...#../..#.../.#..../#...../#####./....../......',
    '|': '.../.../.#./.#./.#./.#./.#./.#./.#./.#./.#./.#./...',
}

# Species names by internal Emerald ID
SPECIES_NAMES = {
    1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon", 6: "Charizard",
    7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie", 11: "Metapod", 12: "Butterfree",
    13: "Weedle", 14: "Kakuna", 15: "Beedrill", 16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot", 19: "Rattata",
    20: "Raticate", 21: "Spearow", 22: "Fearow", 23: "Ekans", 24: "Arbok", 25: "Pikachu", 26: "Raichu",
    27: "Sandshrew", 28: "Sandslash", 29: "Nidoran F", 30: "Nidorina", 31: "Nidoqueen", 32: "Nidoran M",
    33: "Nidorino", 34: "Nidoking", 35: "Clefairy", 36: "Clefable", 37: "Vulpix", 38: "Ninetales",
    39: "Jigglypuff", 40: "Wigglytuff", 41: "Zubat", 42: "Golbat", 43: "Oddish", 44: "Gloom",
    45: "Vileplume", 46: "Paras", 47: "Parasect", 48: "Venonat", 49: "Venomoth", 50: "Diglett",
    51: "Dugtrio", 52: "Meowth", 53: "Persian", 54: "Psyduck", 55: "Golduck", 56: "Mankey", 57: "Primeape",
    58: "Growlithe", 59: "Arcanine", 60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath", 63: "Abra",
    64: "Kadabra", 65: "Alakazam", 66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout",
    70: "Weepinbell", 71: "Victreebel", 72: "Tentacool", 73: "Tentacruel", 74: "Geodude", 75: "Graveler",
    76: "Golem", 77: "Ponyta", 78: "Rapidash", 79: "Slowpoke", 80: "Slowbro", 81: "Magnemite",
    82: "Magneton", 83: "Farfetch'd", 84: "Doduo", 85: "Dodrio", 86: "Seel", 87: "Dewgong", 88: "Grimer",
    89: "Muk", 90: "Shellder", 91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar", 95: "Onix",
    96: "Drowzee", 97: "Hypno", 98: "Krabby", 99: "Kingler", 100: "Voltorb", 101: "Electrode",
    102: "Exeggcute", 103: "Exeggutor", 104: "Cubone", 105: "Marowak", 106: "Hitmonlee", 107: "Hitmonchan",
    108: "Lickitung", 109: "Koffing", 110: "Weezing", 111: "Rhyhorn", 112: "Rhydon", 113: "Chansey",
    114: "Tangela", 115: "Kangaskhan", 116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking",
    120: "Staryu", 121: "Starmie", 122: "Mr. Mime", 123: "Scyther", 124: "Jynx", 125: "Electabuzz",
    126: "Magmar", 127: "Pinsir", 128: "Tauros", 129: "Magikarp", 130: "Gyarados", 131: "Lapras",
    132: "Ditto", 133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon", 137: "Porygon",
    138: "Omanyte", 139: "Omastar", 140: "Kabuto", 141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax",
    144: "Articuno", 145: "Zapdos", 146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite",
    150: "Mewtwo", 151: "Mew", 152: "Chikorita", 153: "Bayleef", 154: "Meganium", 155: "Cyndaquil",
    156: "Quilava", 157: "Typhlosion", 158: "Totodile", 159: "Croconaw", 160: "Feraligatr", 161: "Sentret",
    162: "Furret", 163: "Hoothoot", 164: "Noctowl", 165: "Ledyba", 166: "Ledian", 167: "Spinarak",
    168: "Ariados", 169: "Crobat", 170: "Chinchou", 171: "Lanturn", 172: "Pichu", 173: "Cleffa",
    174: "Igglybuff", 175: "Togepi", 176: "Togetic", 177: "Natu", 178: "Xatu", 179: "Mareep", 180: "Flaaffy",
    181: "Ampharos", 182: "Bellossom", 183: "Marill", 184: "Azumarill", 185: "Sudowoodo", 186: "Politoed",
    187: "Hoppip", 188: "Skiploom", 189: "Jumpluff", 190: "Aipom", 191: "Sunkern", 192: "Sunflora",
    193: "Yanma", 194: "Wooper", 195: "Quagsire", 196: "Espeon", 197: "Umbreon", 198: "Murkrow",
    199: "Slowking", 200: "Misdreavus", 201: "Unown", 202: "Wobbuffet", 203: "Girafarig", 204: "Pineco",
    205: "Forretress", 206: "Dunsparce", 207: "Gligar", 208: "Steelix", 209: "Snubbull", 210: "Granbull",
    211: "Qwilfish", 212: "Scizor", 213: "Shuckle", 214: "Heracross", 215: "Sneasel", 216: "Teddiursa",
    217: "Ursaring", 218: "Slugma", 219: "Magcargo", 220: "Swinub", 221: "Piloswine", 222: "Corsola",
    223: "Remoraid", 224: "Octillery", 225: "Delibird", 226: "Mantine", 227: "Skarmory", 228: "Houndour",
    229: "Houndoom", 230: "Kingdra", 231: "Phanpy", 232: "Donphan", 233: "Porygon2", 234: "Stantler",
    235: "Smeargle", 236: "Tyrogue", 237: "Hitmontop", 238: "Smoochum", 239: "Elekid", 240: "Magby",
    241: "Miltank", 242: "Blissey", 243: "Raikou", 244: "Entei", 245: "Suicune", 246: "Larvitar",
    247: "Pupitar", 248: "Tyranitar", 249: "Lugia", 250: "Ho-Oh", 251: "Celebi", 277: "Treecko",
    278: "Grovyle", 279: "Sceptile", 280: "Torchic", 281: "Combusken", 282: "Blaziken", 283: "Mudkip",
    284: "Marshtomp", 285: "Swampert", 286: "Poochyena", 287: "Mightyena", 288: "Zigzagoon", 289: "Linoone",
    290: "Wurmple", 291: "Silcoon", 292: "Beautifly", 293: "Cascoon", 294: "Dustox", 295: "Lotad",
    296: "Lombre", 297: "Ludicolo", 298: "Seedot", 299: "Nuzleaf", 300: "Shiftry", 301: "Nincada",
    302: "Ninjask", 303: "Shedinja", 304: "Taillow", 305: "Swellow", 306: "Shroomish", 307: "Breloom",
    308: "Spinda", 309: "Wingull", 310: "Pelipper", 311: "Surskit", 312: "Masquerain", 313: "Wailmer",
    314: "Wailord", 315: "Skitty", 316: "Delcatty", 317: "Kecleon", 318: "Baltoy", 319: "Claydol",
    320: "Nosepass", 321: "Torkoal", 322: "Sableye", 323: "Barboach", 324: "Whiscash", 325: "Luvdisc",
    326: "Corphish", 327: "Crawdaunt", 328: "Feebas", 329: "Milotic", 330: "Carvanha", 331: "Sharpedo",
    332: "Trapinch", 333: "Vibrava", 334: "Flygon", 335: "Makuhita", 336: "Hariyama", 337: "Electrike",
    338: "Manectric", 339: "Numel", 340: "Camerupt", 341: "Spheal", 342: "Sealeo", 343: "Walrein",
    344: "Cacnea", 345: "Cacturne", 346: "Snorunt", 347: "Glalie", 348: "Lunatone", 349: "Solrock",
    350: "Azurill", 351: "Spoink", 352: "Grumpig", 353: "Plusle", 354: "Minun", 355: "Mawile",
    356: "Meditite", 357: "Medicham", 358: "Swablu", 359: "Altaria", 360: "Wynaut", 361: "Duskull",
    362: "Dusclops", 363: "Roselia", 364: "Slakoth", 365: "Vigoroth", 366: "Slaking", 367: "Gulpin",
    368: "Swalot", 369: "Tropius", 370: "Whismur", 371: "Loudred", 372: "Exploud", 373: "Clamperl",
    374: "Huntail", 375: "Gorebyss", 376: "Absol", 377: "Shuppet", 378: "Banette", 379: "Seviper",
    380: "Zangoose", 381: "Relicanth", 382: "Aron", 383: "Lairon", 384: "Aggron", 385: "Castform",
    386: "Volbeat", 387: "Illumise", 388: "Lileep", 389: "Cradily", 390: "Anorith", 391: "Armaldo",
    392: "Ralts", 393: "Kirlia", 394: "Gardevoir", 395: "Bagon", 396: "Shelgon", 397: "Salamence",
    398: "Beldum", 399: "Metang", 400: "Metagross", 401: "Regirock", 402: "Regice", 403: "Registeel",
    404: "Kyogre", 405: "Groudon", 406: "Rayquaza", 407: "Latias", 408: "Latios", 409: "Jirachi",
    410: "Deoxys", 411: "Chimecho",
}

STAT_NAMES = ("HP", "ATK", "DEF", "SPE", "SPA", "SPD")
ORDERS = ["GAEM","GAME","GEAM","GEMA","GMAE","GMEA","AGEM","AGME","AEGM","AEMG","AMGE","AMEG","EGAM","EGMA","EAGM","EAMG","EMGA","EMAG","MGAE","MGEA","MAGE","MAEG","MEGA","MEAG"]
# Save layouts: checksum sizes of the sectors and where the party lives inside SaveBlock1
FORMATS = (
    ("EMERALD", {0: 3884, 13: 2000}, 0x234, 0x238),
    ("FIRERED/LEAFGREEN", {0: 3876, 4: 3816, 13: 2000}, 0x34, 0x38),
)

def sector_ok(sec, sid, sizes):
    size = sizes.get(sid, 3968)
    total = sum(struct.unpack_from("<%dI" % (size // 4), sec, 0)) & 0xFFFFFFFF
    return ((total + (total >> 16)) & 0xFFFF) == struct.unpack_from("<H", sec, 0xFF6)[0]

def load_slot(data, first, sizes):
    secs, counter = {}, 0
    for i in range(14):
        sec = data[(first + i) * 4096:(first + i + 1) * 4096]
        sid, _, sig, cnt = struct.unpack_from("<HHII", sec, 0xFF4)
        if sig != 0x08012025 or sid > 13 or not sector_ok(sec, sid, sizes):
            return None
        secs[sid] = sec
        counter = cnt
    return (counter, secs) if len(secs) == 14 else None

def decode_mon(b):
    pid, otid = struct.unpack_from("<II", b, 0)
    if pid == 0 and otid == 0:
        return None
    key = pid ^ otid
    dec = [struct.unpack_from("<I", b, 0x20 + 4 * k)[0] ^ key for k in range(12)]
    chk = sum((w & 0xFFFF) + (w >> 16) for w in dec) & 0xFFFF
    if chk != struct.unpack_from("<H", b, 0x1C)[0]:
        return "bad"
    def w(letter, n):
        return dec[3 * ORDERS[pid % 24].index(letter) + n]
    g0, e0, e1 = w("G", 0), w("E", 0), w("E", 1)
    evs = (e0 & 255, (e0 >> 8) & 255, (e0 >> 16) & 255, e0 >> 24, e1 & 255, (e1 >> 8) & 255)
    return g0 & 0xFFFF, (w("M", 1) >> 30) & 1, evs, g0 >> 16, pid, otid

def gen3_text(raw):
    """Gen 3 character codes (letters, digits, a few symbols) to str; 0xFF ends the text."""
    out = []
    for c in raw:
        if c == 0xFF:
            break
        if 0xBB <= c <= 0xD4:
            out.append(chr(ord("A") + c - 0xBB))
        elif 0xD5 <= c <= 0xEE:
            out.append(chr(ord("a") + c - 0xD5))
        elif 0xA1 <= c <= 0xAA:
            out.append(chr(ord("0") + c - 0xA1))
        else:
            out.append({0x00: " ", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-"}.get(c, "?"))
    return "".join(out)

def plan_for(name):
    """[(stat, target), ...] for this species from PLANS, or None."""
    for key, steps in PLANS.items():
        if key.lower() == name.lower():
            plan = [(st, int(tg)) for st, tg in steps if st in STAT_NAMES]
            return plan or None
    return None

def mon_line(n, mon):
    if mon == "bad":
        return "%d. BAD DATA (CHECKSUM MISMATCH)" % n
    species, egg, evs = mon[:3]
    name = SPECIES_NAMES.get(species, "Species #%d" % species)
    return "%d. %s%s | %s | TOTAL %d/510" % (n, name, " (EGG)" if egg else "",
        " ".join("%s %d" % (s, v) for s, v in zip(STAT_NAMES, evs)), sum(evs))

def read_save(path):
    with open(path, "rb") as f:
        data = f.read(0x20000)
    candidates = []
    for name, sizes, count_off, party_off in FORMATS:
        slots = [x for x in (load_slot(data, 0, sizes), load_slot(data, 14, sizes)) if x]
        if not slots:
            continue
        secs = max(slots, key=lambda x: x[0])[1]
        sb1 = b"".join(secs[i][:3968] for i in (1, 2, 3, 4))
        first = decode_mon(sb1[party_off:party_off + 100])
        plausible = 1 <= sb1[count_off] <= 6 and first not in (None, "bad")
        candidates.append((plausible, secs, sb1, count_off, party_off))
    if not candidates:
        return ["NO VALID SAVE FOUND IN FILE"]
    plausible, secs, sb1, count_off, party_off = next((c for c in candidates if c[0]), candidates[0])
    storage = b"".join(secs[i][:3968] for i in range(5, 13)) + secs[13][:2000]
    lines = ["--- PARTY ---"]
    count = min(sb1[count_off], 6)
    for i in range(count):
        mon = decode_mon(sb1[party_off + 100 * i:party_off + 100 * (i + 1)])
        if mon:
            lines.append(mon_line(i + 1, mon))
    if count == 0:
        lines.append("NO POKEMON IN PARTY")
    for box in range(14):
        header = False
        for slot in range(30):
            off = 4 + (box * 30 + slot) * 80
            mon = decode_mon(storage[off:off + 80])
            if mon:
                if not header:
                    lines.append("--- BOX %d ---" % (box + 1))
                    header = True
                lines.append(mon_line(slot + 1, mon))
    return lines

# ---------- Wii link: live memory mirror streamed by the patched mGBA on the Wii ----------
import math
import socket
import threading
import time

WII_PORT = 5555
WII_PORTS = 10                   # the Wii tries 5555..5564, whichever is free
ROM_MARKER = 0xFFFFFFF0          # pseudo address: payload = ROM address of gBaseStats
STORAGE_PTR = 0x03005D94
STAT_SHIFT = {"HP": 0, "ATK": 2, "DEF": 4, "SPE": 6, "SPA": 8, "SPD": 10}
NO_BOXES = "--- BOXES NOT AVAILABLE ---"

class WiiMirror:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.ewram = bytearray(0x40000)
        self.iwram = bytearray(0x8000)
        self.rom = bytearray(0x3000)
        self.header = bytearray(32)
        self.rom_base = None
        self.regions = ((0x02000000, self.ewram), (0x03000000, self.iwram), (0x080000A0, self.header))
        self.chunks_seen = set()
        self.chunks_total = (0x40000 + 0x8000 + 0x3000) // 4096
        self.status = "CONNECTING TO WII " + host + "..."
        threading.Thread(target=self.run, daemon=True).start()

    @property
    def complete(self):
        return len(self.chunks_seen) >= self.chunks_total

    def store(self, addr, data):
        if addr == ROM_MARKER:
            self.rom_base = struct.unpack("<I", data)[0] or None
            return
        if self.rom_base and self.rom_base <= addr and addr + len(data) <= self.rom_base + len(self.rom):
            self.rom[addr - self.rom_base:addr - self.rom_base + len(data)] = data
            self.chunks_seen.add(addr)
            return
        for base, buf in self.regions:
            if base <= addr and addr + len(data) <= base + len(buf):
                buf[addr - base:addr - base + len(data)] = data
                if len(data) == 4096:
                    self.chunks_seen.add(addr)
                return

    def get(self, addr, n):
        if self.rom_base and self.rom_base <= addr and addr + n <= self.rom_base + len(self.rom):
            return bytes(self.rom[addr - self.rom_base:addr - self.rom_base + n])
        for base, buf in self.regions:
            if base <= addr and addr + n <= base + len(buf):
                return bytes(buf[addr - base:addr - base + n])
        return bytes(n)

    def run(self):
        while True:
            found = False
            for port in range(self.port, self.port + WII_PORTS):
                try:
                    sock = socket.create_connection((self.host, port), timeout=2)
                except OSError:
                    continue
                try:
                    # the Wii may still be busy with the previous (dead) connection and only reach this one
                    # when that times out, so wait long instead of giving up after a few seconds
                    self.status = "WAITING FOR WII %s:%d ..." % (self.host, port)
                    sock.settimeout(30)
                    first = sock.recv(65536)
                except OSError:
                    sock.close()
                    continue
                if not first:
                    sock.close()
                    continue
                found = True
                self.status = "CONNECTED TO WII %s:%d" % (self.host, port)
                try:
                    sock.settimeout(10)
                    self.pump(sock, first)
                except OSError:
                    pass
                sock.close()
                break
            if not found:
                self.status = "NO CONNECTION TO WII " + self.host + ". RETRYING..."
            time.sleep(2)

    def pump(self, sock, buf=b""):
        while True:
            while len(buf) >= 12:
                if buf[:4] != b"EVM1":
                    raise OSError("bad stream")
                addr, length = struct.unpack(">II", buf[4:12])
                if len(buf) < 12 + length:
                    break
                self.store(addr, buf[12:12 + length])
                buf = buf[12 + length:]
            data = sock.recv(65536)
            if not data:
                raise OSError("closed")
            buf += data

def game_addrs(mem):
    """(gPlayerParty, gEnemyParty) for the game running on the Wii, or None until the ROM header arrives."""
    code = mem.get(0x080000AC, 4)
    if code in (b"BPRE", b"BPGE"):      # FireRed / LeafGreen
        return 0x02024284, 0x0202402C
    if code == b"BPEE":                 # Emerald
        return 0x020244EC, 0x02024744
    return None

class WiiTrainer:
    """Port of the training logic from ev_licznik.lua, running on the mirrored Wii memory."""
    def __init__(self, mem):
        self.mem = mem
        self.log = []
        self.last_val = self.last_pid = self.last_stat = self.last_key = None
        self.measured = None
        self.last_enemy = None
        self.active_stat = FALLBACK_STAT
        self.brace = False
        self.bad_logged = self.enemy_bad_logged = self.rom_warned = False
        self.enemy_sprite = None        # (species, shiny) of the last enemy seen
        self.view = None                # what the training window shows for slot 1 (None = nothing yet)
        self.history = []               # encountered enemies, newest first
        self.rev = 0                    # grows whenever view or history change, so the window knows to redraw

    def set_view(self, view):
        if view != self.view:
            self.view = view
            self.rev += 1

    def say(self, msg):
        self.log.append(msg)
        del self.log[:-200]

    def step(self):
        addrs = game_addrs(self.mem)
        if addrs is None:
            return
        self.party, self.enemy_addr = addrs
        self.report()
        self.enemy()

    def report(self):
        raw = self.mem.get(self.party, 100)
        mon = decode_mon(raw)
        if mon is None:
            self.set_view(None)
            return
        if mon == "bad":
            if not self.bad_logged:
                self.say("Read skipped: slot 1 checksum mismatch. Waiting.")
                self.bad_logged = True
            return
        self.bad_logged = False
        species, egg, evs, item, pid = mon[:5]
        s = dict(zip(STAT_NAMES, evs))
        stat = STAT
        target = TARGET
        name = SPECIES_NAMES.get(species, "Species #%d" % species)
        plan = plan_for(name)
        if plan:
            stat, target = plan[-1]                      # all steps done: stay on the last one
            for st, tg in plan:
                if s[st] < tg:
                    stat, target = st, tg
                    break
        elif stat == "AUTO":
            stat, best = FALLBACK_STAT, 0
            for k in STAT_NAMES:
                if s[k] > best:
                    stat, best = k, s[k]
        if self.last_stat != stat:
            self.measured, self.last_val = None, None
        self.last_stat = self.active_stat = stat
        val = s[stat]
        total = sum(evs)
        brace = item == MACHO_BRACE
        self.brace = brace
        if self.last_pid != pid:
            self.measured, self.last_val = None, None
        self.last_pid = pid
        if self.last_val is not None and val > self.last_val and val - self.last_val <= MAX_GAIN:
            self.measured = val - self.last_val
        changed = val != self.last_val
        self.last_val = val
        missing = min(target, val + (510 - total)) - val
        if self.measured:
            gain, src = self.measured, "measured"
        else:
            gain, src = BASE_YIELD * (2 if brace else 1), "assumed"
        level = raw[0x54]
        stats = struct.unpack_from("<6H", raw, 0x58)         # max HP, ATK, DEF, SPE, SPA, SPD (same order as the EVs)
        shiny = ((mon[5] & 0xFFFF) ^ (mon[5] >> 16) ^ (mon[4] & 0xFFFF) ^ (mon[4] >> 16)) < 8
        ot = gen3_text(raw[0x14:0x1B])
        self.set_view(dict(pid=pid, ot=ot, tid=mon[5] & 0xFFFF, target=target,
                           plan=tuple((st, tg, s[st]) for st, tg in plan) if plan else None, species=species, egg=bool(egg), shiny=shiny, level=level, stats=stats, evs=evs, stat=stat,
                           val=val, total=total, brace=brace, missing=max(missing, 0), gain=gain,
                           battles=math.ceil(missing / gain) if missing > 0 else 0))
        key = (stat, val, brace, pid)
        if key == self.last_key and not changed:
            return
        self.last_key = key
        head = "Slot 1 (%s): %s %d/%d" % (name, stat, val, target)
        if missing <= 0:
            if total >= 510 and val < target:
                msg = head + " | Limit 510 reached, no more EVs"
            else:
                msg = head + " | TARGET REACHED!"
        else:
            msg = "%s, missing %d, Macho Brace %s, +%d per KO (%s) -> %d battles left" % (
                head, missing, "YES" if brace else "NO", gain, src, math.ceil(missing / gain))
        self.say(msg)

    def enemy(self):
        raw = self.mem.get(self.enemy_addr, 100)
        pid, otid = struct.unpack_from("<II", raw, 0)
        if (pid == 0 and otid == 0) or pid == self.last_enemy:
            return
        base = self.mem.rom_base
        if base is None or self.mem.get(base + 28, 6) != bytes((45, 49, 49, 45, 65, 65)):
            if self.mem.complete and not self.rom_warned:
                self.rom_warned = True
                self.say("gBaseStats address mismatch - cannot rate enemies.")
            return
        mon = decode_mon(raw)
        if mon == "bad":
            if not self.enemy_bad_logged:
                self.say("Enemy read skipped: checksum mismatch. Waiting.")
                self.enemy_bad_logged = True
            return
        self.enemy_bad_logged = False
        species = mon[0]
        if species == 0 or species > 411:
            return
        self.last_enemy = pid
        shiny = ((otid & 0xFFFF) ^ (otid >> 16) ^ (pid & 0xFFFF) ^ (pid >> 16)) < 8
        self.enemy_sprite = (species, shiny)
        shift = STAT_SHIFT[self.active_stat]
        packed = struct.unpack_from("<H", self.mem.get(base + species * 28 + 0x0A, 2))[0]
        y = (packed >> shift) & 3
        if self.brace:
            y *= 2
        name = SPECIES_NAMES.get(species, "Species #%d" % species)
        self.history.insert(0, dict(species=species, shiny=shiny, name=name, y=y, stat=self.active_stat, good=y > 0))
        del self.history[60:]
        self.rev += 1
        self.say("Enemy: %s (+%d %s) %s" % (name, y, self.active_stat, "GOOD" if y > 0 else "[WRONG]"))

def scan_boxes(mem, ptr, need_mon):
    if ptr % 4 or ptr < 0x02000000 or ptr + 33744 > 0x02040000:
        return None
    off = ptr - 0x02000000 + 4
    found = []
    for i in range(420):
        mon = decode_mon(bytes(mem.ewram[off + 80 * i:off + 80 * i + 80]))
        if mon is None:
            continue
        if mon == "bad":
            return None
        found.append((i // 30, i % 30, mon))
    if need_mon and not found:
        return None
    return found

class BoxFinder:
    def __init__(self, mem):
        self.mem, self.at, self.next_try = mem, None, 0

    def find(self):
        mem = self.mem
        if not mem.complete:
            return None
        if self.at is not None:
            found = scan_boxes(mem, struct.unpack_from("<I", mem.iwram, self.at)[0], False)
            if found is not None:
                return found
            self.at = None
        if time.time() < self.next_try:
            return None
        cand = [STORAGE_PTR - 0x03000000]
        for a in range(0, 0x8000, 4):
            if a not in cand:
                cand.append(a)
        seen = set()
        for a in cand:
            ptr = struct.unpack_from("<I", mem.iwram, a)[0]
            if ptr in seen:
                continue
            seen.add(ptr)
            found = scan_boxes(mem, ptr, a != STORAGE_PTR - 0x03000000)
            if found is not None:
                self.at = a
                return found
        self.next_try = time.time() + 10
        return None

def wii_list_lines(mem, finder, save_lines):
    addrs = game_addrs(mem)
    if addrs is None:
        return ["WAITING FOR GAME DATA FROM WII..."]
    lines = ["--- PARTY ---"]
    count = 0
    for i in range(6):
        mon = decode_mon(mem.get(addrs[0] + 100 * i, 100))
        if mon is not None:
            lines.append(mon_line(i + 1, mon))
            count += 1
    if count == 0:
        lines.append("NO POKEMON IN PARTY")
    boxes = finder.find()
    if boxes is None:
        lines.append(NO_BOXES)
    else:
        last = -1
        for box, slot, mon in boxes:
            if box != last:
                lines.append("--- BOX %d ---" % (box + 1))
                last = box
            lines.append(mon_line(slot + 1, mon))
    return merge_save_boxes(lines, save_lines)

def merge_save_boxes(lines, save):
    if NO_BOXES in lines and save:
        idx = [i for i, l in enumerate(save) if l.startswith("--- BOX ")]
        if idx:
            return [l for l in lines if l != NO_BOXES] + ["(BOXES FROM SAVE FILE)"] + save[idx[0]:]
    return lines


# ---------- Sprites read straight from your own ROM ----------
import re

def lz77(d, off):
    """GBA BIOS LZ77 (type 0x10) decompression."""
    hdr = struct.unpack_from("<I", d, off)[0]
    if hdr & 0xFF != 0x10:
        raise ValueError("not LZ77 data")
    size = hdr >> 8
    out = bytearray()
    p = off + 4
    while len(out) < size:
        flags = d[p]
        p += 1
        for i in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> i):
                b0, b1 = d[p], d[p + 1]
                p += 2
                disp = ((b0 & 15) << 8 | b1) + 1
                for _ in range((b0 >> 4) + 3):
                    out.append(out[-disp])
            else:
                out.append(d[p])
                p += 1
    return bytes(out[:size])

def _entry_ok(rom, base, i, kind, tagbase):
    """Check table entry i: pointer to LZ77 data, plus size/tag fields typical for the table kind."""
    off = base + 8 * i
    if off + 8 > len(rom):
        return False
    ptr, a, b = struct.unpack_from("<IHH", rom, off)
    if not 0x08000000 <= ptr < 0x08000000 + len(rom) - 8:
        return False
    if rom[ptr - 0x08000000] != 0x10:
        return False
    if kind == "pic":
        return a == 0x800 and b == i
    return a == tagbase + i and b == 0

def _run_length(rom, base, kind, tagbase=0):
    n = 0
    while _entry_ok(rom, base, n, kind, tagbase):
        n += 1
    return n

def find_sprite_tables(rom):
    """Locate (front pics, normal palettes, shiny palettes) tables by their structure."""
    pic = re.compile(b"\x00\x08\x00\x00....\x00\x08\x01\x00", re.S)
    fronts = [m.start() - 4 for m in pic.finditer(rom) if (m.start() - 4) % 4 == 0]
    fronts = [b for b in fronts if b >= 0 and _run_length(rom, b, "pic") >= 300]
    if not fronts:
        return None
    front = min(fronts)            # the front table comes before the back table in both games

    def pal_table(tagbase):
        pat = re.compile(b"....".join(struct.pack("<HH", tagbase + i, 0) for i in range(3)), re.S)
        cands = [m.start() - 4 for m in pat.finditer(rom) if (m.start() - 4) % 4 == 0 and m.start() >= 4]
        cands = [b for b in cands if _run_length(rom, b, "pal", tagbase) >= 300]
        return min(cands) if cands else None

    normal = pal_table(0)
    shiny = None
    for tagbase in (500, 5000):
        shiny = pal_table(tagbase)
        if shiny is not None:
            break
    if normal is None:
        return None
    return front, normal, shiny

rom_cache = {}      # (game code, version) -> (rom bytes, tables, path) or None
POKE_CODES = (b"BPE", b"BPR", b"BPG", b"AXV", b"AXP")     # Emerald, FireRed, LeafGreen, Ruby, Sapphire

def list_roms():
    """[(path, game code, version)] of the .gba files in ROM_DIR, or None if the folder cannot be read."""
    here = APP_DIR
    dirs = [ROM_DIR, here, os.getcwd(), os.path.join(os.path.expanduser("~"), "Desktop", "Wii ev")]
    out, seen, readable = [], set(), False
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        readable = True
        for f in names:
            path = os.path.join(d, f)
            if not f.lower().endswith(".gba") or os.path.normcase(path) in seen:
                continue
            seen.add(os.path.normcase(path))
            try:
                with open(path, "rb") as fh:
                    head = fh.read(0xC0)
            except OSError:
                continue
            if len(head) >= 0xC0:
                out.append((path, head[0xAC:0xB0], head[0xBC]))
    return out if readable else None

def load_rom(code, version):
    """Best ROM for this game: same code and version, else same code, else any Gen 3 Pokemon ROM
    (all of them share the species numbering and the sprites)."""
    key = (code, version)
    if key in rom_cache:
        return rom_cache[key]
    roms = list_roms() or []
    order = [r for r in roms if r[1] == code and r[2] == version]
    order += [r for r in roms if r[1] == code and r[2] != version]
    order += [r for r in roms if r[1] != code and r[1][:3] in POKE_CODES]
    for path, _, _ in order:
        try:
            with open(path, "rb") as fh:
                rom = fh.read()
        except OSError:
            continue
        tables = find_sprite_tables(rom)
        if tables:
            rom_cache[key] = (rom, tables, path)
            return rom_cache[key]
    return None         # not cached: you can drop a ROM into ROM_DIR later

def sprite_problem(code, version):
    """One line saying why no sprite can be shown."""
    game = "%s REV %d" % (code.decode("ascii", "replace"), version)
    roms = list_roms()
    if roms is None:
        return "NO SPRITE: ROM_DIR NOT FOUND: " + ROM_DIR
    if not roms:
        return "NO SPRITE: NO .GBA FILE IN " + ROM_DIR + " (COPY YOUR " + game + " ROM THERE)"
    found = ", ".join("%s (%s REV %d)" % (os.path.basename(p), c.decode("ascii", "replace"), v) for p, c, v in roms)
    return "NO SPRITE: NO USABLE POKEMON ROM FOR " + game + ". FOUND: " + found

pack_cache = {}

def find_pack():
    """Folder of the Gen 3 sprite pack (the one that contains Graphics/Pokemon/Front), or None."""
    if "dir" in pack_cache:
        return pack_cache["dir"]
    here = APP_DIR
    roots = [SPRITE_PACK, ROM_DIR, here, os.getcwd(), os.path.join(os.path.expanduser("~"), "Desktop", "Wii ev")]
    for root_dir in roots:
        try:
            subs = [root_dir] + [os.path.join(root_dir, n) for n in sorted(os.listdir(root_dir))]
        except OSError:
            continue
        for d in subs:
            if os.path.isdir(os.path.join(d, "Graphics", "Pokemon", "Front")):
                pack_cache["dir"] = os.path.join(d, "Graphics", "Pokemon")
                return pack_cache["dir"]
    return None                # not cached: the pack may be copied there later

def pack_file(species, shiny):
    """PNG of this species from the sprite pack (front, shiny if it exists), or None."""
    base = find_pack()
    name = SPECIES_NAMES.get(species)
    if not base or not name:
        return None
    stem = {"Nidoran F": "NIDORANfE", "Nidoran M": "NIDORANmA"}.get(name) or re.sub(r"[^A-Z0-9]", "", name.upper())
    for folder in (("Front shiny", "Front") if shiny else ("Front",)):
        path = os.path.join(base, folder, stem + ".png")
        if os.path.isfile(path):
            return path
    return None

def icon_file(species):
    base = find_pack()
    name = SPECIES_NAMES.get(species)
    if not base or not name:
        return None
    stem = {"Nidoran F": "NIDORANfE", "Nidoran M": "NIDORANmA"}.get(name) or re.sub(r"[^A-Z0-9]", "", name.upper())
    path = os.path.join(base, "Icons", stem + ".png")
    return path if os.path.isfile(path) else None

def sprite_rows(code, version, species, shiny):
    """64x64 sprite as rows of '#rrggbb' (None = transparent), or None if it cannot be built."""
    loaded = load_rom(code, version)
    if not loaded or not (0 < species < 440):
        return None
    rom, (front, normal, shiny_tbl), _path = loaded
    use_shiny = bool(shiny and shiny_tbl is not None)
    try:
        if not _entry_ok(rom, front, species, "pic", 0):
            return None
        px = lz77(rom, struct.unpack_from("<I", rom, front + 8 * species)[0] - 0x08000000)[:2048]
        ptr = struct.unpack_from("<I", rom, (shiny_tbl if use_shiny else normal) + 8 * species)[0]
        pal = lz77(rom, ptr - 0x08000000)[:32]
    except (ValueError, IndexError, struct.error):
        return None
    if len(px) < 2048 or len(pal) < 32:
        return None
    colors = []
    for i in range(16):
        c = struct.unpack_from("<H", pal, 2 * i)[0]
        colors.append("#%02x%02x%02x" % ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31))
    rows = [[None] * 64 for _ in range(64)]
    for t in range(64):                       # 8x8 grid of 8x8 tiles, 4 bits per pixel
        tx, ty = t % 8, t // 8
        for y in range(8):
            for x in range(4):
                byte = px[t * 32 + y * 4 + x]
                for k, idx in enumerate((byte & 15, byte >> 4)):
                    if idx:
                        rows[ty * 8 + y][tx * 8 + x * 2 + k] = colors[idx]
    return rows

wii = wii_trainer = wii_finder = None
if WII_IP:
    wii = WiiMirror(WII_IP, WII_PORT)
    wii_trainer = WiiTrainer(wii)
    wii_finder = BoxFinder(wii)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

root = tk.Tk()
root.title("EV Counter")
root.configure(bg=BG)
root.geometry("820x460")
root.attributes("-topmost", True)
canvas = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)

crash_count = [0]
def report_error(exc, val, tb):
    """A windowed .exe has no console: write errors to ~/ev/crash.txt instead."""
    import traceback
    crash_count[0] += 1
    if crash_count[0] <= 20:
        try:
            with open(os.path.join(os.path.dirname(LOG_FILE), "crash.txt"), "a", encoding="utf-8") as f:
                f.write("".join(traceback.format_exception(exc, val, tb)) + "\n")
        except OSError:
            pass
root.report_callback_exception = report_error

images = {}
shown = []
scroll = 0
cursor_id = None
cursor_on = True

def glyph(ch):
    g = GLYPHS.get(ch) or GLYPHS.get("?")
    return g.split("/")

def char_w(ch):
    return len(glyph(ch)[0]) * SCALE

def glyph_image(ch, color):
    key = (ch, color)
    if key not in images:
        rows = glyph(ch)
        img = tk.PhotoImage(width=len(rows[0]), height=len(rows))
        data = " ".join("{" + " ".join(color if c == "#" else BG for c in r) + "}" for r in rows)
        img.put(data)
        if SCALE > 1:
            img = img.zoom(SCALE, SCALE)
        images[key] = img
    return images[key]

sprite_images = {}

sprite_reported = set()

def current_sprite():
    """PhotoImage of the last enemy (training view, Wii mode), or None."""
    if not (wii and wii_trainer and SPRITE_ZOOM > 0 and mode == "training" and wii_trainer.enemy_sprite):
        return None
    species, shiny = wii_trainer.enemy_sprite
    code, version = wii.get(0x080000AC, 4), wii.get(0x080000BC, 1)[0]
    key = (code, version, species, shiny)
    if key not in sprite_images:
        img = None
        try:
            png = pack_file(species, shiny)
            rows = None if png else sprite_rows(code, version, species, shiny)
            if png:                                # pack PNGs are 128x128 = zoom 2 of the 64x64 ROM sprite
                img = tk.PhotoImage(file=png)
                if SPRITE_ZOOM != 2:
                    img = img.zoom(SPRITE_ZOOM, SPRITE_ZOOM).subsample(2, 2)
            elif rows is None:
                if load_rom(code, version) is None and (code, version) not in sprite_reported:
                    sprite_reported.add((code, version))
                    wii_trainer.say("NO SPRITE: PACK NOT FOUND (" + SPRITE_PACK + ") AND " + sprite_problem(code, version)[11:])
            else:
                img = tk.PhotoImage(width=64, height=64)
                img.put(" ".join("{" + " ".join(c or BG for c in r) + "}" for r in rows))
                img = img.zoom(SPRITE_ZOOM, SPRITE_ZOOM)
        except Exception as e:
            img = None
            if "error" not in sprite_reported:
                sprite_reported.add("error")
                wii_trainer.say("SPRITE ERROR: " + str(e))
        sprite_images[key] = img
    return sprite_images[key]

def layout(lines, width, all_new=False):
    out = []
    maxw = width - 2 * PAD
    for idx, line in enumerate(lines):
        is_new = all_new or idx == len(lines) - 1
        
        # Wybór koloru: jeśli nowa linia zawiera [WRONG], dajemy czerwony, w przeciwnym razie standardowy
        if is_new:
            base = COL_NEW_WRONG if "[WRONG]" in line else COL_NEW
            numc = NUM_NEW
        else:
            base = COL_OLD
            numc = NUM_OLD

        s = "> " + (line.upper() if UPPERCASE else line)
        row, w, last_space = [], 0, -1
        for ch in s:
            cell = (ch, numc if ch.isdigit() else base)
            cw = char_w(ch)
            if w + cw > maxw and row:
                if last_space > 0:
                    rest = row[last_space + 1:]
                    out.append(row[:last_space])
                    row = rest
                else:
                    out.append(row)
                    row = []
                w = sum(char_w(c[0]) for c in row)
                last_space = -1
            row.append(cell)
            w += cw
            if ch == " ":
                last_space = len(row) - 1
        out.append(row)
    return out

def redraw(_event=None):
    global cursor_id, scroll
    w, h = canvas.winfo_width(), canvas.winfo_height()
    if w < 60:
        return
    canvas.delete("all")
    if wii and mode == "training":
        draw_dashboard(w, h)
        return
    sprite = current_sprite()
    sprite_w = (sprite.width() + PAD) if sprite else 0
    if sprite:
        canvas.create_image(w - PAD, PAD, image=sprite, anchor="ne")
    rows = layout(shown, w - sprite_w, mode != "training") + [[(">", COL_OLD), (" ", COL_OLD)]]
    line_h = (GLYPH_ROWS + LINE_GAP) * SCALE
    total = len(rows) * line_h
    if mode == "list":
        scroll = max(0, min(scroll, (total + 2 * PAD - h + line_h - 1) // line_h))
        y = PAD - scroll * line_h
    else:
        y = PAD if total + 2 * PAD <= h else h - PAD - total
    x = PAD
    cy = y
    for row in rows:
        x = PAD
        cy = y
        if y + line_h < 0 or y > h:
            x += sum(char_w(ch) for ch, _ in row)
        else:
            for ch, color in row:
                canvas.create_image(x, y, image=glyph_image(ch, color), anchor="nw")
                x += char_w(ch)
        y += line_h
    cursor_id = canvas.create_rectangle(
        x + SCALE, cy + CAP_TOP * SCALE, x + 2 * SCALE, cy + (CAP_TOP + 9) * SCALE,
        fill=COL_NEW, width=0, state="normal" if cursor_on else "hidden")

COL_GOOD = "#7ee787"             # EV bar and GOOD marks
COL_WRONG_OLD = "#8a4640"        # older WRONG rows
COL_FRAME = "#30363d"            # bar outline, divider
COL_FLASH = "#ffd33d"            # bar color for a moment after EVs are gained
anim = {"key": None, "shown": 0.0, "last": None, "flash": 0, "pop": None}   # state of the animated bar
LEFT_W = 330                     # width of the left column (current Pokemon)
ROW_H = 36                       # height of one encounter row
ICON_PX = 32

def text_w(s):
    return sum(char_w(ch) for ch in s)

def draw_text(x, y, s, color, numcolor=None):
    """Pixel-font text at x, y. Returns the x after the last character."""
    s = s.upper() if UPPERCASE else s
    for ch in s:
        canvas.create_image(x, y, image=glyph_image(ch, numcolor if numcolor and ch.isdigit() else color), anchor="nw")
        x += char_w(ch)
    return x

png_images = {}

def png_image(path, kind):
    """PhotoImage of a pack PNG. kind 'front' = sprite at SPRITE_ZOOM, 'icon' = left frame of the icon sheet, 32x32."""
    key = (path, kind)
    if key not in png_images:
        try:
            img = tk.PhotoImage(file=path)
            if kind == "front":
                if SPRITE_ZOOM != 2:
                    img = img.zoom(SPRITE_ZOOM, SPRITE_ZOOM).subsample(2, 2)
            else:
                frame = tk.PhotoImage(width=64, height=64)
                frame.tk.call(str(frame), "copy", str(img), "-from", 0, 0, 64, 64)
                img = frame.subsample(2, 2)
        except Exception as e:
            img = None
            if wii_trainer and "png" not in sprite_reported:
                sprite_reported.add("png")
                wii_trainer.say("SPRITE ERROR: " + str(e))
        png_images[key] = img
    return png_images[key]

def draw_dashboard(w, h):
    """Training window for the Wii: current Pokemon + EV bar on the left, encountered Pokemon on the right."""
    global cursor_id
    cursor_id = None
    line_h = (GLYPH_ROWS + LINE_GAP) * SCALE
    view = wii_trainer.view
    x0, y = PAD, PAD
    if view is None:
        draw_text(x0, y, "WAITING FOR POKEMON IN SLOT 1...", COL_OLD)
        draw_text(x0, y + line_h, wii.status, COL_OLD)
    else:
        name = SPECIES_NAMES.get(view["species"], "Species #%d" % view["species"])
        draw_text(x0, y, name, COL_NEW)
        draw_text(x0 + text_w(name) + 8 * SCALE, y, "LV %d" % view["level"], COL_OLD, NUM_OLD)
        ot = "OT %s  ID %05d" % (view["ot"], view["tid"])
        draw_text(x0 + LEFT_W - 2 * PAD - text_w(ot), y, ot, COL_OLD, NUM_OLD)
        y += line_h + 4
        img = None
        png = pack_file(view["species"], view["shiny"])
        if png and SPRITE_ZOOM > 0:
            img = png_image(png, "front")
        top = y
        if img:
            canvas.create_image(x0, y, image=img, anchor="nw")
        sx = x0 + (img.width() if img else 0) + 14 * SCALE
        for i, st in enumerate(STAT_NAMES):
            trained = st == view["stat"]
            col = COL_NEW if trained else COL_OLD
            draw_text(sx, top + i * line_h, st, col)
            draw_text(sx + 40 * SCALE, top + i * line_h, "%d" % view["stats"][i], col, NUM_NEW if trained else NUM_OLD)
            draw_text(sx + 80 * SCALE, top + i * line_h, "EV %d" % view["evs"][i], col, NUM_NEW if trained else NUM_OLD)
        y = top + max(img.height() if img else 0, 6 * line_h) + 12
        val, target = view["val"], view["target"]
        draw_text(x0, y, "%s EV" % view["stat"], COL_NEW)
        label = "%d/%d" % (val, target)
        draw_text(x0 + LEFT_W - 2 * PAD - text_w(label), y, label, COL_NEW, NUM_NEW)
        y += line_h
        bar_w, bar_h = LEFT_W - 2 * PAD, 16
        canvas.create_rectangle(x0, y, x0 + bar_w, y + bar_h, outline=COL_FRAME, width=1)
        shown_val = anim["shown"] if anim["key"] == (view["pid"], view["stat"]) else val
        fill = int((bar_w - 2) * max(0, min(shown_val, target)) / target)
        if fill > 0:
            color = COL_FLASH if anim["flash"] > 0 else (COL_GOOD if val >= target else NUM_NEW)
            canvas.create_rectangle(x0 + 1, y + 1, x0 + 1 + fill, y + bar_h - 1, fill=color, width=0)
        if anim["pop"]:                                   # "+2" floats up from the end of the bar
            gain, frame = anim["pop"]
            draw_text(x0 + max(0, fill - 8), y - line_h - frame // 2, "+%d" % gain, COL_GOOD)
        y += bar_h + 8
        draw_text(x0, y, "TOTAL %d/510" % view["total"], COL_OLD, NUM_OLD)
        y += line_h
        draw_text(x0, y, "MACHO BRACE %s" % ("YES" if view["brace"] else "NO"), COL_OLD)
        y += line_h
        if view["missing"] > 0:
            draw_text(x0, y, "MISSING %d  +%d PER KO  ABOUT %d BATTLES" % (view["missing"], view["gain"], view["battles"]), COL_OLD, NUM_OLD)
        else:
            draw_text(x0, y, "TARGET REACHED!" if val >= target else "LIMIT 510 REACHED", COL_GOOD)
        if view["plan"]:                                  # PLAN: HP 240/240 > SPD 30/240
            y += line_h
            px = draw_text(x0, y, "PLAN ", COL_OLD)
            for i, (st, tg, have) in enumerate(view["plan"]):
                if i:
                    px = draw_text(px, y, " > ", COL_OLD)
                col = COL_GOOD if have >= tg else (COL_NEW if st == view["stat"] else COL_OLD)
                px = draw_text(px, y, "%s %d/%d" % (st, have, tg), col, col if have >= tg else (NUM_NEW if st == view["stat"] else NUM_OLD))
    # right column: encountered Pokemon, newest first
    rx = LEFT_W + PAD
    canvas.create_line(LEFT_W, PAD, LEFT_W, h - PAD, fill=COL_FRAME)
    draw_text(rx, PAD, "ENCOUNTERS", COL_OLD)
    ry = PAD + line_h + 4
    for i, e in enumerate(wii_trainer.history):
        if ry + ROW_H > h - PAD - line_h:
            break
        newest = i == 0
        icon = icon_file(e["species"])
        icon = png_image(icon, "icon") if icon and SPRITE_ZOOM > 0 else None
        if icon:
            canvas.create_image(rx, ry + (ROW_H - ICON_PX) // 2, image=icon, anchor="nw")
        col = (COL_NEW_WRONG if newest else COL_WRONG_OLD) if not e["good"] else (COL_NEW if newest else COL_OLD)
        numc = NUM_NEW if newest else NUM_OLD
        tx, ty = rx + ICON_PX + 10, ry + (ROW_H - GLYPH_ROWS * SCALE) // 2
        tx = draw_text(tx, ty, e["name"] + (" *" if e["shiny"] else ""), col)
        tx = draw_text(tx + 10 * SCALE, ty, "+%d %s" % (e["y"], e["stat"]), col, numc if e["good"] else col)
        draw_text(tx + 10 * SCALE, ty, "GOOD" if e["good"] else "[WRONG]", COL_GOOD if e["good"] and newest else col)
        ry += ROW_H
    if not wii_trainer.history:
        draw_text(rx, PAD + line_h + 4, "NONE YET", COL_OLD)
    # bottom line: connection problems or sprite problems
    notes = [l for l in wii_trainer.log[-5:] if l.startswith(("NO SPRITE", "SPRITE ERROR"))]
    bottom = notes[-1] if notes else (wii.status if not wii.status.startswith("CONNECTED") else "")
    if bottom:
        draw_text(PAD, h - PAD - GLYPH_ROWS * SCALE, bottom, COL_NEW_WRONG)

def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [l.strip() for l in f.read().splitlines() if l.strip()]
    except OSError:
        return None

mode = "menu"                    # "menu", "list" or "training"

save_cache = {"key": None, "lines": None}
list_state = {"key": None, "lines": []}

def save_path():
    try:
        saves = [os.path.join(SAVE_DIR, f) for f in os.listdir(SAVE_DIR) if f.lower().endswith(".sav")]
    except OSError:
        return None
    return max(saves, key=os.path.getmtime) if saves else None

def cached_save():
    path = save_path()
    if path is None:
        return None
    key = (path, os.path.getmtime(path))
    if key != save_cache["key"]:
        save_cache["key"] = key
        try:
            save_cache["lines"] = read_save(path)
        except Exception as e:
            save_cache["lines"] = ["COULD NOT READ SAVE: " + str(e)]
    return save_cache["lines"]

def build_list(has_live):
    save = cached_save()
    if not has_live:
        if save is None:
            return ["NO DATA. LOAD THE SCRIPT IN MGBA (OR PUT A .SAV IN SAVE_DIR)."]
        return ["(FROM SAVE FILE - SCRIPT NOT RUNNING)"] + save
    lines = read_lines(LIST_FILE) or ["WAITING FOR SCRIPT IN MGBA..."]
    return merge_save_boxes(lines, save)

def list_lines():
    if wii:
        return wii_list_lines(wii, wii_finder, cached_save())
    sp = save_path()
    keys = []
    for path in (LIST_FILE, sp):
        try:
            keys.append((path, os.path.getmtime(path)))
        except (OSError, TypeError):
            keys.append(None)
    if keys != list_state["key"]:
        list_state["key"] = keys
        list_state["lines"] = build_list(keys[0] is not None)
    return list_state["lines"]

def refresh():
    global shown
    if wii:
        wii_trainer.step()
    if mode == "menu":
        lines = MENU_LINES
    elif mode == "list":
        lines = list_lines()
    elif wii:
        lines = wii_trainer.log or [wii.status]
    else:
        lines = read_lines(LOG_FILE) or ["WAITING FOR SCRIPT IN MGBA..."]
    if mode == "training":
        lines = lines[-MAX_LINES:]
    if wii and mode == "training":
        lines = (wii_trainer.rev, wii.status, len(wii_trainer.log))    # the dashboard draws from the trainer, not from text lines
    if lines != shown:
        shown = lines
        redraw()

def set_mode(m):
    global mode, shown, scroll
    mode = m
    shown = None
    scroll = 0
    refresh()

def on_key(event):
    if event.char == "1":
        set_mode("list")
    elif event.char == "2":
        set_mode("training")
    elif event.char == "0" or event.keysym == "Escape":
        set_mode("menu")
    elif mode == "list":
        step = {"Up": -1, "Down": 1, "Prior": -10, "Next": 10, "Home": -10**6, "End": 10**6}.get(event.keysym)
        if step:
            scroll_by(step)

def scroll_by(n):
    global scroll
    if mode == "list":
        scroll = max(0, scroll + n)
        redraw()

def on_wheel(event):
    scroll_by(-3 if event.delta > 0 else 3)

def poll():
    refresh()
    root.after(POLL_MS, poll)

def anim_step():
    """Moves the bar smoothly towards the real EV value; redraws only while something moves."""
    again = 60
    view = wii_trainer.view if (wii and mode == "training") else None
    if view:
        key, val = (view["pid"], view["stat"]), view["val"]
        moving = False
        if anim["key"] != key or anim["last"] is None or val < anim["last"]:
            anim.update(key=key, shown=float(val), last=val, flash=0, pop=None)
            moving = True
        else:
            if val > anim["last"]:
                anim.update(pop=[val - anim["last"], 0], flash=14, last=val)
            if abs(val - anim["shown"]) > 0.3:
                anim["shown"] += (val - anim["shown"]) * 0.2
                moving = True
            elif anim["shown"] != val:
                anim["shown"] = float(val)
                moving = True
        if anim["flash"] > 0:
            anim["flash"] -= 1
            moving = True
        if anim["pop"]:
            anim["pop"][1] += 1
            moving = True
            if anim["pop"][1] > 34:
                anim["pop"] = None
        if moving:
            redraw()
            again = 35
    root.after(again, anim_step)

def blink():
    global cursor_on
    cursor_on = not cursor_on
    if cursor_id is not None:
        canvas.itemconfigure(cursor_id, state="normal" if cursor_on else "hidden")
    root.after(500, blink)

canvas.bind("<Configure>", redraw)
root.bind("<Key>", on_key)
root.bind("<MouseWheel>", on_wheel)
poll()
blink()
anim_step()
root.mainloop()