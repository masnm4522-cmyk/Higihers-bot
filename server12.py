from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition
from asyncio import sleep, create_task, CancelledError
import os
import json
import logging
from datetime import datetime, timedelta
import random
import aiohttp

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تنظیمات پیش‌فرض
CONFIG_FILE = "bot_config.json"
DEFAULT_CONFIG = {
    "admin_usernames": ["farshiidx7"],
    "vip_usernames": [],
    "banned_users": [],
    "teleport_locations": {
        "vip": {"x": 14.5, "y": 16.75, "z": 5.5},
        "vip1": {"x": 14.5, "y": 16.75, "z": 5.5},
        "dj": {"x": 9.5, "y": 10.75, "z": 10.5}
    },
    "language": "fa",
    "welcome_message": "خوش اومدی {username}! برای دستورات !help بزنید.",
    "announcement_interval": 300,
    "announcement_message": "برای دیدن دستورات ربات، !help بزنید!"
}

class AdvancedBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.active_users = {}
        self.user_dances = {}
        self.dance_tasks = {}
        self.user_positions = {}
        self.user_scores = {}
        self.user_id = None
        self.announcement_task = None
        self.score_update_task = None
        self.frozen_users = {}
        self.party_dances = {}
        self.commands = {
            "!help": self.cmd_help,
            "!spam": self.cmd_spam,
            "!tele": self.cmd_tele,
            "!heart": self.cmd_heart,
            "!clap": self.cmd_clap,
            "!wink": self.cmd_wink,
            "!wave": self.cmd_wave,
            "!thumbs": self.cmd_thumbs,
            "!wallet": self.cmd_wallet,
            "!set": self.cmd_set,
            "!tip": self.cmd_tip,
            "!vip": self.cmd_vip,
            "!vip1": self.cmd_vip1,
            "!dj": self.cmd_dj,
            "!down": self.cmd_down,
            "!ban": self.cmd_ban,
            "!unban": self.cmd_unban,
            "!dancechain": self.cmd_dancechain,
            "!addtele": self.cmd_addtele,
            "!deltele": self.cmd_deltele,
            "!item set": self.cmd_set_item,
            "!welcome": self.cmd_welcome,
            "!addadmin": self.cmd_addadmin,
            "!removeadmin": self.cmd_removeadmin,
            "!listadd": self.cmd_listadd,
            "!freeze": self.cmd_freeze,
            "!unfreeze": self.cmd_unfreeze,
            "!party": self.cmd_party,
            "!partys": self.cmd_partys
        }
        self.emotes = {
            "1": "idle_zombie",
            "2": "idle_layingdown2",
            "3": "idle_layingdown",
            "4": "idle-sleep",
            "5": "idle-sad",
            "6": "idle-posh",
            "7": "idle-loop-tired",
            "8": "idle-loop-tapdance",
            "9": "idle-loop-sitfloor",
            "10": "idle-loop-shy",
            "11": "idle-loop-sad",
            "12": "idle-loop-happy",
            "13": "idle-loop-annoyed",
            "14": "idle-loop-aerobics",
            "15": "idle-lookup",
            "16": "idle-hero",
            "17": "idle-floorsleeping",
            "18": "idle-enthusiastic",
            "19": "idle-dance-swinging",
            "20": "idle-dance-headbobbing",
            "21": "idle-angry",
            "22": "emote-yes",
            "23": "emote-wings",
            "24": "emote-wave",
            "25": "emote-tired",
            "26": "emote-think",
            "27": "emote-theatrical",
            "28": "emote-tapdance",
            "29": "emote-superrun",
            "30": "emote-superpunch",
            "31": "emote-sumo",
            "32": "emote-suckthumb",
            "33": "emote-splitsdrop",
            "34": "emote-snowball",
            "35": "emote-snowangel",
            "36": "emote-shy",
            "37": "emote-secrethandshake",
            "38": "emote-sad",
            "39": "emote-ropepull",
            "40": "emote-roll",
            "41": "emote-rofl",
            "42": "emote-robot",
            "43": "emote-rainbow",
            "44": "emote-proposing",
            "45": "emote-peekaboo",
            "46": "emote-peace",
            "47": "emote-panic",
            "48": "emote-no",
            "49": "emote-ninjarun",
            "50": "emote-nightfever",
            "51": "emote-monster_fail",
            "52": "emote-model",
            "53": "emote-lust",
            "54": "emote-levelup",
            "55": "emote-laughing2",
            "56": "emote-laughing",
            "57": "emote-kiss",
            "58": "emote-kicking",
            "59": "emote-jumpb",
            "60": "emote-gravity",
            "61": "emote-judochop",
            "62": "emote-jetpack",
            "63": "emote-hugyourself",
            "64": "emote-hot",
            "65": "emote-hero",
            "66": "emote-hello",
            "67": "emote-headball",
            "68": "emote-harlemshake",
            "69": "emote-happy",
            "70": "emote-handstand",
            "71": "emote-greedy",
            "72": "emote-graceful",
            "73": "emote-gordonshuffle",
            "74": "emote-ghost-idle",
            "75": "emote-gangnam",
            "76": "emote-frollicking",
            "77": "emote-fainting",
            "78": "emote-fail2",
            "79": "emote-fail1",
            "80": "emote-exasperatedb",
            "81": "emote-exasperated",
            "82": "emote-elbowbump",
            "83": "emote-disco",
            "84": "emote-disappear",
            "85": "emote-deathdrop",
            "86": "emote-death2",
            "87": "emote-death",
            "88": "emote-dab",
            "89": "emote-curtsy",
            "90": "emote-confused",
            "91": "emote-cold",
            "92": "emote-charging",
            "93": "emote-bunnyhop",
            "94": "emote-bow",
            "95": "emote-boo",
            "96": "emote-baseball",
            "97": "emote-apart",
            "98": "emoji-thumbsup",
            "99": "emoji-there",
            "100": "emoji-sneeze",
            "101": "emoji-smirking",
            "102": "emoji-sick",
            "103": "emoji-scared",
            "104": "emoji-punch",
            "105": "emoji-pray",
            "106": "emoji-poop",
            "107": "emoji-naughty",
            "118": "emoji-mind-blown",
            "119": "emoji-lying",
            "110": "emoji-halo",
            "111": "emoji-hadoken",
            "112": "emoji-give-up",
            "113": "emoji-gagging",
            "114": "emoji-flex",
            "115": "emoji-dizzy",
            "116": "emoji-cursing",
            "117": "emoji-crying",
            "118": "emoji-clapping",
            "119": "emoji-celebrate",
            "120": "emoji-arrogance",
            "121": "emoji-angry",
            "122": "dance-voguehands",
            "123": "dance-tiktok8",
            "124": "dance-tiktok2",
            "125": "dance-spiritual",
            "126": "dance-smoothwalk",
            "127": "dance-singleladies",
            "128": "dance-shoppingcart",
            "129": "dance-russian",
            "130": "dance-robotic",
            "131": "dance-pennywise",
            "132": "dance-orangejustice",
            "133": "dance-metal",
            "134": "dance-martial-artist",
            "135": "dance-macarena",
            "136": "dance-handsup",
            "137": "dance-duckwalk",
            "138": "dance-breakdance",
            "139": "dance-blackpink",
            "140": "dance-aerobics",
            "141": "emote-hyped",
            "142": "dance-jinglebell",
            "143": "idle-nervous",
            "144": "idle-toilet",
            "145": "emote-attention",
            "146": "sit-open",
            "147": "emote-astronaut",
            "148": "dance-zombie",
            "149": "emoji-ghost",
            "150": "emote-hearteyes",
            "151": "emote-swordfight",
            "152": "emote-timejump",
            "153": "emote-snake",
            "154": "emote-heartfingers",
            "155": "emote-heartshape",
            "156": "emote-hug",
            "157": "emote-lagughing",
            "158": "emoji-eyeroll",
            "159": "emote-embarrassed",
            "160": "emote-float",
            "161": "emote-telekinesis",
            "162": "dance-sexy",
            "163": "emote-puppet",
            "164": "idle-fighter",
            "165": "dance-pinguin",
            "166": "dance-creepypuppet",
            "167": "emote-sleigh",
            "168": "emote-maniac",
            "169": "emote-energyball",
            "170": "idle_singing",
            "171": "emote-frog",
            "172": "emote-superpose",
            "173": "emote-cute",
            "174": "dance-tiktok9",
            "175": "dance-weird",
            "176": "dance-tiktok10",
            "177": "emote-pose7",
            "178": "emote-pose8",
            "179": "idle-dance-casual",
            "180": "emote-pose1",
            "181": "emote-pose3",
            "182": "emote-pose5",
            "183": "emote-cutey",
            "184": "emote-punkguitar",
            "185": "emote-zombierun",
            "186": "dance-jinglebell",
            "187": "emote-gravity",
            "188": "dance-icecream",
            "189": "dance-wrong",
            "190": "idle-uwu",
            "191": "idle-dance-tiktok4",
            "192": "emote-shy2",
            "193": "dance-anime",
            "194": "dance-kawai",
            "195": "idle-wild",
            "196": "emote-iceskating",
            "197": "emote-pose6",
            "198": "emote-celebrationstep",
            "199": "emote-creepycute",
            "200": "emote-frustrated",
            "201": "emote-pose10",
            "202": "sit-relaxed",
            "203": "emote-stargaze",
            "204": "emote-slap",
            "205": "emote-boxer",
            "206": "emote-headblowup",
            "207": "emote-kawaiigogo",
            "208": "emote-repose",
            "209": "idle-dance-tiktok7",
            "210": "emote-shrink",
            "211": "emote-pose9",
            "212": "emote-teleporting",
            "213": "dance-touch",
            "214": "idle-guitar",
            "215": "emote-gift",
            "216": "dance-employee",
            "217": "emote-kissing",
            "218": "dance-tiktok11",
            "219": "emote-cutesalute",
            "220": "emote-salute",
            "221": "idle-floorsleeping2",
            "۱": "idle_zombie",
            "۲": "idle_layingdown2",
            "۳": "idle_layingdown",
            "۴": "idle-sleep",
            "۵": "idle-sad",
            "۶": "idle-posh",
            "۷": "idle-loop-tired",
            "۸": "idle-loop-tapdance",
            "۹": "idle-loop-sitfloor",
            "۱۰": "idle-loop-shy",
            "۱۱": "idle-loop-sad",
            "۱۲": "idle-loop-happy",
            "۱۳": "idle-loop-annoyed",
            "۱۴": "idle-loop-aerobics",
            "۱۵": "idle-lookup",
            "۱۶": "idle-hero",
            "۱۷": "idle-floorsleeping",
            "۱۸": "idle-enthusiastic",
            "۱۹": "idle-dance-swinging",
            "۲۰": "idle-dance-headbobbing",
            "۲۱": "idle-angry",
            "۲۲": "emote-yes",
            "۲۳": "emote-wings",
            "۲۴": "emote-wave",
            "۲۵": "emote-tired",
            "۲۶": "emote-think",
            "۲۷": "emote-theatrical",
            "۲۸": "emote-tapdance",
            "۲۹": "emote-superrun",
            "۳۰": "emote-superpunch",
            "۳۱": "emote-sumo",
            "۳۲": "emote-suckthumb",
            "۳۳": "emote-splitsdrop",
            "۳۴": "emote-snowball",
            "۳۵": "emote-snowangel",
            "۳۶": "emote-shy",
            "۳۷": "emote-secrethandshake",
            "۳۸": "emote-sad",
            "۳۹": "emote-ropepull",
            "۴۰": "emote-roll",
            "۴۱": "emote-rofl",
            "۴۲": "emote-robot",
            "۴۳": "emote-rainbow",
            "۴۴": "emote-proposing",
            "۴۵": "emote-peekaboo",
            "۴۶": "emote-peace",
            "۴۷": "emote-panic",
            "۴۸": "emote-no",
            "۴۹": "emote-ninjarun",
            "۵۰": "emote-nightfever",
            "۵۱": "emote-monster_fail",
            "۵۲": "emote-model",
            "۵۳": "emote-lust",
            "۵۴": "emote-levelup",
            "۵۵": "emote-laughing2",
            "۵۶": "emote-laughing",
            "۵۷": "emote-kiss",
            "۵۸": "emote-kicking",
            "۵۹": "emote-jumpb",
            "۶۰": "emote-gravity",
            "۶۱": "emote-judochop",
            "۶۲": "emote-jetpack",
            "۶۳": "emote-hugyourself",
            "۶۴": "emote-hot",
            "۶۵": "emote-hero",
            "۶۶": "emote-hello",
            "۶۷": "emote-headball",
            "۶۸": "emote-harlemshake",
            "۶۹": "emote-happy",
            "۷۰": "emote-handstand",
            "۷۱": "emote-greedy",
            "۷۲": "emote-graceful",
            "۷۳": "emote-gordonshuffle",
            "۷۴": "emote-ghost-idle",
            "۷۵": "emote-gangnam",
            "۷۶": "emote-frollicking",
            "۷۷": "emote-fainting",
            "۷۸": "emote-fail2",
            "۷۹": "emote-fail1",
            "۸۰": "emote-exasperatedb",
            "۸۱": "emote-exasperated",
            "۸۲": "emote-elbowbump",
            "۸۳": "emote-disco",
            "۸۴": "emote-disappear",
            "۸۵": "emote-deathdrop",
            "۸۶": "emote-death2",
            "۸۷": "emote-death",
            "۸۸": "emote-dab",
            "۸۹": "emote-curtsy",
            "۹۰": "emote-confused",
            "۹۱": "emote-cold",
            "۹۲": "emote-charging",
            "۹۳": "emote-bunnyhop",
            "۹۴": "emote-bow",
            "۹۵": "emote-boo",
            "۹۶": "emote-baseball",
            "۹۷": "emote-apart",
            "۹۸": "emoji-thumbsup",
            "۹۹": "emoji-there",
            "۱۰۰": "emoji-sneeze",
            "۱۰۱": "emoji-smirking",
            "۱۰۲": "emoji-sick",
            "۱۰۳": "emoji-scared",
            "۱۰۴": "emoji-punch",
            "۱۰۵": "emoji-pray",
            "۱۰۶": "emoji-poop",
            "۱۰۷": "emoji-naughty",
            "۱۰۸": "emoji-mind-blown",
            "۱۰۹": "emoji-lying",
            "۱۱۰": "emoji-halo",
            "۱۱۱": "emoji-hadoken",
            "۱۱۲": "emoji-give-up",
            "۱۱۳": "emoji-gagging",
            "۱۱۴": "emoji-flex",
            "۱۱۵": "emoji-dizzy",
            "۱۱۶": "emoji-cursing",
            "۱۱۷": "emoji-crying",
            "۱۱۸": "emoji-clapping",
            "۱۱۹": "emoji-celebrate",
            "۱۲۰": "emoji-arrogance",
            "۱۲۱": "emoji-angry",
            "۱۲۲": "dance-voguehands",
            "۱۲۳": "dance-tiktok8",
            "۱۲۴": "dance-tiktok2",
            "۱۲۵": "dance-spiritual",
            "۱۲۶": "dance-smoothwalk",
            "۱۲۷": "dance-singleladies",
            "۱۲۸": "dance-shoppingcart",
            "۱۲۹": "dance-russian",
            "۱۳۰": "dance-robotic",
            "۱۳۱": "dance-pennywise",
            "۱۳۲": "dance-orangejustice",
            "۱۳۳": "dance-metal",
            "۱۳۴": "dance-martial-artist",
            "۱۳۵": "dance-macarena",
            "۱۳۶": "dance-handsup",
            "۱۳۷": "dance-duckwalk",
            "۱۳۸": "dance-breakdance",
            "۱۳۹": "dance-blackpink",
            "۱۴۰": "dance-aerobics",
            "۱۴۱": "emote-hyped",
            "۱۴۲": "dance-jinglebell",
            "۱۴۳": "idle-nervous",
            "۱۴۴": "idle-toilet",
            "۱۴۵": "emote-attention",
            "۱۴۶": "sit-open",
            "۱۳۷": "emote-astronaut",
            "۱۴۸": "dance-zombie",
            "۱۴۹": "emoji-ghost",
            "۱۵۰": "emote-hearteyes",
            "۱۵۱": "emote-swordfight",
            "۱۵۲": "emote-timejump",
            "۱۵۳": "emote-snake",
            "۱۵۴": "emote-heartfingers",
            "۱۵۵": "emote-heartshape",
            "۱۵۶": "emote-hug",
            "۱۵۷": "emote-lagughing",
            "۱۵۸": "emoji-eyeroll",
            "۱۵۹": "emote-embarrassed",
            "۱۶۰": "emote-float",
            "۱۶۱": "emote-telekinesis",
            "۱۶۲": "dance-sexy",
            "۱۶۳": "emote-puppet",
            "۱۶۴": "idle-fighter",
            "۱۶۵": "dance-pinguin",
            "۱۶۶": "dance-creepypuppet",
            "۱۶۷": "emote-sleigh",
            "۱۶۸": "emote-maniac",
            "۱۶۹": "emote-energyball",
            "۱۷۰": "idle_singing",
            "۱۷۱": "emote-frog",
            "۱۷۲": "emote-superpose",
            "۱۷۳": "emote-cute",
            "۱۷۴": "dance-tiktok9",
            "۱۷۵": "dance-weird",
            "۱۷۶": "dance-tiktok10",
            "۱۷۷": "emote-pose7",
            "۱۷۸": "emote-pose8",
            "۱۷۹": "idle-dance-casual",
            "۱۸۰": "emote-pose1",
            "۱۸۱": "emote-pose3",
            "۱۸۲": "emote-pose5",
            "۱۸۳": "emote-cutey",
            "۱۸۴": "emote-punkguitar",
            "۱۸۵": "emote-zombierun",
            "۱۸۶": "dance-jinglebell",
            "۱۸۷": "emote-gravity",
            "۱۸۸": "dance-icecream",
            "۱۸۹": "dance-wrong",
            "۱۹۰": "idle-uwu",
            "۱۹۱": "idle-dance-tiktok4",
            "۱۹۲": "emote-shy2",
            "۱۹۳": "dance-anime",
            "۱۹۴": "dance-kawai",
            "۱۹۵": "idle-wild",
            "۱۹۶": "emote-iceskating",
            "۱۹۷": "emote-pose6",
            "۱۹۸": "emote-celebrationstep",
            "۱۹۹": "emote-creepycute",
            "۲۰۰": "emote-frustrated",
            "۲۰۱": "emote-pose10",
            "۲۰۲": "sit-relaxed",
            "۲۰۳": "emote-stargaze",
            "۲۰۴": "emote-slap",
            "۲۰۵": "emote-boxer",
            "۲۰۶": "emote-headblowup",
            "۲۰۷": "emote-kawaiigogo",
            "۲۰۸": "emote-repose",
            "۲۰۹": "idle-dance-tiktok7",
            "۲۱۰": "emote-shrink",
            "۲۱۱": "emote-pose9",
            "۲۱۲": "emote-teleporting",
            "۲۱۳": "dance-touch",
            "۲۱۴": "idle-guitar",
            "۲۱۵": "emote-gift",
            "۲۱۶": "dance-employee",
            "۲۱۷": "emote-kissing",
            "۲۱۸": "dance-tiktok11",
            "۲۱۹": "emote-cutesalute",
            "۲۲۰": "emote-salute",
            "۲۲۱": "idle-floorsleeping2",
            "zombie": "idle_zombie",
            "relaxed": "idle_layingdown2",
            "attentive": "idle_layingdown",
            "sleepy": "idle-sleep",
            "poutyFace": "idle-sad",
            "posh": "idle-posh",
            "sleepy": "idle-loop-tired",
            "tapLoop": "idle-loop-tapdance",
            "sit": "idle-loop-sitfloor",
            "shy": "idle-loop-shy",
            "bummed": "idle-loop-sad",
            "chillin'": "idle-loop-happy",
            "annoyed": "idle-loop-annoyed",
            "aerobics": "idle-loop-aerobics",
            "ponder": "idle-lookup",
            "heropose": "idle-hero",
            "cozynap": "idle-floorsleeping",
            "enthused": "idle-enthusiastic",
            "boogieswing": "idle-dance-swinging",
            "feelthebeat": "idle-dance-headbobbing",
            "irritated": "idle-angry",
            "yes": "emote-yes",
            "ibelieveIcanfly": "emote-wings",
            "theWave": "emote-wave",
            "tired": "emote-tired",
            "think": "emote-think",
            "theatrical": "emote-theatrical",
            "tapdance": "emote-tapdance",
            "superrun": "emote-superrun",
            "superPunch": "emote-superpunch",
            "sumofight": "emote-sumo",
            "thumbSuck": "emote-suckthumb",
            "splitsdrop": "emote-splitsdrop",
            "snowballFight": "emote-snowball",
            "snowAngel": "emote-snowangel",
            "shy": "emote-shy",
            "secrehandshake": "emote-secrethandshake",
            "sad": "emote-sad",
            "ropepull": "emote-ropepull",
            "roll": "emote-roll",
            "rofl": "emote-rofl",
            "robot": "emote-robot",
            "rainbow": "emote-rainbow",
            "proposing": "emote-proposing",
            "peekaboo": "emote-peekaboo",
            "peace": "emote-peace",
            "panic": "emote-panic",
            "no": "emote-no",
            "ninjarun": "emote-ninjarun",
            "nightfever": "emote-nightfever",
            "monsterfail": "emote-monster_fail",
            "model": "emote-model",
            "flirtywave": "emote-lust",
            "levelUp": "emote-levelup",
            "amused": "emote-laughing2",
            "laugh": "emote-laughing",
            "kiss": "emote-kiss",
            "superKick": "emote-kicking",
            "jump": "emote-jumpb",
            "gravity": "emote-gravity",
            "judochop": "emote-judochop",
            "imaginaryjetpack": "emote-jetpack",
            "hugyourself": "emote-hugyourself",
            "sweating": "emote-hot",
            "heroentrance": "emote-hero",
            "hello": "emote-hello",
            "headball": "emote-headball",
            "harlemShake": "emote-harlemshake",
            "happy": "emote-happy",
            "handstand": "emote-handstand",
            "greedyEmote": "emote-greedy",
            "graceful": "emote-graceful",
            "moonwalk": "emote-gordonshuffle",
            "ghostfloat": "emote-ghost-idle",
            "gangnamstyle": "emote-gangnam",
            "frolic": "emote-frollicking",
            "faint": "emote-fainting",
            "clumsy": "emote-fail2",
            "fall": "emote-fail1",
            "facePalm": "emote-exasperatedb",
            "exasperated": "emote-exasperated",
            "elbowBump": "emote-elbowbump",
            "disco": "emote-disco",
            "blastOff": "emote-disappear",
            "faintDrop": "emote-deathdrop",
            "collapse": "emote-death2",
            "revival": "emote-death",
            "dab": "emote-dab",
            "curtsy": "emote-curtsy",
            "confusion": "emote-confused",
            "cold": "emote-cold",
            "charging": "emote-charging",
            "bunnyHop": "emote-bunnyhop",
            "bow": "emote-bow",
            "boo": "emote-boo",
            "homerun": "emote-baseball",
            "fallingapart": "emote-apart",
            "thumbsup": "emoji-thumbsup",
            "point": "emoji-there",
            "sneeze": "emoji-sneeze",
            "smirk": "emoji-smirking",
            "sick": "emoji-sick",
            "gasp": "emoji-scared",
            "punch": "emoji-punch",
            "pray": "emoji-pray",
            "stinky": "emoji-poop",
            "naughty": "emoji-naughty",
            "mindBlown": "emoji-mind-blown",
            "lying": "emoji-lying",
            "levitate": "emoji-halo",
            "fireball Lunge": "emoji-hadoken",
            "giveup": "emoji-give-up",
            "tummy Ache": "emoji-gagging",
            "flex": "emoji-flex",
            "stunned": "emoji-dizzy",
            "cursing Emote": "emoji-cursing",
            "sob": "emoji-crying",
            "clap": "emoji-clapping",
            "raiseTheRoof": "emoji-celebrate",
            "arrogance": "emoji-arrogance",
            "angry": "emoji-angry",
            "VogueHands": "dance-voguehands",
            "SavageDance": "dance-tiktok8",
            "DontStartNow": "dance-tiktok2",
            "YogaFlow": "dance-spiritual",
            "Smoothwalk": "dance-smoothwalk",
            "RingonIt": "dance-singleladies",
            "Let's Go Shopping": "dance-shoppingcart",
            "russian Dance": "dance-russian",
            "tobotic": "dance-robotic",
            "penny's Dance": "dance-pennywise",
            "orange Juice Dance": "dance-orangejustice",
            "rockout": "dance-metal",
            "karate": "dance-martial-artist",
            "macarena": "dance-macarena",
            "handsintheair": "dance-handsup",
            "duckealk": "dance-duckwalk",
            "Breakdance": "dance-breakdance",
            "kpop": "dance-blackpink",
            "PushUps": "dance-aerobics",
            "Hyped": "emote-hyped",
            "Jinglebell": "dance-jinglebell",
            "Nervous": "idle-nervous",
            "Toilet": "idle-toilet",
            "Attention": "emote-attention",
            "laidback": "sit-open",
            "Astronaut": "emote-astronaut",
            "DanceZombie": "dance-zombie",
            "ghost": "emoji-ghost",
            "HeartEyes": "emote-hearteyes",
            "Swordfight": "emote-swordfight",
            "TimeJump": "emote-timejump",
            "Snake": "emote-snake",
            "HeartFingers": "emote-heartfingers",
            "Heart Shape": "emote-heartshape",
            "hug": "emote-hug",
            "Laugh": "emote-lagughing",
            "Eyeroll": "emoji-eyeroll",
            "Embarrassed": "emote-embarrassed",
            "float": "emote-float",
            "Telekinesis": "emote-telekinesis",
            "Sexydance": "dance-sexy",
            "Puppet": "emote-puppet",
            "Fighter idle": "idle-fighter",
            "Penguindance": "dance-pinguin",
            "Creepypuppet": "dance-creepypuppet",
            "Sleigh": "emote-sleigh",
            "Maniac": "emote-maniac",
            "EnergyBall": "emote-energyball",
            "Singing": "idle_singing",
            "Frog": "emote-frog",
            "Superpose": "emote-superpose",
            "Cute": "emote-cute",
            "TikTok9": "dance-tiktok9",
            "Weird": "dance-weird",
            "TikTok10": "dance-tiktok10",
            "pose7": "emote-pose7",
            "pose8": "emote-pose8",
            "casualDance": "idle-dance-casual",
            "pose1": "emote-pose1",
            "pose3": "emote-pose3",
            "pose5": "emote-pose5",
            "Cutey": "emote-cutey",
            "PunkGuitar": "emote-punkguitar",
            "zombieru": "emote-zombierun",
            "fashionista": "dance-jinglebell",
            "gravity": "emote-gravity",
            "icecream": "dance-icecream",
            "wrong": "dance-wrong",
            "uwu": "idle-uwu",
            "TikTok4": "idle-dance-tiktok4",
            "advancedshy": "emote-shy2",
            "anime": "dance-anime",
            "kawaii": "dance-kawai",
            "Scritchy": "idle-wild",
            "iceskating": "emote-iceskating",
            "surpriseBig": "emote-pose6",
            "celebrationStep": "emote-celebrationstep",
            "creepycute": "emote-creepycute",
            "frustrated": "emote-frustrated",
            "pose10": "emote-pose10",
            "repose": "sit-relaxed",
            "stargazing": "emote-stargaze",
            "slap": "emote-slap",
            "boxer": "emote-boxer",
            "headBlowup": "emote-headblowup",
            "kawaiiGoGo": "emote-kawaiigogo",
            "repose": "emote-repose",
            "tiktok7": "idle-dance-tiktok7",
            "shrink": "emote-shrink",
            "ditzyPose": "emote-pose9",
            "teleporting": "emote-teleporting",
            "touch": "dance-touch",
            "airuitar": "idle-guitar",
            "thisIs For You": "emote-gift",
            "pushit": "dance-employee",
            "sweetSmooch": "emote-kissing",
            "tiktok11": "dance-tiktok11",
            "cutesalute": "emote-cutesalute",
            "relaxing": "idle-floorsleeping2",
            "attention": "emote-salute"
            
        }

        self.emote_durations = {
            "idle_zombie": 28.754937,
            "idle_layingdown2": 21.546653,
            "idle_layingdown": 24.585168,
            "idle-sleep": 22.620446,
            "idle-sad": 24.377214,
            "idle-posh": 21.851256,
            "idle-loop-tired": 21.959007,
            "idle-loop-tapdance": 6.261593,
            "idle-loop-sitfloor": 22.321055,
            "idle-loop-shy": 16.47449,
            "idle-loop-sad": 6.052999,
            "idle-loop-happy": 18.798322,
            "idle-loop-annoyed": 17.058522,
            "idle-loop-aerobics": 8.507535,
            "idle-lookup": 22.339865,
            "idle-hero": 21.877099,
            "idle-floorsleeping": 13.935264,
            "idle-enthusiastic": 15.941537,
            "idle-dance-swinging": 13.198551,
            "idle-dance-headbobbing": 25.367458,
            "idle-angry": 25.427848,
            "emote-yes": 2.565001,
            "emote-wings": 13.134487,
            "emote-wave": 2.690873,
            "emote-tired": 4.61063,
            "emote-think": 3.691104,
            "emote-theatrical": 8.591869,
            "emote-tapdance": 11.057294,
            "emote-superrun": 6.273226,
            "emote-superpunch": 3.751054,
            "emote-sumo": 10.868834,
            "emote-suckthumb": 4.185944,
            "emote-splitsdrop": 4.46931,
            "emote-snowball": 5.230467,
            "emote-snowangel": 6.218627,
            "emote-shy": 4.477567,
            "emote-secrethandshake": 3.879024,
            "emote-sad": 5.411073,
            "emote-ropepull": 8.769656,
            "emote-roll": 3.560517,
            "emote-rofl": 6.314731,
            "emote-robot": 7.607362,
            "emote-rainbow": 2.813373,
            "emote-proposing": 4.27888,
            "emote-peekaboo": 3.629867,
            "emote-peace": 5.755004,
            "emote-panic": 2.850966,
            "emote-no": 2.703034,
            "emote-ninjarun": 4.754721,
            "emote-nightfever": 15.0,
            "emote-monster_fail": 15.0,
            "emote-model": 15.0,
            "emote-lust": 15.0,
            "emote-levelup": 15.0,
            "emote-laughing2": 15.0,
            "emote-laughing": 15.0,
            "emote-kiss": 15.0,
            "emote-kicking": 15.0,
            "emote-jumpb": 15.0,
            "emote-gravity": 15.0,
            "emote-judochop": 15.0,
            "emote-jetpack": 15.0,
            "emote-hugyourself": 15.0,
            "emote-hot": 15.0,
            "emote-hero": 15.0,
            "emote-hello": 15.0,
            "emote-headball": 15.0,
            "emote-harlemshake": 15.0,
            "emote-happy": 15.0,
            "emote-handstand": 15.0,
            "emote-greedy": 15.0,
            "emote-graceful": 15.0,
            "emote-gordonshuffle": 15.0,
            "emote-ghost-idle": 15.0,
            "emote-gangnam": 15.0,
            "emote-frollicking": 15.0,
            "emote-fainting": 15.0,
            "emote-fail2": 15.0,
            "emote-fail1": 15.0,
            "emote-exasperatedb": 15.0,
            "emote-exasperated": 15.0,
            "emote-elbowbump": 15.0,
            "emote-disco": 15.0,
            "emote-disappear": 15.0,
            "emote-deathdrop": 15.0,
            "emote-death2": 15.0,
            "emote-death": 15.0,
            "emote-dab": 15.0,
            "emote-curtsy": 15.0,
            "emote-confused": 15.0,
            "emote-cold": 15.0,
            "emote-charging": 15.0,
            "emote-bunnyhop": 15.0,
            "emote-bow": 15.0,
            "emote-boo": 15.0,
            "emote-baseball": 15.0,
            "emote-apart": 15.0,
            "emoji-thumbsup": 15.0,
            "emoji-there": 15.0,
            "emoji-sneeze": 15.0,
            "emoji-smirking": 15.0,
            "emoji-sick": 15.0,
            "emoji-scared": 15.0,
            "emoji-punch": 15.0,
            "emoji-pray": 15.0,
            "emoji-poop": 15.0,
            "emoji-naughty": 15.0,
            "emoji-mind-blown": 15.0,
            "emoji-lying": 15.0,
            "emoji-halo": 15.0,
            "emoji-hadoken": 15.0,
            "emoji-give-up": 15.0,
            "emoji-gagging": 15.0,
            "emoji-flex": 15.0,
            "emoji-dizzy": 15.0,
            "emoji-cursing": 15.0,
            "emoji-crying": 15.0,
            "emoji-clapping": 15.0,
            "emoji-celebrate": 15.0,
            "emoji-arrogance": 15.0,
            "emoji-angry": 15.0,
            "dance-voguehands": 15.0,
            "dance-tiktok8": 15.0,
            "dance-tiktok2": 15.0,
            "dance-spiritual": 15.0,
            "dance-smoothwalk": 15.0,
            "dance-singleladies": 15.0,
            "dance-shoppingcart": 15.0,
            "dance-russian": 15.0,
            "dance-robotic": 15.0,
            "dance-pennywise": 15.0,
            "dance-orangejustice": 15.0,
            "dance-metal": 15.0,
            "dance-martial-artist": 15.0,
            "dance-macarena": 15.0,
            "dance-handsup": 15.0,
            "dance-duckwalk": 15.0,
            "dance-breakdance": 15.0,
            "dance-blackpink": 15.0,
            "dance-aerobics": 15.0,
            "emote-hyped": 15.0,
            "dance-jinglebell": 15.0,
            "idle-nervous": 15.0,
            "idle-toilet": 15.0,
            "emote-attention": 15.0,
            "sit-open": 15.0,
            "emote-astronaut": 15.0,
            "dance-zombie": 15.0,
            "emoji-ghost": 15.0,
            "emote-hearteyes": 15.0,
            "emote-swordfight": 15.0,
            "emote-timejump": 15.0,
            "emote-snake": 15.0,
            "emote-heartfingers": 15.0,
            "emote-heartshape": 15.0,
            "emote-hug": 15.0,
            "emote-lagughing": 15.0,
            "emoji-eyeroll": 15.0,
            "emote-embarrassed": 15.0,
            "emote-float": 15.0,
            "emote-telekinesis": 15.0,
            "dance-sexy": 15.0,
            "emote-puppet": 15.0,
            "idle-fighter": 15.0,
            "dance-pinguin": 15.0,
            "dance-creepypuppet": 15.0,
            "emote-sleigh": 15.0,
            "emote-maniac": 15.0,
            "emote-energyball": 15.0,
            "idle_singing": 15.0,
            "emote-frog": 15.0,
            "emote-superpose": 15.0,
            "emote-cute": 15.0,
            "dance-tiktok9": 15.0,
            "dance-weird": 15.0,
            "dance-tiktok10": 15.0,
            "emote-pose7": 15.0,
            "emote-pose8": 15.0,
            "idle-dance-casual": 15.0,
            "emote-pose1": 15.0,
            "emote-pose3": 15.0,
            "emote-pose5": 15.0,
            "emote-cutey": 15.0,
            "emote-punkguitar": 15.0,
            "emote-zombierun": 15.0,
            "dance-jinglebell": 15.0,
            "emote-gravity": 15.0,
            "dance-icecream": 15.0,
            "dance-wrong": 15.0,
            "idle-uwu": 15.0,
            "idle-dance-tiktok4": 15.0,
            "emote-shy2": 15.0,
            "dance-anime": 15.0,
            "dance-kawai": 15.0,
            "idle-wild": 15.0,
            "emote-iceskating": 15.0,
            "emote-pose6": 15.0,
            "emote-celebrationstep": 15.0,
            "emote-creepycute": 15.0,
            "emote-frustrated": 15.0,
            "emote-pose10": 15.0,
            "sit-relaxed": 15.0,
            "emote-stargaze": 15.0,
            "emote-slap": 15.0,
            "emote-boxer": 15.0,
            "emote-headblowup": 15.0,
            "emote-kawaiigogo": 15.0,
            "emote-repose": 15.0,
            "idle-dance-tiktok7": 15.0,
            "emote-shrink": 15.0,
            "emote-pose9": 15.0,
            "emote-teleporting": 15.0,
            "dance-touch": 15.0,
            "idle-guitar": 15.0,
            "emote-gift": 15.0,
            "dance-employee": 15.0,
            "emote-kissing": 15.0,
            "dance-tiktok11": 15.0,
            "emote-cutesalute": 15.0,
            "emote-salute": 15.0
        }

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("تنظیمات با موفقیت بارگذاری شد.")
            else:
                logger.info("فایل تنظیمات یافت نشد، استفاده از تنظیمات پیش‌فرض...")
                self.config = DEFAULT_CONFIG
                self.save_config()
        except json.JSONDecodeError as e:
            logger.error(f"خطا در ساختار JSON فایل تنظیمات: {e}")
            self.config = DEFAULT_CONFIG
            self.save_config()
        except Exception as e:
            logger.error(f"خطا در بارگذاری تنظیمات: {e}")
            self.config = DEFAULT_CONFIG
            self.save_config()

    def save_config(self):
        try:
            config_to_save = self.config.copy()
            config_to_save["admin_usernames"] = list(config_to_save["admin_usernames"])
            config_to_save["vip_usernames"] = list(config_to_save["vip_usernames"])
            config_to_save["banned_users"] = list(config_to_save["banned_users"])
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            logger.info("تنظیمات با موفقیت ذخیره شد.")
        except Exception as e:
            logger.error(f"خطا در ذخیره تنظیمات: {e}")

    def get_message(self, key, **kwargs):
        messages = {
            "fa": {
                "welcome": self.config["welcome_message"],
                "invalid_command": "دستور {cmd} شناخته نشده! برای راهنما !help بزنید.",
                "no_permission": "فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!",
                "user_not_found": "کاربر {username} آنلاین نیست.",
                "invalid_format": "فرمت نادرست: {format}",
                "teleport_success": "@{username} به {location} تلپورت شد!",
                "teleport_error": "خطا در تلپورت: {error}",
                "heart_success": "{count} قلب بنفش به @{username} ارسال شد!",
                "heart_all_success": "{count} واکنش به {count} نفر ارسال شد!",
                "clap_success": "{count} clap به @{username} ارسال شد!",
                "wink_success": "{count} wink به @{username} ارسال شد!",
                "wave_success": "{count} wave به @{username} ارسال شد!",
                "thumbs_success": "{count} thumbs-up به @{username} ارسال شد!",
                "wallet_error": "خطا در دریافت موجودی: {error}",
                "tip_success": "{amount} گلد به @{username} ارسال شد.",
                "tip_all_success": "تیپ {amount} گلد به {count} نفر ارسال شد!",
                "ban_success": "@{username} بن شد!",
                "unban_success": "کاربر @{username} با موفقیت آنبن شد!",
                "unban_not_banned": "کاربر @{username} در لیست بن نیست.",
                "dancechain_success": "زنجیره رقص برای @{username} اجرا شد!",
                "addtele_success": "مکان {location} ذخیره شد!",
                "deltele_success": "مکان {location} با موفقیت حذف شد!",
                "deltele_not_found": "مکان {location} وجود ندارد!",
                "deltele_protected": "نمی‌توانید مکان پیش‌فرض {location} را حذف کنید!",
                "set_item_success": "ظاهر ربات به ایتم‌های @{username} تغییر کرد!",
                "listadd_empty": "هیچ ادمینی در لیست وجود ندارد.",
                "listadd_success": "لیست ادمین‌ها ({count} نفر):\n{admin_list}",
                "freeze_success": "کاربر @{username} فریز شد!",
                "unfreeze_success": "کاربر @{username} از حالت فریز آزاد شد!",
                "unfreeze_not_frozen": "کاربر @{username} فریز نشده است!",
                "party_success": "رقص شماره {dance_number} برای @{username} فعال شد!",
                "party_all_success": "رقص شماره {dance_number} برای {count} کاربر فعال شد!",
                "partys_success": "رقص اجباری برای @{username} متوقف شد!",
                "partys_not_dancing": "کاربر @{username} در حال رقص اجباری نیست!"
            }
        }
        return messages[self.config["language"]][key].format(**kwargs)

    async def cleanup_tasks(self):
        try:
            for username, task in self.dance_tasks.items():
                if not task.done():
                    task.cancel()
                try:
                    await task
                except CancelledError:
                    pass
            self.dance_tasks.clear()
            self.user_dances.clear()
            self.party_dances.clear()
            
            for username, task in self.frozen_users.items():
                if not task.done():
                    task.cancel()
                try:
                    await task
                except CancelledError:
                    pass
            self.frozen_users.clear()
            
            if self.announcement_task and not self.announcement_task.done():
                self.announcement_task.cancel()
                try:
                    await self.announcement_task
                except CancelledError:
                    pass
                self.announcement_task = None
            if self.score_update_task and not self.score_update_task.done():
                self.score_update_task.cancel()
                try:
                    await self.score_update_task
                except CancelledError:
                    pass
                self.score_update_task = None
            logger.info("همه وظایف ناهمزمان لغو شدند.")
        except Exception as e:
            logger.error(f"خطا در لغو وظایف: {e}")

    async def on_start(self, session_metadata):
        logger.info("ربات با موفقیت وصل شد.")
        self.user_id = getattr(session_metadata, "user_id", None)
        if not self.user_id:
            logger.error("شناسه ربات در session_metadata پیدا نشد.")
            await self.highrise.chat("خطا: شناسه ربات پیدا نشد.")
            return

        try:
            dest = Position(x=16.5, y=0.25, z=3.5)
            await self.highrise.teleport(user_id=self.user_id, dest=dest)
            await self.highrise.chat("ربات به موقعیت اولیه (x=0.5, y=1.0, z=1.5) منتقل شد!")
            logger.info("ربات به موقعیت اولیه تلپورت شد.")
        except Exception as e:
            logger.error(f"خطا در تلپورت اولیه: {e}")
            await self.highrise.chat(f"خطا در تلپورت اولیه: {e}")

        await self.sync_room_users()
        self.announcement_task = create_task(self.announcement_loop())
        self.score_update_task = create_task(self.score_update_loop())
        async def dance_loop():
            try:
                while True:
                    await self.highrise.send_emote("emote-ghost-idle", self.user_id)
                    await sleep(9.0)
            except CancelledError:
                logger.info("وظیفه رقص ربات لغو شد.")
        self.dance_tasks[self.user_id] = create_task(dance_loop())

    async def on_user_join(self, user: User, position: Position):
        username = user.username.lower()
        if username in self.config["banned_users"]:
            await self.highrise.chat(self.get_message("ban_success", username=user.username))
            return
        self.active_users[username] = user
        self.user_positions[username] = position
        self.user_scores[username] = self.user_scores.get(username, 0) + 10
        await self.highrise.chat(self.get_message("welcome", username=user.username))
        logger.info(f"کاربر {user.username} (ID: {user.id}) وارد روم شد. موقعیت: {position}")

    async def on_user_leave(self, user: User, position: Position | None = None):
        username = user.username.lower()
        self.active_users.pop(username, None)
        self.user_positions.pop(username, None)
        if username in self.dance_tasks:
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            self.user_dances.pop(username, None)
            self.party_dances.pop(username, None)
        if username in self.frozen_users:
            self.frozen_users[username].cancel()
            self.frozen_users.pop(username, None)
        await self.highrise.chat(f"@{user.username} از روم خارج شد.")
        logger.info(f"کاربر {user.username} (ID: {user.id}) از روم خارج شد. موقعیت: {position}")

    async def sync_room_users(self):
        try:
            room_users = await self.highrise.get_room_users()
            current_users = {user_data[0].username.lower(): user_data for user_data in room_users.content}
            
            for username in list(self.active_users.keys()):
                if username not in current_users:
                    self.active_users.pop(username, None)
                    self.user_positions.pop(username, None)
                    if username in self.dance_tasks:
                        self.dance_tasks[username].cancel()
                        self.dance_tasks.pop(username, None)
                    if username in self.frozen_users:
                        self.frozen_users[username].cancel()
                        self.frozen_users.pop(username, None)
                    logger.info(f"کاربر {username} از لیست‌ها حذف شد (همگام‌سازی).")
            
            for username, user_data in current_users.items():
                self.active_users[username] = user_data[0]
                self.user_positions[username] = user_data[1]
            
            logger.info(f"همگام‌سازی کاربران انجام شد. تعداد کاربران: {len(self.active_users)}. کاربران: {[user.username for user in self.active_users.values()]}")
            await self.highrise.chat(f"{len(self.active_users)} کاربر در روم شناسایی شدند.")
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی کاربران: {e}", exc_info=True)
            await self.highrise.chat("خطا در شناسایی کاربران روم.")

    async def announcement_loop(self):
        try:
            while True:
                await sleep(self.config["announcement_interval"])
                await self.highrise.chat(self.config["announcement_message"])
                logger.info("پیام اطلاع‌رسانی ارسال شد.")
        except CancelledError:
            logger.info("وظیفه اطلاع‌رسانی لغو شد.")
        except Exception as e:
            logger.error(f"خطا در حلقه اطلاع‌رسانی: {e}")

    async def score_update_loop(self):
        try:
            while True:
                await sleep(300)
                for username in self.active_users:
                    self.user_scores[username] = self.user_scores.get(username, 0) + 5
                logger.info("امتیازات کاربران به‌روزرسانی شد.")
        except CancelledError:
            logger.info("وظیفه به‌روزرسانی امتیازات لغو شد.")
        except Exception as e:
            logger.error(f"خطا در حلقه به‌روزرسانی امتیازات: {e}")

    async def on_user_move(self, user: User, position: Position):
        username = user.username.lower()
        self.user_positions[username] = position
        if username in self.config["admin_usernames"]:
            logger.info(f"ادمین {user.username} به موقعیت x={position.x}, y={position.y}, z={position.z} حرکت کرد.")
        if username in self.frozen_users:
            try:
                original_position = self.user_positions.get(username)
                if original_position:
                    await self.highrise.teleport(user_id=user.id, dest=original_position)
                    logger.info(f"کاربر {username} فریز شده به موقعیت اولیه x={original_position.x}, y={original_position.y}, z={original_position.z} بازگردانده شد.")
            except Exception as e:
                logger.error(f"خطا در بازگرداندن {username} به موقعیت فریز: {e}")

    async def on_chat(self, user: User, message: str):
        username = user.username.lower()
        msg = message.strip().lower()
        self.user_scores[username] = self.user_scores.get(username, 0) + 2

        if msg in self.emotes:
            await self.start_dance(user, self.emotes[msg])
        elif msg == "stop":
            await self.stop_dance(user)
        elif msg.startswith("!"):
            parts = msg.split()
            cmd = parts[0] if len(parts) == 1 else " ".join(parts[:2]) if parts[0] == "!item" else parts[0]
            if cmd in self.commands:
                await self.commands[cmd](user, message)
            else:
                await self.highrise.chat(self.get_message("invalid_command", cmd=cmd))

    async def on_tip(self, sender: User, receiver: User, tip):
        try:
            # بررسی ساختار شیء tip برای اطمینان از وجود ویژگی amount
            amount = getattr(tip, "amount", 0)
            await self.highrise.chat(f"@{sender.username} {amount} گلد به @{receiver.username} داد!")
            self.user_scores[sender.username.lower()] = self.user_scores.get(sender.username.lower(), 0) + amount
            logger.info(f"کاربر {sender.username} {amount} گلد به {receiver.username} تیپ داد.")
        except Exception as e:
            logger.error(f"خطا در پردازش تیپ از {sender.username} به {receiver.username}: {e}")
            await self.highrise.chat(f"خطا در پردازش تیپ از @{sender.username} به @{receiver.username}: {e}")

    async def start_dance(self, user: User, emote: str):
        username = user.username.lower()
        await self.stop_dance(user)
        self.user_dances[username] = emote
        duration = self.emote_durations.get(emote, 7.5)

        async def dance_loop():
            try:
                while self.user_dances.get(username) == emote:
                    await self.highrise.send_emote(emote, user.id)
                    await sleep(duration)
            except CancelledError:
                logger.info(f"وظیفه رقص برای {username} لغو شد.")
            except Exception as e:
                logger.error(f"خطا در حلقه رقص برای {username}: {e}")

        task = create_task(dance_loop())
        self.dance_tasks[username] = task
        logger.info(f"کاربر {username} شروع به رقص {emote} کرد.")

    async def stop_dance(self, user: User):
        username = user.username.lower()
        if username in self.party_dances and self.party_dances[username][1]:
            await self.highrise.chat(f"@{username} نمی‌توانید رقص اجباری را متوقف کنید! فقط ادمین با !partys می‌تواند آن را متوقف کند.")
            logger.info(f"کاربر {username} سعی کرد رقص اجباری را متوقف کند اما مجاز نیست.")
            return
        if username in self.dance_tasks:
            self.user_dances.pop(username, None)
            self.party_dances.pop(username, None)
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            
        
            
           

    async def cmd_help(self, user: User, message: str):
        help_text = (
            "دستورات ربات:\n"
            "1-6 - اجرای رقص\n"
            "stop - توقف رقص\n"
            "!help - نمایش راهنما\n"
            "!spam تعداد پیام - ارسال پیام اسپم\n"
            "!tele @username [vip|vip1|dj|مکان_سفارشی] - تلپورت کاربر\n"
            "!tele to @username - تلپورت به کاربر\n"
            "!tele me @username - تلپورت کاربر به ادمین\n"
            "!tele me all - تلپورت همه به ادمین\n"
            "!heart تعداد @username - ارسال قلب بنفش\n"
            "!heart all - قلب بنفش به همه\n"
            "!clap تعداد @username - ارسال clap\n"
            "!clap all - clap به همه\n"
            "!wink تعداد @username - ارسال wink\n"
            "!wink all - wink به همه\n"
            "!wave تعداد @username - ارسال wave\n"
            "!wave all - wave به همه\n"
            "!thumbs تعداد @username - ارسال thumbs-up\n"
            "!thumbs all - thumbs-up به همه\n"
            "!wallet - نمایش موجودی ربات\n"
            "!set - تلپورت ربات به ادمین\n"
            "!item set @username - تغییر ظاهر ربات به ایتم‌های کاربر\n"
            "!tip <تعداد> all - تیپ به همه\n"
            "!vip - تلپورت به VIP\n"
            "!vip1 - تلپورت به VIP1\n"
            "!dj - تلپورت به DJ\n"
            "!down - تلپورت به پایین\n"
            "!ban @username - بن کردن کاربر\n"
            "!unban @username - آنبن کردن کاربر\n"
            "!dancechain - اجرای زنجیره رقص\n"
            "!addtele نام_مکان - ذخیره مکان جدید\n"
            "!deltele نام_مکان - حذف مکان تلپورت\n"
            "!welcome پیام - تنظیم پیام خوش‌آمدگویی\n"
            "!addadmin @username - افزودن ادمین (فقط bad_qoq)\n"
            "!removeadmin @username - حذف ادمین (فقط bad_qoq)\n"
            "!listadd - نمایش لیست ادمین‌ها\n"
            "!freeze @username - فریز کردن کاربر\n"
            "!unfreeze @username - آزاد کردن کاربر از فریز\n"
            "!party @username عدد - اجرای رقص اجباری برای کاربر\n"
            "!party all عدد - اجرای رقص برای همه\n"
            "!partys @username - توقف رقص اجباری کاربر"
        )
        for chunk in [help_text[i:i+200] for i in range(0, len(help_text), 200)]:
            await self.highrise.chat(chunk)
        logger.info(f"راهنما توسط {user.username} درخواست شد.")

    async def cmd_spam(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !spam را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) < 2 or not parts[1].isdigit():
            await self.highrise.chat(self.get_message("invalid_format", format="!spam تعداد پیام"))
            logger.info(f"فرمت نادرست برای دستور !spam توسط {user.username} وارد شد.")
            return

        try:
            count = int(parts[1])
            spam_message = " ".join(parts[2:]) if len(parts) > 2 else "اسپم آزمایشی!"
            if count < 1 or count > 100:
                await self.highrise.chat("تعداد پیام‌ها باید بین 1 تا 100 باشد.")
                logger.info(f"تعداد پیام‌های نامعتبر ({count}) توسط {user.username} وارد شد.")
                return

            for _ in range(count):
                await self.highrise.chat(spam_message)
                await sleep(2.0)
            logger.info(f"{count} پیام اسپم توسط {user.username} ارسال شد: {spam_message}")
            await self.highrise.chat(f"{count} پیام اسپم ارسال شد!")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال پیام اسپم: {str(e)}")
            logger.error(f"خطا در cmd_spam برای {user.username}: {str(e)}")

    async def cmd_tele(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !tele را ندارد.")
            return

        parts = message.lower().split()
        
        if len(parts) == 3 and parts[1].startswith("@"):
            target_username = parts[1][1:].lower()
            location = parts[2]
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
                return
            if location not in self.config["teleport_locations"]:
                await self.highrise.chat(f"مکان {location} وجود ندارد!")
                logger.info(f"مکان {location} توسط {user.username} برای تلپورت پیدا نشد.")
                return
            try:
                dest_data = self.config["teleport_locations"][location]
                dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
                await self.highrise.teleport(user_id=target_user.id, dest=dest)
                await self.highrise.chat(self.get_message("teleport_success", username=target_user.username, location=location.upper()))
                logger.info(f"کاربر {target_username} به {location} تلپورت شد.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطا در تلپورت {target_username} به {location}: {e}")

        elif len(parts) == 3 and parts[1] == "to" and parts[2].startswith("@"):
            target_username = parts[2][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
                return
            try:
                position = self.user_positions.get(target_username)
                if position:
                    await self.highrise.teleport(user_id=user.id, dest=position)
                    await self.highrise.chat(f"@{user.username} به مکان @{target_user.username} تلپورت شد.")
                    logger.info(f"کاربر {user.username} به مکان {target_username} تلپورت شد.")
                else:
                    await self.highrise.chat("موقعیت کاربر در دسترس نیست.")
                    logger.info(f"موقعیت {target_username} برای تلپورت {user.username} در دسترس نیست.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطا در تلپورت به {target_username}: {e}")

        elif len(parts) == 3 and parts[1] == "me" and parts[2].startswith("@"):
            target_username = parts[2][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
                return
            try:
                position = self.user_positions.get(user.username.lower())
                if position:
                    await self.highrise.teleport(user_id=target_user.id, dest=position)
                    await self.highrise.chat(f"@{target_user.username} به مکان @{user.username} تلپورت شد.")
                    logger.info(f"کاربر {target_username} به مکان {user.username} تلپورت شد.")
                else:
                    await self.highrise.chat("موقعیت شما در دسترس نیست.")
                    logger.info(f"موقعیت {user.username} برای تلپورت {target_username} در دسترس نیست.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطا در تلپورت {target_username} به {user.username}: {e}")

        elif len(parts) == 3 and parts[1] == "me" and parts[2] == "all":
            admin_position = self.user_positions.get(user.username.lower())
            if not admin_position:
                await self.highrise.chat("موقعیت شما در دسترس نیست.")
                logger.info(f"موقعیت {user.username} برای تلپورت همه کاربران در دسترس نیست.")
                return
            try:
                successful_teleports = 0
                for username, target_user in self.active_users.items():
                    if target_user.id == user.id or target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین تلپورت آفلاین شد.")
                        continue
                    try:
                        await self.highrise.teleport(user_id=target_user.id, dest=admin_position)
                        successful_teleports += 1
                        await sleep(0.5)
                    except Exception as e:
                        logger.error(f"خطا در تلپورت {username} به {user.username}: {e}")
                await self.highrise.chat(f"{successful_teleports} کاربر به مکان @{user.username} تلپورت شدند.")
                logger.info(f"{successful_teleports} کاربر به مکان {user.username} تلپورت شدند.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطا در تلپورت همه کاربران به {user.username}: {e}")

        else:
            await self.highrise.chat(self.get_message("invalid_format", format="!tele @username [مکان] یا !tele to @username یا !tele me @username یا !tele me all"))
            logger.info(f"فرمت نادرست برای دستور !tele توسط {user.username} وارد شد.")

    async def cmd_heart(self, user: User, message: str):
        parts = message.lower().split()
        
        if parts[0] == "!heart" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("هیچ کاربری در روم آنلاین نیست!")
                    return
                reaction_id = "heart"
                successful_hearts = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین ارسال قلب آفلاین شد.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_hearts += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطا در ارسال قلب بنفش به @{target_user.username}: {e}")
                        logger.error(f"خطا در ارسال قلب به {target_user.username}: {e}")
                if successful_hearts > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_hearts))
                    logger.info(f"قلب بنفش به {successful_hearts} نفر ارسال شد.")
                else:
                    await self.highrise.chat("هیچ قلبی با موفقیت ارسال نشد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای دستور: {e}")
                logger.error(f"خطا در ارسال قلب به همه: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!heart تعداد @username یا !heart all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: تعداد باید بین 1 تا 100 باشد.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: عدد نامعتبر است.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "heart"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"کاربر @{target_user.username} آفلاین شد و قلب ارسال نشد.")
                    logger.info(f"کاربر {target_user.username} در حین ارسال قلب آفلاین شد.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("heart_success", count=count, username=target_user.username))
            logger.info(f"{count} قلب بنفش به {target_user.username} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال قلب بنفش: {e}")
            logger.error(f"خطا در ارسال قلب به {target_username}: {e}")

    async def cmd_clap(self, user: User, message: str):
        parts = message.lower().split()
        
        if parts[0] == "!clap" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("هیچ کاربری در روم آنلاین نیست!")
                    return
                reaction_id = "clap"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین ارسال clap آفلاین شد.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطا در ارسال clap به @{target_user.username}: {e}")
                        logger.error(f"خطا در ارسال clap به {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"Clap به {successful_reactions} نفر ارسال شد.")
                else:
                    await self.highrise.chat("هیچ clap با موفقیت ارسال نشد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای دستور: {e}")
                logger.error(f"خطا در ارسال clap به همه: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!clap تعداد @username یا !clap all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: تعداد باید بین 1 تا 100 باشد.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: عدد نامعتبر است.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "clap"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"کاربر @{target_user.username} آفلاین شد و clap ارسال نشد.")
                    logger.info(f"کاربر {target_user.username} در حین ارسال clap آفلاین شد.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("clap_success", count=count, username=target_user.username))
            logger.info(f"{count} clap به {target_user.username} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال clap: {e}")
            logger.error(f"خطا در ارسال clap به {target_username}: {e}")

    async def cmd_wink(self, user: User, message: str):
        parts = message.lower().split()
        
        if parts[0] == "!wink" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("هیچ کاربری در روم آنلاین نیست!")
                    return
                reaction_id = "wink"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین ارسال wink آفلاین شد.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطا در ارسال wink به @{target_user.username}: {e}")
                        logger.error(f"خطا در ارسال wink به {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"Wink به {successful_reactions} نفر ارسال شد.")
                else:
                    await self.highrise.chat("هیچ wink با موفقیت ارسال نشد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای دستور: {e}")
                logger.error(f"خطا در ارسال wink به همه: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!wink تعداد @username یا !wink all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: تعداد باید بین 1 تا 100 باشد.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: عدد نامعتبر است.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "wink"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"کاربر @{target_user.username} آفلاین شد و wink ارسال نشد.")
                    logger.info(f"کاربر {target_user.username} در حین ارسال wink آفلاین شد.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("wink_success", count=count, username=target_user.username))
            logger.info(f"{count} wink به {target_user.username} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال wink: {e}")
            logger.error(f"خطا در ارسال wink به {target_username}: {e}")

    async def cmd_wave(self, user: User, message: str):
        parts = message.lower().split()
        
        if parts[0] == "!wave" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("هیچ کاربری در روم آنلاین نیست!")
                    return
                reaction_id = "wave"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین ارسال wave آفلاین شد.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطا در ارسال wave به @{target_user.username}: {e}")
                        logger.error(f"خطا در ارسال wave به {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"Wave به {successful_reactions} نفر ارسال شد.")
                else:
                    await self.highrise.chat("هیچ wave با موفقیت ارسال نشد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای دستور: {e}")
                logger.error(f"خطا در ارسال wave به همه: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!wave تعداد @username یا !wave all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: تعداد باید بین 1 تا 100 باشد.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: عدد نامعتبر است.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "wave"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"کاربر @{target_user.username} آفلاین شد و wave ارسال نشد.")
                    logger.info(f"کاربر {target_user.username} در حین ارسال wave آفلاین شد.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("wave_success", count=count, username=target_user.username))
            logger.info(f"{count} wave به {target_user.username} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال wave: {e}")
            logger.error(f"خطا در ارسال wave به {target_username}: {e}")

    async def cmd_thumbs(self, user: User, message: str):
        parts = message.lower().split()
        
        if parts[0] == "!thumbs" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("هیچ کاربری در روم آنلاین نیست!")
                    return
                reaction_id = "thumbs-up"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین ارسال thumbs-up آفلاین شد.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطا در ارسال thumbs-up به @{target_user.username}: {e}")
                        logger.error(f"خطا در ارسال thumbs-up به {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"Thumbs-up به {successful_reactions} نفر ارسال شد.")
                else:
                    await self.highrise.chat("هیچ thumbs-up با موفقیت ارسال نشد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای دستور: {e}")
                logger.error(f"خطا در ارسال thumbs-up به همه: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!thumbs تعداد @username یا !thumbs all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: تعداد باید بین 1 تا 100 باشد.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: عدد نامعتبر است.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "thumbs-up"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"کاربر @{target_user.username} آفلاین شد و thumbs-up ارسال نشد.")
                    logger.info(f"کاربر {target_user.username} در حین ارسال thumbs-up آفلاین شد.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("thumbs_success", count=count, username=target_user.username))
            logger.info(f"{count} thumbs-up به {target_user.username} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در ارسال thumbs-up: {e}")
            logger.error(f"خطا در ارسال thumbs-up به {target_username}: {e}")

    async def cmd_wallet(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        try:
            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            else:
                logger.error("ساختار wallet ناشناخته است.")
                await self.highrise.chat("خطا: ساختار پاسخ wallet ناشناخته است.")
                return
            
            await self.highrise.chat(f"موجودی گلد ربات: {gold_amount} گلد")
            logger.info(f"موجودی ربات: {gold_amount} گلد")
        except Exception as e:
            await self.highrise.chat(self.get_message("wallet_error", error=str(e)))
            logger.error(f"خطا در دریافت موجودی: {e}")

    async def cmd_tip(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        parts = message.lower().split()
        if len(parts) != 3 or not parts[1].isdigit() or parts[2] != "all":
            await self.highrise.chat(self.get_message("invalid_format", format="!tip <تعداد> all (تعداد: 1، 5، 10، 50، 100)"))
            return

        try:
            tip_amount = int(parts[1])
            if tip_amount not in [1, 5, 10, 50, 100]:
                await self.highrise.chat("مقدار گلد باید 1، 5، 10، 50 یا 100 باشد.")
                return

            gold_bar_map = {
                1: "gold_bar_1",
                5: "gold_bar_5",
                10: "gold_bar_10",
                50: "gold_bar_50",
                100: "gold_bar_100"
            }
            gold_bar_item = gold_bar_map.get(tip_amount)
            if not gold_bar_item:
                await self.highrise.chat(f"مقدار {tip_amount} پشتیبانی نمی‌شود.")
                return

            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            else:
                logger.error("ساختار wallet ناشناخته است.")
                await self.highrise.chat("خطا: ساختار پاسخ wallet ناشناخته است.")
                return

            active_users = [u for u in self.active_users.values() if u.id != self.user_id]
            active_users_count = len(active_users)
            total_needed = tip_amount * active_users_count

            if gold_amount < total_needed:
                await self.highrise.chat(
                    f"موجودی ربات ({gold_amount} گلد) برای تیپ {tip_amount} گلد به {active_users_count} نفر کافی نیست."
                )
                return

            successful_tips = 0
            for target_user in active_users:
                if target_user.username.lower() not in self.active_users:
                    logger.info(f"کاربر {target_user.username} در حین ارسال تیپ آفلاین شد.")
                    continue
                try:
                    response = await self.highrise.tip_user(target_user.id, gold_bar_item)
                    if hasattr(response, "error"):
                        raise Exception(f"خطای API: {response.error}")
                    successful_tips += 1
                    await self.highrise.chat(self.get_message("tip_success", amount=tip_amount, username=target_user.username))
                    logger.info(f"ارسال {tip_amount} گلد به {target_user.username} موفقیت‌آمیز بود.")
                    await sleep(3.0)
                except Exception as e:
                    await self.highrise.chat(f"خطا در تیپ به @{target_user.username}: {e}")
                    logger.error(f"خطا در تیپ به {target_user.username}: {e}")

            if successful_tips > 0:
                await self.highrise.chat(self.get_message("tip_all_success", amount=tip_amount, count=successful_tips))
            else:
                await self.highrise.chat("هیچ تیپی با موفقیت ارسال نشد.")

            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            await self.highrise.chat(f"موجودی جدید ربات: {gold_amount} گلد")
            logger.info(f"موجودی جدید ربات: {gold_amount} گلد")

        except Exception as e:
            await self.highrise.chat(f"خطای ناشناخته: {e}")
            logger.error(f"خطا در cmd_tip: {e}")

    async def cmd_set(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat(f"@{user.username}: موقعیت شما مشخص نیست.")
            return
        try:
            await self.highrise.teleport(user_id=self.user_id, dest=pos)
            await self.highrise.chat(f"ربات به موقعیت @{user.username} منتقل شد.")
            logger.info(f"ربات به موقعیت {user.username} تلپورت شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در تلپورت ربات: {e}")
            logger.error(f"خطا در cmd_set: {e}")

    async def cmd_vip(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["vip"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="VIP"))
            logger.info(f"کاربر {user.username} به VIP تلپورت شد.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطا در cmd_vip: {e}")

    async def cmd_vip1(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["vip1"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="VIP1"))
            logger.info(f"کاربر {user.username} به VIP1 تلپورت شد.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطا در cmd_vip1: {e}")

    async def cmd_dj(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["dj"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="DJ"))
            logger.info(f"کاربر {user.username} به DJ تلپورت شد.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطا در cmd_dj: {e}")

    async def cmd_down(self, user: User, message: str):
        try:
            dest = Position(x=2.0, y=0.5, z=1.5)
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(f"@{user.username} به پایین رفت.")
            logger.info(f"کاربر {user.username} به مختصات x=2, y=0.5, z=1.5 تلپورت شد.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطا در cmd_down: {e}")

    async def cmd_ban(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!ban @username"))
            return
        target_username = parts[1][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return
        self.config["banned_users"].append(target_username)
        self.save_config()
        await self.highrise.chat(self.get_message("ban_success", username=target_username))
        logger.info(f"کاربر {target_username} توسط {user.username} بن شد.")

    async def cmd_unban(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !unban را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!unban @username"))
            logger.info(f"فرمت نادرست برای دستور !unban توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.config["banned_users"]:
            await self.highrise.chat(self.get_message("unban_not_banned", username=target_username))
            logger.info(f"کاربر {target_username} توسط {user.username} برای آنبن درخواست شد، اما در لیست بن نیست.")
            return

        try:
            self.config["banned_users"].remove(target_username)
            self.save_config()
            await self.highrise.chat(self.get_message("unban_success", username=target_username))
            logger.info(f"کاربر {target_username} توسط {user.username} آنبن شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در آنبن کردن کاربر @{target_username}: {str(e)}")
            logger.error(f"خطا در cmd_unban برای {target_username}: {str(e)}")

    async def cmd_dancechain(self, user: User, message: str):
        dance_list = ["dance-tiktok8", "dance-blackpink", "dance-tiktok2"]
        for emote in dance_list:
            await self.highrise.send_emote(emote, user.id)
            await sleep(self.emote_durations.get(emote, 7.5))
        await self.highrise.chat(self.get_message("dancechain_success", username=user.username))
        logger.info(f"زنجیره رقص برای {user.username} اجرا شد.")

    async def cmd_addtele(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        parts = message.lower().split()
        if len(parts) != 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!addtele نام_مکان"))
            return
        location_name = parts[1]
        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat("موقعیت شما مشخص نیست!")
            return
        self.config["teleport_locations"][location_name] = {"x": pos.x, "y": pos.y, "z": pos.z}
        self.save_config()
        await self.highrise.chat(self.get_message("addtele_success", location=location_name))
        logger.info(f"مکان {location_name} توسط {user.username} اضافه شد.")

    async def cmd_deltele(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !deltele را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!deltele نام_مکان"))
            logger.info(f"فرمت نادرست برای دستور !deltele توسط {user.username} وارد شد.")
            return

        location_name = parts[1]
        if location_name in ["vip", "vip1", "dj"]:
            await self.highrise.chat(self.get_message("deltele_protected", location=location_name))
            logger.info(f"کاربر {user.username} سعی کرد مکان پیش‌فرض {location_name} را حذف کند.")
            return

        if location_name not in self.config["teleport_locations"]:
            await self.highrise.chat(self.get_message("deltele_not_found", location=location_name))
            logger.info(f"مکان {location_name} توسط {user.username} برای حذف درخواست شد، اما وجود ندارد.")
            return

        try:
            del self.config["teleport_locations"][location_name]
            self.save_config()
            await self.highrise.chat(self.get_message("deltele_success", location=location_name))
            logger.info(f"مکان {location_name} توسط {user.username} حذف شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در حذف مکان {location_name}: {str(e)}")
            logger.error(f"خطا در cmd_deltele برای {location_name}: {str(e)}")

    async def cmd_set_item(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !item set را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 3 or not parts[2].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!item set @username"))
            logger.info(f"فرمت نادرست برای دستور !item set توسط {user.username} وارد شد.")
            return

        target_username = parts[2][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
            return

        try:
            outfit_response = await self.highrise.get_user_outfit(target_user.id)
            if not hasattr(outfit_response, "outfit") or not outfit_response.outfit:
                await self.highrise.chat(f"خطا: اطلاعات ظاهر برای @{target_username} در دسترس نیست.")
                logger.error(f"اطلاعات ظاهر برای {target_username} در دسترس نیست.")
                return

            outfit_items = outfit_response.outfit
            await self.highrise.set_outfit(outfit_items)
            await self.highrise.chat(self.get_message("set_item_success", username=target_username))
            logger.info(f"ظاهر ربات به ایتم‌های {target_username} تغییر کرد: {outfit_items}")
        except Exception as e:
            await self.highrise.chat(f"خطا در تغییر ظاهر ربات: {str(e)}")
            logger.error(f"خطا در cmd_set_item برای {target_username}: {str(e)}")

    async def cmd_welcome(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !welcome را ندارد.")
            return

        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!welcome پیام"))
            logger.info(f"فرمت نادرست برای دستور !welcome توسط {user.username} وارد شد.")
            return

        welcome_message = parts[1]
        self.config["welcome_message"] = welcome_message
        self.save_config()
        await self.highrise.chat(f"پیام خوش‌آمدگویی به '{welcome_message}' تغییر کرد.")
        logger.info(f"پیام خوش‌آمدگویی توسط {user.username} به '{welcome_message}' تغییر کرد.")

    async def cmd_addadmin(self, user: User, message: str):
        if user.username.lower() != "bad_qoq":
            await self.highrise.chat("فقط bad_qoq می‌تواند از این دستور استفاده کند!")
            logger.info(f"کاربر {user.username} سعی کرد !addadmin را اجرا کند اما دسترسی ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!addadmin @username"))
            logger.info(f"فرمت نادرست برای دستور !addadmin توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        if target_username in self.config["admin_usernames"]:
            await self.highrise.chat(f"کاربر @{target_username} قبلاً ادمین است!")
            logger.info(f"کاربر {target_username} توسط {user.username} برای افزودن به ادمین‌ها درخواست شد، اما قبلاً ادمین است.")
            return

        try:
            self.config["admin_usernames"].append(target_username)
            self.save_config()
            await self.highrise.chat(f"کاربر @{target_username} با موفقیت به ادمین‌ها اضافه شد!")
            logger.info(f"کاربر {target_username} توسط {user.username} به ادمین‌ها اضافه شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در افزودن ادمین @{target_username}: {str(e)}")
            logger.error(f"خطا در cmd_addadmin برای {target_username}: {str(e)}")

    async def cmd_removeadmin(self, user: User, message: str):
        if user.username.lower() != "bad_qoq":
            await self.highrise.chat("فقط bad_qoq می‌تواند از این دستور استفاده کند!")
            logger.info(f"کاربر {user.username} سعی کرد !removeadmin را اجرا کند اما دسترسی ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!removeadmin @username"))
            logger.info(f"فرمت نادرست برای دستور !removeadmin توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.config["admin_usernames"]:
            await self.highrise.chat(f"کاربر @{target_username} در لیست ادمین‌ها نیست!")
            logger.info(f"کاربر {target_username} توسط {user.username} برای حذف از ادمین‌ها درخواست شد، اما در لیست نیست.")
            return

        if target_username == "bad_qoq":
            await self.highrise.chat("نمی‌توانید bad_qoq را از ادمین‌ها حذف کنید!")
            logger.info(f"تلاش برای حذف bad_qoq از ادمین‌ها توسط {user.username} رد شد.")
            return

        try:
            self.config["admin_usernames"].remove(target_username)
            self.save_config()
            await self.highrise.chat(f"کاربر @{target_username} با موفقیت از ادمین‌ها حذف شد!")
            logger.info(f"کاربر {target_username} توسط {user.username} از ادمین‌ها حذف شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در حذف ادمین @{target_username}: {str(e)}")
            logger.error(f"خطا در cmd_removeadmin برای {target_username}: {str(e)}")

    async def cmd_listadd(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !listadd را ندارد.")
            return

        try:
            if not self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("listadd_empty"))
                logger.info(f"لیست ادمین‌ها خالی است. درخواست توسط {user.username}.")
                return
            admin_list = [f"@{username}" for username in self.config["admin_usernames"]]
            await self.highrise.chat(self.get_message("listadd_success", count=len(admin_list), admin_list="\n".join(admin_list)))
            logger.info(f"لیست ادمین‌ها توسط {user.username} درخواست شد: {admin_list}")
        except Exception as e:
            await self.highrise.chat(f"خطا در نمایش لیست ادمین‌ها: {str(e)}")
            logger.error(f"خطا در cmd_listadd: {str(e)}")

    async def cmd_freeze(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !freeze را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!freeze @username"))
            logger.info(f"فرمت نادرست برای دستور !freeze توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
            return

        if target_username in self.frozen_users:
            await self.highrise.chat(f"کاربر @{target_username} قبلاً فریز شده است.")
            logger.info(f"کاربر {target_username} توسط {user.username} برای فریز درخواست شد، اما قبلاً فریز شده است.")
            return

        position = self.user_positions.get(target_username)
        if not position:
            await self.highrise.chat(f"موقعیت @{target_username} در دسترس نیست.")
            logger.info(f"موقعیت {target_username} برای فریز توسط {user.username} در دسترس نیست.")
            return

        async def freeze_loop():
            try:
                while target_username in self.frozen_users:
                    if target_username not in self.active_users:
                        self.frozen_users.pop(target_username, None)
                        logger.info(f"کاربر {target_username} آفلاین شد، فریز لغو شد.")
                        break
                    await self.highrise.teleport(user_id=target_user.id, dest=position)
                    await sleep(1.0)
            except CancelledError:
                logger.info(f"وظیفه فریز برای {target_username} لغو شد.")
            except Exception as e:
                logger.error(f"خطا در حلقه فریز برای {target_username}: {e}")

        task = create_task(freeze_loop())
        self.frozen_users[target_username] = task
        await self.highrise.chat(self.get_message("freeze_success", username=target_username))
        logger.info(f"کاربر {target_username} توسط {user.username} فریز شد.")

    async def cmd_unfreeze(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !unfreeze را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!unfreeze @username"))
            logger.info(f"فرمت نادرست برای دستور !unfreeze توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.frozen_users:
            await self.highrise.chat(self.get_message("unfreeze_not_frozen", username=target_username))
            logger.info(f"کاربر {target_username} توسط {user.username} برای آنفریز درخواست شد، اما فریز نشده است.")
            return

        try:
            task = self.frozen_users.pop(target_username)
            task.cancel()
            await task
            await self.highrise.chat(self.get_message("unfreeze_success", username=target_username))
            logger.info(f"کاربر {target_username} توسط {user.username} از حالت فریز آزاد شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در آزاد کردن @{target_username}: {str(e)}")
            logger.error(f"خطا در cmd_unfreeze برای {target_username}: {str(e)}")

    async def cmd_party(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !party را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 3 or (not parts[1].startswith("@") and parts[1] != "all") or not parts[2].isdigit():
            await self.highrise.chat(self.get_message("invalid_format", format="!party @username عدد یا !party all عدد"))
            logger.info(f"فرمت نادرست برای دستور !party توسط {user.username} وارد شد.")
            return

        dance_number = parts[2]
        if dance_number not in self.emotes:
            await self.highrise.chat(f"رقص شماره {dance_number} وجود ندارد!")
            logger.info(f"رقص شماره {dance_number} توسط {user.username} نامعتبر است.")
            return

        emote = self.emotes[dance_number]
        duration = self.emote_durations.get(emote, 7.5)

        if parts[1] == "all":
            try:
                successful_dances = 0
                for username, target_user in self.active_users.items():
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"کاربر {username} در حین اجرای رقص آفلاین شد.")
                        continue
                    await self.stop_dance(target_user)  # توقف رقص قبلی
                    self.party_dances[username] = (emote, False)  # False نشان‌دهنده رقص قابل توقف توسط کاربر
                    async def dance_loop():
                        try:
                            while username in self.party_dances and self.party_dances[username][0] == emote:
                                if username not in self.active_users:
                                    self.party_dances.pop(username, None)
                                    logger.info(f"کاربر {username} آفلاین شد، رقص متوقف شد.")
                                    break
                                await self.highrise.send_emote(emote, target_user.id)
                                await sleep(duration)
                        except CancelledError:
                            logger.info(f"وظیفه رقص برای {username} لغو شد.")
                        except Exception as e:
                            logger.error(f"خطا در حلقه رقص برای {username}: {e}")
                    task = create_task(dance_loop())
                    self.dance_tasks[username] = task
                    successful_dances += 1
                    await sleep(0.5)
                await self.highrise.chat(self.get_message("party_all_success", dance_number=dance_number, count=successful_dances))
                logger.info(f"رقص شماره {dance_number} برای {successful_dances} کاربر توسط {user.username} فعال شد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای رقص برای همه: {str(e)}")
                logger.error(f"خطا در cmd_party all: {str(e)}")
        else:
            target_username = parts[1][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"کاربر هدف {target_username} توسط {user.username} پیدا نشد.")
                return
            try:
                await self.stop_dance(target_user)  # توقف رقص قبلی
                self.party_dances[target_username] = (emote, True)  # True نشان‌دهنده رقص غیرقابل توقف توسط کاربر
                async def dance_loop():
                    try:
                        while target_username in self.party_dances and self.party_dances[target_username][0] == emote:
                            if target_username not in self.active_users:
                                self.party_dances.pop(target_username, None)
                                logger.info(f"کاربر {target_username} آفلاین شد، رقص متوقف شد.")
                                break
                            await self.highrise.send_emote(emote, target_user.id)
                            await sleep(duration)
                    except CancelledError:
                        logger.info(f"وظیفه رقص برای {target_username} لغو شد.")
                    except Exception as e:
                        logger.error(f"خطا در حلقه رقص برای {target_username}: {e}")
                task = create_task(dance_loop())
                self.dance_tasks[target_username] = task
                await self.highrise.chat(self.get_message("party_success", dance_number=dance_number, username=target_username))
                logger.info(f"رقص شماره {dance_number} برای {target_username} توسط {user.username} فعال شد.")
            except Exception as e:
                await self.highrise.chat(f"خطا در اجرای رقص برای @{target_username}: {str(e)}")
                logger.error(f"خطا در cmd_party برای {target_username}: {str(e)}")

    async def cmd_partys(self, user: User, message: str):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"کاربر {user.username} دسترسی لازم برای اجرای !partys را ندارد.")
            return

        parts = message.lower().split()
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!partys @username"))
            logger.info(f"فرمت نادرست برای دستور !partys توسط {user.username} وارد شد.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.party_dances:
            await self.highrise.chat(self.get_message("partys_not_dancing", username=target_username))
            logger.info(f"کاربر {target_username} توسط {user.username} برای توقف رقص درخواست شد، اما در حال رقص اجباری نیست.")
            return

        try:
            await self.stop_dance(self.active_users[target_username])
            self.party_dances.pop(target_username, None)
            await self.highrise.chat(self.get_message("partys_success", username=target_username))
            logger.info(f"رقص اجباری برای {target_username} توسط {user.username} متوقف شد.")
        except Exception as e:
            await self.highrise.chat(f"خطا در توقف رقص برای @{target_username}: {str(e)}")
            logger.error(f"خطا در cmd_partys برای {target_username}: {str(e)}")

async def main():
    logger.info("تلاش برای بارگذاری متغیرهای محیطی...")
    room_id = os.getenv("ROOM_ID", "68a74f38943256ad973e46c6")
    api_token = os.getenv("API_TOKEN", "939100bea8022e1435282617add7a89d58c8e1c497beee1292d1d5f486efa701")
    
    if not room_id or not api_token:
        logger.error("ROOM_ID یا API_TOKEN تنظیم نشده‌اند.")
        return
    
    logger.info(f"ROOM_ID: {room_id}")
    logger.info(f"API_TOKEN: {api_token}")
    
    bot_def = BotDefinition(room_id=room_id, api_token=api_token, bot=AdvancedBot())
    
    max_reconnect_attempts = 5
    attempt = 0
    while attempt < max_reconnect_attempts:
        try:
            logger.info("تلاش برای اتصال به سرور Highrise...")
            from highrise.__main__ import main as highrise_main
            await highrise_main([bot_def])
        except aiohttp.client_exceptions.ClientConnectionResetError as e:
            logger.error(f"اتصال WebSocket قطع شد: {e}")
            await bot_def.bot.cleanup_tasks()
            attempt += 1
            logger.info(f"تلاش برای اتصال مجدد ({attempt}/{max_reconnect_attempts}) پس از 10 ثانیه...")
            await sleep(10)
        else:
            attempt = 0
    logger.error("حداکثر تلاش‌های اتصال مجدد به پایان رسید.")

if __name__ == "__main__":
    import asyncio
    logger.info("شروع اجرای ربات...")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"خطا در اجرای اولیه: {e}", exc_info=True)