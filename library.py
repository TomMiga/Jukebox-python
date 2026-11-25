import os
import sqlite3
import hashlib
import requests
import re
import time
import unicodedata
from collections import defaultdict
from mutagen import File
from PIL import Image
from io import BytesIO
import config

FIRST_NAMES = {
    # České a slovenské mužské
    "adam", "ales", "alexandr", "alois", "antonin", "bedrich", "bohumil", "bohuslav",
    "borek", "boris", "bretislav", "bronislav", "cecil", "ctibor", "ctirad", "dalibor",
    "dan", "daniel", "david", "dominik", "drahomir", "dusan", "eduard", "emil", "erik",
    "evzen", "ferdinand", "filip", "frantisek", "gabriel", "gustav", "hanus", "havel",
    "hynek", "ignac", "igor", "ivan", "ivo", "jachym", "jakub", "jan", "jarmil",
    "jaromir", "jaroslav", "jindrich", "jiri", "jonas", "josef", "jozef", "julius",
    "kamil", "karel", "karol", "kazimir", "krystof", "kvido", "ladislav", "leos",
    "libor", "lubomir", "lubos", "ludek", "ludvik", "lukas", "lumir", "marcel", "marek",
    "marian", "martin", "matej", "matous", "max", "maxmilian", "michal", "mikulas",
    "milan", "milos", "miloslav", "mirek", "miroslav", "mojmir", "norbert", "oldrich",
    "oleg", "oliver", "ondrej", "oskar", "ota", "otakar", "otmar", "pavel", "pavol",
    "petr", "peter", "premysl", "prokop", "radek", "radim", "radomir", "radoslav",
    "radovan", "rastislav", "rene", "richard", "robert", "robin", "roman", "rostislav",
    "rudolf", "rehor", "samuel", "slavomir", "sobeslav", "stanislav", "stepan",
    "svatopluk", "svatoslav", "tadeas", "teodor", "tibor", "tomas", "vaclav", "valdemar",
    "vavrinec", "vendelin", "viktor", "vilem", "vincenc", "vit", "vitezslav", "vladimir",
    "vladislav", "vlastimil", "vojtech", "vratislav", "zbynek", "zdenek", "zdeno",
    # České a slovenské ženské
    "adela", "agata", "alena", "alexandra", "alice", "alzbeta", "amalie", "anastazie",
    "andrea", "aneta", "anezka", "anna", "antonie", "barbora", "beata", "bernadeta",
    "berta", "blanka", "blazena", "bohumila", "bohuslava", "bozena", "brigita",
    "cecilie", "dagmar", "dana", "daniela", "darina", "denisa", "diana", "dita",
    "dobromila", "dominika", "dorota", "doubravka", "drahomira", "elena", "eliska",
    "ema", "emilie", "erika", "ester", "eva", "evelina", "frantiska", "gabriela",
    "hana", "hedvika", "helena", "ilona", "irena", "iva", "ivana", "iveta", "ivona",
    "izabela", "jana", "jarmila", "jaroslava", "jindriska", "jirina", "jitka",
    "johana", "jolana", "judita", "julie", "kamila", "karolina", "katarina", "katerina",
    "klara", "klaudie", "kristina", "kristyna", "kveta", "kvetoslava", "lada", "laura",
    "lenka", "leona", "libuse", "liliana", "linda", "ljuba", "lucia", "lucie",
    "ludmila", "lydie", "magdalena", "mahulena", "marcela", "margita", "marie",
    "marketa", "marta", "martina", "michaela", "milada", "milena", "miloslava",
    "miluse", "miroslava", "monika", "nadezda", "natalie", "nela", "nikol", "nikola",
    "nina", "nora", "olga", "olivie", "otilie", "patricie", "pavla", "pavlina",
    "petra", "radana", "radka", "renata", "romana", "ruzena", "sabina", "sandra",
    "sara", "sarka", "sarlota", "silvie", "simona", "slavomira", "sona", "stanislava",
    "stela", "stepanka", "suzana", "svetlana", "tamara", "tatana", "tereza", "vendula",
    "vera", "veronika", "viktorie", "vilemina", "vlasta", "zdenka", "zdislava",
    "zofie", "zuzana",
    # Zahraniční sólisté
    "michael", "elvis", "freddie", "john", "paul", "george", "ringo", "david", "elton",
    "eric", "phil", "sting", "bryan", "bruce", "bob", "billy", "frank", "dean",
    "robbie", "ed", "justin", "bruno", "enrique", "ricky", "shakira", "celine",
    "whitney", "mariah", "madonna", "britney", "christina", "taylor", "katy", "adele",
    "amy", "tina", "cher", "donna", "diana", "janet", "kylie", "rihanna", "beyonce",
    "ozzy", "alice", "marilyn", "kurt", "chester", "james", "lars", "kirk", "bon",
}

HYPHEN_BANDS = {
    "ac-dc", "a-ha", "jay-z", "ne-yo", "t-rex", "b-52s", "blink-182",
    "alt-j", "g-eazy", "k-os", "x-ray", "c-block", "e-type", "u-96",
}

# Slovník oprav častých překlepů, zkomolenin a zkratek u české, slovenské i světové scény
ARTIST_ALIASES = {
    # Wanastowi Vjecy
    "wanastovy vjeci": "Wanastowi Vjecy",
    "wanastovy vjecy": "Wanastowi Vjecy",
    "wanastowi vjeci": "Wanastowi Vjecy",
    "vanastovy vjeci": "Wanastowi Vjecy",
    "vanastowi vjecy": "Wanastowi Vjecy",
    # Holki
    "holky": "Holki",
    "diskografie (1999": "Holki",
    "2009)(flac)": "Holki",
    # Hradišťan
    "diskografie (1972": "Hradišťan",
    "hradistan": "Hradišťan",
    # Yo Yo Band
    "yoyo band": "Yo Yo Band",
    "jojo band": "Yo Yo Band",
    "jo jo band": "Yo Yo Band",
    # Těžkej Pokondr
    "tezkej pokonder": "Těžkej Pokondr",
    "tezkej pokondr": "Těžkej Pokondr",
    "tezky pokondr": "Těžkej Pokondr",
    # Škwor
    "skvor": "Škwor",
    "skwor": "Škwor",
    # Horkýže Slíže
    "horkyze slize": "Horkýže Slíže",
    "horkize slize": "Horkýže Slíže",
    # Divokej Bill
    "divoky bill": "Divokej Bill",
    "divokej bil": "Divokej Bill",
    # Visací zámek
    "visaci zamek": "Visací zámek",
    "visaci zamky": "Visací zámek",
    # Tři sestry
    "tri sestry": "Tři sestry",
    "3 sestry": "Tři sestry",
    # Pražský výběr
    "prazsky vyber": "Pražský výběr",
    # Žlutý pes
    "zluty pes": "Žlutý pes",
    # Čechomor
    "cechomor": "Čechomor",
    "ceskomoravska hudebni spolecnost": "Čechomor",
    "ceskomoravska hudebni spolecnocechomor": "Čechomor",
    # Mňága a Žďorp
    "mnaga a zdorp": "Mňága a Žďorp",
    "mnaga zdorp": "Mňága a Žďorp",
    # Sto zvířat
    "sto zvirat": "Sto zvířat",
    "100 zvirat": "Sto zvířat",
    # Mig 21
    "mig21": "Mig 21",
    # J.A.R. & P.S.
    "jar": "J.A.R.",
    "j.a.r": "J.A.R.",
    "ps": "P.S.",
    "p.s": "P.S.",
    # No Name
    "noname": "No Name",
    # Inekafe
    "ine kafe": "Inekafe",
    # Olympic
    "olympik": "Olympic",
    "olympic diskografia": "Olympic",
    # Kabát
    "kabat": "Kabát",
    # Chinaski
    "chinasky": "Chinaski",
    # Kryštof
    "krystof": "Kryštof",
    # Support Lesbiens
    "support lesbians": "Support Lesbiens",
    "suport lesbiens": "Support Lesbiens",
    # Monkey Business
    "monkey busines": "Monkey Business",
    # Wohnout
    "vohnout": "Wohnout",
    # Harlej
    "harley": "Harlej",
    # Alkehol
    "alkohol": "Alkehol",
    # Arakain
    "arakajn": "Arakain",
    # Blue Effect
    "modry efekt": "Blue Effect",
    # Team
    "tim": "Team",
    # Folk & Country legendy a sjednocení variant
    "zelenaci": "Greenhorns",
    "novi zelenaci": "Greenhorns",
    "plavci": "Rangers",
    "the rangers": "Rangers",
    "nedved": "Nedvědi",
    "nedvedi": "Nedvědi",
    "bratri nedvedove": "Nedvědi",
    "honza nedved": "Nedvěd Jan",
    "honza medved": "Nedvěd Jan",
    "j.nedved": "Nedvěd Jan",
    "f.nedved": "Nedvěd František",
    "honza vycital": "Vyčítal Honza",
    "jan vycital": "Vyčítal Honza",
    "jarek nohavica": "Nohavica Jaromír",
    "jarek nohavoca": "Nohavica Jaromír",
    "nohavica": "Nohavica Jaromír",
    "nohavica jarek": "Nohavica Jaromír",
    "j.nohavica": "Nohavica Jaromír",
    "j. nohavica": "Nohavica Jaromír",
    "jaromir nohavica": "Nohavica Jaromír",
    "bratri ebenove": "Bratři Ebenové",
    "z. navarova": "Navarová Zuzana",
    "z.navarova": "Navarová Zuzana",
    "navarova zuzana": "Navarová Zuzana",
    "zuzana navarova": "Navarová Zuzana",
    "plihal ka": "Plíhal Karel",
    "karel plihal": "Plíhal Karel",
    "k.plihal": "Plíhal Karel",
    "pavel zalman lohonka": "Žalman",
    "zalman": "Žalman",
    "pavel dobes": "Dobeš Pavel",
    "hudka jaroslav": "Hutka Jaroslav",
    "jaroslav hutka": "Hutka Jaroslav",
    "brontosauri iii": "Brontosauři",
    "brontosauri": "Brontosauři",
    "spiritual kvintet": "Spirituál Kvintet",
    "michal tucny": "Tučný Michal",
    "m.tucny": "Tučný Michal",
    "wabi danek": "Daněk Wabi",
    "vlasta redl": "Redl Vlasta",
    "jiri schmitzer": "Schmitzer Jiří",
    "ivo jahelka": "Jahelka Ivo",
    "vladimir merta": "Merta Vladimír",
    "petr skoumal": "Skoumal Petr",
    "jaroslav samson lenk": "Lenk Jaroslav Samson",
    "slavek janousek": "Janoušek Slávek",
    "v.visotsky": "Vysotsky Vladimir",
    "v.vysockij": "Vysotsky Vladimir",
    "vladimir vysockij": "Vysotsky Vladimir",
    "владимир высоцкий": "Vysotsky Vladimir",
    # Sólo interpreti a časté zkratky křestních jmen
    "m.david": "David Michal",
    "m. david": "David Michal",
    "michal david": "David Michal",
    "k.gott": "Gott Karel",
    "k. gott": "Gott Karel",
    "karel gott": "Gott Karel",
    "d.landa": "Landa Daniel",
    "d. landa": "Landa Daniel",
    "daniel landa": "Landa Daniel",
    "l.bila": "Bílá Lucie",
    "l. bila": "Bílá Lucie",
    "lucie bila": "Bílá Lucie",
    "h.vondrackova": "Vondráčková Helena",
    "h. vondrackova": "Vondráčková Helena",
    "helena vondrackova": "Vondráčková Helena",
    "h.zagorova": "Zagorová Hana",
    "h. zagorova": "Zagorová Hana",
    "hana zagorova": "Zagorová Hana",
    "v.neckar": "Neckář Václav",
    "v. neckar": "Neckář Václav",
    "vaclav neckar": "Neckář Václav",
    "w.matuska": "Matuška Waldemar",
    "w. matuska": "Matuška Waldemar",
    "waldemar matuska": "Matuška Waldemar",
    "k.kryl": "Kryl Karel",
    "k. kryl": "Kryl Karel",
    "karel kryl": "Kryl Karel",
    "p.muk": "Muk Petr",
    "p. muk": "Muk Petr",
    "petr muk": "Muk Petr",
    "p.hapka": "Hapka Petr",
    "p. hapka": "Hapka Petr",
    "petr hapka": "Hapka Petr",
    "r.muller": "Müller Richard",
    "r. muller": "Müller Richard",
    "richard muller": "Müller Richard",
    "muller richard": "Müller Richard",
    "m.zbirka": "Žbirka Miro",
    "m. zbirka": "Žbirka Miro",
    "miro zbirka": "Žbirka Miro",
    "miroslav zbirka": "Žbirka Miro",
    "meky zbirka": "Žbirka Miro",
    "p.habera": "Habera Pavol",
    "p. habera": "Habera Pavol",
    "pavol habera": "Habera Pavol",
    "palo habera": "Habera Pavol",
    "j.ledeky": "Ledecký Janek",
    "janek ledecky": "Ledecký Janek",
    "j.kalousek": "Kalousek Jan",
    "jan kalousek": "Kalousek Jan",
    "v.patejdl": "Patejdl Vašo",
    "vaso patejdl": "Patejdl Vašo",
    "j.raz": "Ráž Jožo",
    "jozo raz": "Ráž Jožo",
    "i.bartosova": "Bartošová Iveta",
    "iveta bartosova": "Bartošová Iveta",
    "b.basikova": "Basiková Bára",
    "bara basikova": "Basiková Bára",
    "barbora basikova": "Basiková Bára",
    "a.langerova": "Langerová Aneta",
    "aneta langerova": "Langerová Aneta",
    "e.farna": "Farna Ewa",
    "ewa farna": "Farna Ewa",
    "eva farna": "Farna Ewa",
    "t.klus": "Klus Tomáš",
    "tomas klus": "Klus Tomáš",
    "xindl x": "Xindl X",
    "xindlx": "Xindl X",
    # Zahraniční časté překlepy
    "aphrodites childs": "Aphrodite's Child",
    "aphrodites child": "Aphrodite's Child",
    "aphrodite's childs": "Aphrodite's Child",
    "new golden kids": "Golden Kids",
}


def fix_mojibake(text):
    if not text:
        return ""
    s = str(text)

    multi_replacements = [
        ("ã\x81i", "á"), ("Ã\x81i", "á"), ("ã\x89i", "é"), ("ã\x8di", "í"),
        ("ã\x93i", "ó"), ("ã\x9ai", "ú"), ("ã\x9di", "ý"),
        ("ãi", "á"), ("Ã¡", "á"), ("Ã\xad", "í"), ("Ã©", "é"), ("Ã½", "ý"),
        ("Ãº", "ú"), ("Å¯", "ů"), ("Ä\x8d", "č"), ("Ä\x9b", "ě"), ("Å\x88", "ň"),
        ("Å\x99", "ř"), ("Å¡", "š"), ("Å¥", "ť"), ("Å¾", "ž"), ("Ã\x81", "Á"),
        ("Ä\x8c", "Č"), ("Ä\x8e", "Ď"), ("Ã\x89", "É"), ("Ä\x9a", "Ě"), ("Ã\x8d", "Í"),
        ("Å\x87", "Ň"), ("Ã\x93", "Ó"), ("Å\x98", "Ř"), ("Å\xa0", "Š"), ("Å¤", "Ť"),
        ("Ã\x9a", "Ú"), ("Å®", "Ů"), ("Ã\x9d", "Ý"), ("Å½", "Ž"),
        ("\x9a", "š"), ("\x8a", "Š"), ("\x9e", "ž"), ("\x8e", "Ž"),
        ("\x9d", "ť"), ("\x8d", "Ť"), ("\x9f", "ź"), ("\x8f", "Ź"),
    ]
    for bad, good in multi_replacements:
        s = s.replace(bad, good)

    iso_table = str.maketrans({
        "è": "č", "È": "Č",
        "ø": "ř", "Ø": "Ř",
        "ì": "ě", "Ì": "Ě",
        "ò": "ň", "Ò": "Ň",
        "ù": "ů", "Ù": "Ů",
        "ï": "ď", "Ï": "Ď",
        "»": "ť", "«": "Ť",
        "¾": "ž", "®": "Ž",
        "¹": "š", "©": "Š",
        "µ": "ľ", "¥": "Ľ",
    })
    s = s.translate(iso_table)

    s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
    return s


def strip_diacritics(text):
    if not text:
        return ""
    text = fix_mojibake(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def czech_sort_key(text):
    if not text:
        return ()
    s = fix_mojibake(text).lower()
    s = s.replace("ch", "h\uffff")
    base = strip_diacritics(s)
    return (base, s)


def czech_collation(a, b):
    ka = czech_sort_key(a)
    kb = czech_sort_key(b)
    if ka < kb:
        return -1
    if ka > kb:
        return 1
    return 0


def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.create_collation("CZECH", czech_collation)
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            track_num INTEGER,
            duration REAL,
            cover_path TEXT,
            mtime REAL,
            origin TEXT,
            play_count INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS track_artists (
            track_id INTEGER,
            artist TEXT,
            PRIMARY KEY (track_id, artist),
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        )
    """)
    for col_sql in [
        "ALTER TABLE tracks ADD COLUMN origin TEXT",
        "ALTER TABLE tracks ADD COLUMN mtime REAL",
        "ALTER TABLE tracks ADD COLUMN play_count INTEGER DEFAULT 0",
    ]:
        try:
            c.execute(col_sql)
        except Exception:
            pass

    c.execute("CREATE INDEX IF NOT EXISTS idx_artist ON tracks(artist)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_album ON tracks(album)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_genre ON tracks(genre)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_path ON tracks(path)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_origin ON tracks(origin)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_play_count ON tracks(play_count)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ta_artist ON track_artists(artist)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ta_track ON track_artists(track_id)")
    conn.commit()
    conn.close()


def is_junk_artist(value):
    if not value:
        return True
    v = value.strip()
    if not v:
        return True
    low = strip_diacritics(v).lower()
    junk_exact = {
        "unknown", "unknown artist", "neznamy", "neznamy interpret", "neni interpret",
        "no artist", "artist", "new artist", "various", "various artists",
        "ruzni", "ruzni interpreti", "ruzni autori",
        "v lucerne", "v helena", "va",
        "folk", "folk tramp", "barvy ceskeho folku", "barvy_ceskeho_folku",
        "trampska oaza", "trampske", "tramske pisne od stare reky",
        "legendy", "obzor trutnov",
        # Útržky názvů skladeb omylem uložené v poli interpreta u výběrovek
        "abych tu", "bajecna", "byt hlidacem ru", "modra z d",
        "pacientsky", "pivni", "vyju",
    }
    if low in junk_exact:
        return True
    if low.startswith("mix cd") or low.startswith("diskografie"):
        return True
    if "(flac)" in low or "(mp3)" in low or low.startswith("(") or low.endswith(")"):
        return True
    if re.match(r"^\d{1,2}(\s+|$|\.|[a-z])", low):
        return True
    return False


def format_single_artist(name):
    if not name:
        return "Neznámý interpret"
    name = fix_mojibake(name)
    name = re.sub(r"\s+", " ", name).strip(" -_,;/")
    if not name or is_junk_artist(name):
        return "Neznámý interpret"

    alias_key = strip_diacritics(name).lower()
    if alias_key in ARTIST_ALIASES:
        return ARTIST_ALIASES[alias_key]

    known_acronyms = {"ABBA", "AC/DC", "AC-DC", "DJ", "MC", "INXS", "U2", "REM", "ZZ", "ELO", "BZN", "EWA", "J.A.R.", "P.S.", "PSH"}
    words = name.split(" ")
    cleaned_words = []
    for w in words:
        if w.upper() in known_acronyms:
            cleaned_words.append(w.upper())
        else:
            cleaned_words.append(w.capitalize())
    name = " ".join(cleaned_words)
    name = name.replace("'S", "'s").replace("'T", "'t")

    parts = name.split(" ")
    if len(parts) == 2:
        w1_norm = strip_diacritics(parts[0]).lower()
        w2_norm = strip_diacritics(parts[1]).lower()
        if w1_norm in FIRST_NAMES and w2_norm not in FIRST_NAMES:
            name = f"{parts[1]} {parts[0]}"

    alias_after = strip_diacritics(name).lower()
    if alias_after in ARTIST_ALIASES:
        return ARTIST_ALIASES[alias_after]

    return name


def split_artists(raw_artist, track_title=None):
    if not raw_artist:
        return ["Neznámý interpret"]

    text = fix_mojibake(str(raw_artist)).strip()
    if not text or is_junk_artist(text):
        return ["Neznámý interpret"]

    # Ochrana známých kapel s pomlčkou nebo aliasem ještě před dělením podle "-"
    low_clean = strip_diacritics(text).lower()
    if low_clean in HYPHEN_BANDS:
        return [format_single_artist(text)]
    if low_clean in ARTIST_ALIASES:
        return [ARTIST_ALIASES[low_clean]]

    # Pokud je v poli Artist uložené "Interpret-Název skladby" (bez mezer kolem pomlčky)
    if "-" in text and " - " not in text:
        left, right = text.split("-", 1)
        left_clean = left.strip()
        right_clean = right.strip()
        if left_clean and right_clean:
            title_norm = strip_diacritics(track_title or "").lower()
            right_norm = strip_diacritics(right_clean).lower()
            if (title_norm and (right_norm in title_norm or title_norm in right_norm)) or (
                len(right_clean.split()) >= 2 and strip_diacritics(left_clean).lower() not in FIRST_NAMES
            ):
                text = left_clean

    separators = [
        r"\s+feat\.?\s+",
        r"\s+ft\.?\s+",
        r"\s+featuring\s+",
        r"\s+with\s+",
        r"\s+vs\.?\s+",
        r"\s+a\s+",
        r"\s+and\s+",
        r"\s*-\s*",
        r"\s*&\s*",
        r"\s*\+\s*",
        r"\s*/\s*",
        r"\s*;\s*",
        r"\s*,\s*",
        r"\s*%\s*",
    ]
    pattern = "|".join(separators)
    parts = re.split(pattern, text, flags=re.IGNORECASE)

    title_norm = strip_diacritics(track_title or "").lower().strip()

    result = []
    seen = set()
    for p in parts:
        p_norm = strip_diacritics(p).lower().strip()
        if title_norm and len(p_norm) >= 4 and (p_norm == title_norm or p_norm in title_norm):
            continue
        formatted = format_single_artist(p)
        key = strip_diacritics(formatted).lower()
        if formatted and formatted != "Neznámý interpret" and key not in seen:
            seen.add(key)
            result.append(formatted)

    return result if result else ["Neznámý interpret"]


def score_variant(name):
    czech_chars = set("áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ")
    score = 0
    score += sum(30 for c in name if c in czech_chars)
    score -= sum(50 for c in name if ord(c) > 127 and c not in czech_chars)
    if not name.isupper():
        score += 10
    score += len(name)
    return score


def extract_folder_artist(path, base_dir=None):
    base = base_dir if base_dir else config.MUSIC_DIR
    try:
        rel = os.path.relpath(os.path.dirname(path), base)
    except Exception:
        rel = os.path.dirname(path)
    parts = rel.split(os.sep)
    if len(parts) >= 2 and parts[0].lower() in ("czask", "cizí", "cizi", "foreign"):
        return parts[1]
    if len(parts) >= 1 and parts[0] not in (".", "..", ""):
        return parts[0]
    return "Neznámý interpret"


def normalize_album_name(artist, album):
    if not album:
        return "Neznámé album"
    s = fix_mojibake(album).strip()
    art_tokens = [t for t in strip_diacritics(artist).lower().split() if len(t) >= 3]

    for sep in (" - ", "-"):
        if sep in s:
            left, right = s.split(sep, 1)
            left_norm = strip_diacritics(left).lower()
            if any(tok in left_norm for tok in art_tokens):
                s = right.strip()
                break

    return s if s else "Neznámé album"


def unify_artists_in_db(conn=None):
    close_after = False
    if conn is None:
        conn = get_db()
        close_after = True

    c = conn.cursor()

    rows = c.execute("SELECT id, path, artist, title, album FROM tracks").fetchall()
    c.execute("DELETE FROM track_artists")
    for row in rows:
        tid = row["id"]
        clean_title = fix_mojibake(row["title"])

        raw_art = fix_mojibake(row["artist"])
        if is_junk_artist(raw_art):
            raw_art = extract_folder_artist(row["path"])

        artists = split_artists(raw_art, track_title=clean_title)
        primary = artists[0]
        clean_album = normalize_album_name(primary, row["album"])

        c.execute(
            "UPDATE tracks SET artist = ?, title = ?, album = ? WHERE id = ?",
            (primary, clean_title, clean_album, tid),
        )
        for art in artists:
            c.execute(
                "INSERT OR IGNORE INTO track_artists (track_id, artist) VALUES (?, ?)",
                (tid, art),
            )

    rows = c.execute("SELECT DISTINCT artist FROM track_artists").fetchall()
    groups = defaultdict(list)
    for r in rows:
        a = r["artist"]
        key = strip_diacritics(a).lower()
        groups[key].append(a)

    merged_count = 0
    for key, variants in groups.items():
        if len(variants) <= 1:
            continue
        best = max(variants, key=score_variant)
        for v in variants:
            if v == best:
                continue
            c.execute(
                "INSERT OR IGNORE INTO track_artists (track_id, artist) "
                "SELECT track_id, ? FROM track_artists WHERE artist = ?",
                (best, v),
            )
            c.execute("DELETE FROM track_artists WHERE artist = ?", (v,))
            c.execute("UPDATE tracks SET artist = ? WHERE artist = ?", (best, v))
            merged_count += 1

    all_artists = [r["artist"] for r in c.execute("SELECT DISTINCT artist FROM track_artists").fetchall()]
    by_surname = defaultdict(list)
    for a in all_artists:
        parts = a.split(" ")
        if len(parts) == 2:
            surname_key = strip_diacritics(parts[0]).lower()
            by_surname[surname_key].append(a)

    for a in all_artists:
        parts = a.split(" ")
        if len(parts) == 1:
            key = strip_diacritics(a).lower()
            if len(by_surname[key]) == 1:
                target = by_surname[key][0]
                c.execute(
                    "INSERT OR IGNORE INTO track_artists (track_id, artist) "
                    "SELECT track_id, ? FROM track_artists WHERE artist = ?",
                    (target, a),
                )
                c.execute("DELETE FROM track_artists WHERE artist = ?", (a,))
                c.execute("UPDATE tracks SET artist = ? WHERE artist = ?", (target, a))
                merged_count += 1

    alb_rows = c.execute("SELECT DISTINCT artist, album FROM tracks").fetchall()
    alb_groups = defaultdict(list)
    for r in alb_rows:
        akey = (r["artist"], strip_diacritics(r["album"]).lower())
        alb_groups[akey].append(r["album"])

    for (art, _), variants in alb_groups.items():
        if len(variants) <= 1:
            continue
        best_alb = max(variants, key=score_variant)
        for v in variants:
            if v != best_alb:
                c.execute(
                    "UPDATE tracks SET album = ? WHERE artist = ? AND album = ?",
                    (best_alb, art, v),
                )

    if close_after:
        conn.commit()
        conn.close()
    return merged_count


def detect_origin(path):
    path_lower = path.lower()
    parts = path_lower.split(os.sep)
    for part in parts:
        if part in ("czask", "cz_sk", "cz-sk", "cesko", "česko"):
            return "CZ"
        if part in ("cizí", "cizi", "foreign", "zahranicni", "zahraniční", "world"):
            return "Foreign"
    return "Unknown"


def get_embedded_cover(audio):
    try:
        if hasattr(audio, "pictures") and audio.pictures:
            return audio.pictures[0].data
        if audio.tags:
            for key in audio.tags.keys():
                if key.startswith("APIC") or key.startswith("covr"):
                    return audio.tags[key].data
    except Exception:
        pass
    return None


def find_folder_cover(album_dir):
    if not os.path.isdir(album_dir):
        return None
    valid_ext = {".jpg", ".jpeg", ".png"}
    preferred_names = ["cover", "folder", "albumart", "front", "album", "coverart"]
    try:
        files = os.listdir(album_dir)
    except Exception:
        return None
    for fname in files:
        name, ext = os.path.splitext(fname)
        if ext.lower() in valid_ext and name.lower() in preferred_names:
            path = os.path.join(album_dir, fname)
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                pass
    for fname in files:
        name, ext = os.path.splitext(fname)
        if ext.lower() in valid_ext:
            path = os.path.join(album_dir, fname)
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                pass
    return None


def _artist_search_variants(artist):
    variants = [artist]
    parts = artist.split(" ")
    if len(parts) == 2:
        reversed_name = f"{parts[1]} {parts[0]}"
        if reversed_name not in variants:
            variants.append(reversed_name)
    return variants


def _clean_album_for_search(artist, album):
    s = normalize_album_name(artist, album)
    s = re.sub(r"[\(\[].*?[\)\]]", "", s)
    s = re.sub(r"\b(cd|disc|disk)\s*\d+\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d{1,2}\s*[-–.]\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -_:,")
    return s if len(s) >= 2 else album


def _album_words_match(local_album, remote_album):
    stop_words = {"the", "a", "an", "of", "and", "in", "on", "to", "for", "cd", "vol", "volume", "disc"}
    loc_norm = strip_diacritics(local_album).lower()
    rem_norm = strip_diacritics(remote_album).lower()

    if not loc_norm or not rem_norm:
        return False

    if loc_norm in rem_norm or rem_norm in loc_norm:
        return True

    loc_words = [w for w in re.findall(r"[a-z0-9]+", loc_norm) if len(w) >= 2 and w not in stop_words]
    rem_words = [w for w in re.findall(r"[a-z0-9]+", rem_norm) if len(w) >= 2 and w not in stop_words]

    if not loc_words or not rem_words:
        return loc_norm[:4] == rem_norm[:4]

    common = set(loc_words) & set(rem_words)
    if common:
        return True

    for lw in loc_words:
        for rw in rem_words:
            if len(lw) >= 4 and len(rw) >= 4 and lw[:4] == rw[:4]:
                return True
    return False


def download_from_deezer(artist, album):
    clean_alb = _clean_album_for_search(artist, album)

    for art_query in _artist_search_variants(artist):
        art_tokens = [tok for tok in strip_diacritics(art_query).lower().split() if len(tok) >= 3]
        try:
            params = {
                "q": f'artist:"{art_query}" album:"{clean_alb}"',
                "limit": 10,
            }
            r = requests.get("https://api.deezer.com/search/album", params=params, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()

            if not data.get("data"):
                r = requests.get(
                    "https://api.deezer.com/search/album",
                    params={"q": f"{art_query} {clean_alb}", "limit": 10},
                    timeout=10,
                )
                data = r.json()

            for result in data.get("data", []):
                res_art = strip_diacritics(result.get("artist", {}).get("name", "")).lower()
                res_alb = result.get("title", "")

                art_match = any(tok in res_art for tok in art_tokens)
                alb_match = _album_words_match(clean_alb, res_alb)

                if art_match and alb_match:
                    img_url = result.get("cover_xl") or result.get("cover_big") or result.get("cover_medium")
                    if img_url:
                        img_r = requests.get(img_url, timeout=10)
                        if img_r.status_code == 200 and len(img_r.content) > 2000:
                            return img_r.content, "Deezer"
        except Exception:
            pass
    return None, None


def download_from_itunes(artist, album):
    clean_alb = _clean_album_for_search(artist, album)

    queries = []
    for art_v in _artist_search_variants(artist):
        queries.append((art_v, clean_alb))
        queries.append((strip_diacritics(art_v), strip_diacritics(clean_alb)))

    seen_q = set()
    for art_query, alb_query in queries:
        if (art_query, alb_query) in seen_q:
            continue
        seen_q.add((art_query, alb_query))

        art_tokens = [tok for tok in strip_diacritics(art_query).lower().split() if len(tok) >= 3]
        try:
            params = {
                "term": f"{art_query} {alb_query}",
                "media": "music",
                "entity": "album",
                "limit": 10,
            }
            r = requests.get("https://itunes.apple.com/search", params=params, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()

            for result in data.get("results", []):
                res_art = strip_diacritics(result.get("artistName", "")).lower()
                res_alb = result.get("collectionName", "")

                art_match = any(tok in res_art for tok in art_tokens)
                alb_match = _album_words_match(clean_alb, res_alb)

                if art_match and alb_match:
                    art_url = result.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
                    if art_url:
                        img_r = requests.get(art_url, timeout=10)
                        if img_r.status_code == 200 and len(img_r.content) > 1500:
                            return img_r.content, "iTunes"
        except Exception:
            pass
    return None, None


def download_from_coverartarchive(artist, album):
    clean_alb = _clean_album_for_search(artist, album)
    headers = {"User-Agent": "MaxiMusicBox/2.0 (jukebox@local)"}
    for art_query in _artist_search_variants(artist):
        try:
            query = f'artist:"{art_query}" AND release:"{clean_alb}"'
            url = "https://musicbrainz.org/ws/2/release/"
            params = {"query": query, "fmt": "json", "limit": 5}
            r = requests.get(url, params=params, headers=headers, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json()
            for release in data.get("releases", []):
                mbid = release.get("id")
                if not mbid:
                    continue
                cover_url = f"https://coverartarchive.org/release/{mbid}/front-500"
                try:
                    img_r = requests.get(cover_url, timeout=10, allow_redirects=True)
                    if img_r.status_code == 200 and len(img_r.content) > 1500:
                        return img_r.content, "CoverArtArchive"
                except Exception:
                    continue
                time.sleep(0.25)
        except Exception:
            pass
    return None, None


def download_from_discogs(artist, album):
    token = getattr(config, "DISCOGS_TOKEN", "").strip()
    if not token:
        return None, None

    clean_alb = _clean_album_for_search(artist, album)
    headers = {
        "User-Agent": "MaxiMusicBox/2.0 +https://discogs.com",
        "Authorization": f"Discogs token={token}",
        "Accept": "application/json",
    }

    for art_query in _artist_search_variants(artist):
        art_tokens = [tok for tok in strip_diacritics(art_query).lower().split() if len(tok) >= 3]
        try:
            params = {
                "q": f"{art_query} {clean_alb}",
                "type": "release",
                "per_page": 8,
            }
            r = requests.get(
                "https://api.discogs.com/database/search",
                params=params,
                headers=headers,
                timeout=12,
            )
            time.sleep(1.05)

            if r.status_code != 200:
                continue

            data = r.json()
            for result in data.get("results", []):
                res_title = result.get("title", "")
                res_title_norm = strip_diacritics(res_title).lower()
                if not any(tok in res_title_norm for tok in art_tokens):
                    continue

                img_url = result.get("cover_image") or result.get("thumb")
                if not img_url or "spacer.gif" in img_url:
                    continue

                img_r = requests.get(img_url, headers=headers, timeout=12)
                if img_r.status_code == 200 and len(img_r.content) > 2000:
                    return img_r.content, "Discogs"
        except Exception:
            pass
    return None, None


def download_artist_photo_from_deezer(artist):
    if not artist or "Neznámý" in artist:
        return None, None

    for art_query in _artist_search_variants(artist):
        art_tokens = [tok for tok in strip_diacritics(art_query).lower().split() if len(tok) >= 3]
        if not art_tokens:
            continue
        try:
            r = requests.get(
                "https://api.deezer.com/search/artist",
                params={"q": art_query, "limit": 5},
                timeout=10,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            for result in data.get("data", []):
                res_name = strip_diacritics(result.get("name", "")).lower()
                if all(tok in res_name for tok in art_tokens) or (
                    len(art_tokens) >= 2 and any(len(tok) >= 5 and tok in res_name for tok in art_tokens)
                ):
                    img_url = result.get("picture_xl") or result.get("picture_big") or result.get("picture_medium")
                    if img_url and "default_artist" not in img_url:
                        img_r = requests.get(img_url, timeout=10)
                        if img_r.status_code == 200 and len(img_r.content) > 2000:
                            return img_r.content, "Deezer (foto interpreta)"
        except Exception:
            pass
    return None, None


def download_cover(artist, album):
    if not artist or "Neznámý" in artist:
        return None, None

    has_valid_album = (
        album
        and "Neznámé" not in album
        and album.lower() not in ("no title", "unknown")
        and not strip_diacritics(album).lower().startswith("mix cd")
    )

    if has_valid_album:
        data, source = download_from_deezer(artist, album)
        if data:
            return data, source

        data, source = download_from_itunes(artist, album)
        if data:
            return data, source

        data, source = download_from_coverartarchive(artist, album)
        if data:
            return data, source

        data, source = download_from_discogs(artist, album)
        if data:
            return data, source

    data, source = download_artist_photo_from_deezer(artist)
    if data:
        return data, source

    return None, None


def save_cover(data, artist, album):
    if not data:
        return None
    key = f"{strip_diacritics(artist).lower()}-{strip_diacritics(album).lower()}"
    name = hashlib.md5(key.encode()).hexdigest() + ".jpg"
    path = os.path.join(config.COVERS_DIR, name)
    try:
        img = Image.open(BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail((600, 600))
        img.save(path, "JPEG", quality=85)
        return path
    except Exception:
        return None


def clean_tag(value, fallback):
    if not value:
        return fallback
    value = fix_mojibake(str(value)).strip()
    if not value or value.lower() in ("unknown", "neznámý", "neznámé", "various", "no title", ""):
        return fallback
    return value


def fetch_missing_covers(conn):
    c = conn.cursor()
    rows = c.execute("""
        SELECT DISTINCT artist, album
        FROM tracks
        WHERE (cover_path IS NULL OR cover_path = '')
          AND artist != 'Neznámý interpret'
        ORDER BY artist COLLATE CZECH, album COLLATE CZECH
    """).fetchall()

    if not rows:
        return 0, []

    print(f"\nHledám obaly online pro {len(rows)} alb bez obalu...")
    downloaded = 0
    still_missing = []
    artist_photo_cache = {}

    for row in rows:
        artist = row["artist"]
        album = row["album"]

        key = f"{strip_diacritics(artist).lower()}-{strip_diacritics(album).lower()}"
        cached_path = os.path.join(config.COVERS_DIR, hashlib.md5(key.encode()).hexdigest() + ".jpg")
        if os.path.exists(cached_path) and os.path.getsize(cached_path) > 1000:
            c.execute(
                "UPDATE tracks SET cover_path = ? WHERE artist = ? AND album = ?",
                (cached_path, artist, album),
            )
            downloaded += 1
            continue

        data, source = download_cover(artist, album)

        if not data and artist in artist_photo_cache:
            data = artist_photo_cache[artist]
            source = "Deezer (foto interpreta - cache)"

        if data:
            if "foto interpreta" in (source or ""):
                artist_photo_cache[artist] = data
            cover_path = save_cover(data, artist, album)
            if cover_path:
                c.execute(
                    "UPDATE tracks SET cover_path = ? WHERE artist = ? AND album = ?",
                    (cover_path, artist, album),
                )
                downloaded += 1
                print(f"  ✓ Staženo ({source}): {artist} – {album}")
            else:
                still_missing.append((artist, album))
        else:
            still_missing.append((artist, album))
            print(f"  ✗ Nenalezeno: {artist} – {album}")

    return downloaded, still_missing


def _get_volume_mount_point(path):
    if path.startswith("/Volumes/"):
        parts = path.split(os.sep)
        if len(parts) >= 3 and parts[2]:
            return os.sep.join(parts[:3])
    return None


def scan_library(scan_dirs=None):
    init_db()
    conn = get_db()
    c = conn.cursor()

    if scan_dirs is None:
        target_dirs = [config.MUSIC_DIR]
    else:
        target_dirs = [os.path.abspath(os.path.expanduser(d)) for d in scan_dirs]

    print("1/3 Skenuji soubory a lokální obaly...")
    for d in target_dirs:
        print(f"  -> Zdroj: {d}")
    print("-" * 50)

    existing = {}
    for row in c.execute("SELECT path, mtime, cover_path FROM tracks"):
        existing[row["path"]] = (row["mtime"], row["cover_path"])

    removed_count = 0
    for db_path in list(existing.keys()):
        in_scanned_scope = any(
            db_path == d or db_path.startswith(d + os.sep) for d in target_dirs
        )
        if not in_scanned_scope:
            continue

        vol_root = _get_volume_mount_point(db_path)
        if vol_root and not os.path.exists(vol_root):
            continue

        if not os.path.exists(db_path):
            c.execute("DELETE FROM tracks WHERE path = ?", (db_path,))
            removed_count += 1

    count_new = 0
    count_updated = 0
    count_skipped = 0
    covers_found = 0

    for base_dir in target_dirs:
        if not os.path.exists(base_dir):
            print(f"Přeskakuji nedostupný zdroj: {base_dir}")
            continue

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for f in files:
                if f.startswith(".") or not f.lower().endswith((".mp3", ".flac", ".m4a", ".ogg", ".wav")):
                    continue

                path = os.path.join(root, f)

                try:
                    mtime = os.path.getmtime(path)
                except Exception:
                    continue

                if path in existing and existing[path][0] is not None and abs(existing[path][0] - mtime) < 1.0:
                    count_skipped += 1
                    continue

                is_new = path not in existing
                origin = detect_origin(path)

                try:
                    rel = os.path.relpath(root, base_dir)
                except Exception:
                    rel = "."
                parts = rel.split(os.sep)

                if len(parts) >= 2 and parts[0].lower() in ("czask", "cizí", "cizi", "foreign"):
                    folder_artist = parts[1]
                    folder_album = parts[2] if len(parts) >= 3 else "Neznámé album"
                else:
                    folder_artist = parts[0] if len(parts) >= 1 and parts[0] not in (".", "..", "") else "Neznámý interpret"
                    folder_album = parts[1] if len(parts) >= 2 else "Neznámé album"

                try:
                    audio = None
                    try:
                        audio = File(path, easy=True)
                    except Exception:
                        audio = None

                    if audio is not None:
                        def _tag(k):
                            vals = audio.get(k)
                            return vals[0] if vals else None

                        title = clean_tag(_tag("title"), os.path.splitext(f)[0])
                        raw_artist = clean_tag(_tag("artist"), folder_artist)
                        if is_junk_artist(raw_artist):
                            raw_artist = folder_artist

                        artists_list = split_artists(raw_artist, track_title=title)
                        primary_artist = artists_list[0]

                        album = normalize_album_name(primary_artist, clean_tag(_tag("album"), folder_album))
                        genre = clean_tag(_tag("genre"), "Ostatní")

                        track_num = 0
                        try:
                            tnum_raw = _tag("tracknumber")
                            if tnum_raw:
                                track_num = int(str(tnum_raw).split("/")[0])
                            else:
                                raise ValueError()
                        except Exception:
                            m = re.match(r"^(\d+)", f)
                            if m:
                                track_num = int(m.group(1))

                        duration = audio.info.length if audio.info else 0
                    else:
                        if os.path.getsize(path) < 1024:
                            continue
                        base_no_ext = os.path.splitext(f)[0]
                        m = re.match(r"^(\d+)\s*[-–._]\s*(.+)$", base_no_ext)
                        if m:
                            track_num = int(m.group(1))
                            title = clean_tag(m.group(2), base_no_ext)
                        else:
                            track_num = 0
                            title = clean_tag(base_no_ext, base_no_ext)

                        artists_list = split_artists(folder_artist, track_title=title)
                        primary_artist = artists_list[0]
                        album = normalize_album_name(primary_artist, folder_album)
                        genre = "Ostatní"
                        duration = 0

                    cover_path = existing[path][1] if (path in existing and existing[path][1] and os.path.exists(existing[path][1])) else None

                    if not cover_path and audio is not None:
                        try:
                            raw = File(path)
                            embedded = get_embedded_cover(raw)
                            if embedded:
                                cover_path = save_cover(embedded, primary_artist, album)
                                if cover_path:
                                    covers_found += 1
                        except Exception:
                            pass

                    if not cover_path:
                        folder_cover = find_folder_cover(root)
                        if folder_cover:
                            cover_path = save_cover(folder_cover, primary_artist, album)
                            if cover_path:
                                covers_found += 1

                    c.execute("SELECT id FROM tracks WHERE path = ?", (path,))
                    existing_row = c.fetchone()
                    if existing_row:
                        track_id = existing_row["id"]
                        c.execute("""
                            UPDATE tracks
                            SET title=?, artist=?, album=?, genre=?, track_num=?,
                                duration=?, cover_path=?, mtime=?, origin=?
                            WHERE id=?
                        """, (title, primary_artist, album, genre, track_num,
                              duration, cover_path, mtime, origin, track_id))
                    else:
                        c.execute("""
                            INSERT INTO tracks
                            (path, title, artist, album, genre, track_num, duration, cover_path, mtime, origin, play_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (path, title, primary_artist, album, genre, track_num,
                              duration, cover_path, mtime, origin))
                        track_id = c.lastrowid

                    c.execute("DELETE FROM track_artists WHERE track_id = ?", (track_id,))
                    for art in artists_list:
                        c.execute(
                            "INSERT OR IGNORE INTO track_artists (track_id, artist) VALUES (?, ?)",
                            (track_id, art),
                        )

                    if is_new:
                        count_new += 1
                    else:
                        count_updated += 1

                    total_done = count_new + count_updated
                    if total_done % 50 == 0:
                        print(f"  ... zpracováno {total_done} souborů (přeskočeno {count_skipped})")

                except Exception as e:
                    print(f"Chyba u {path}: {e}")

    print("\n2/3 Sjednocuji interprety, duety a českou diakritiku...")
    merged = unify_artists_in_db(conn)
    conn.commit()

    print("\n3/3 Dostahovávám chybějící obaly alb a fotky interpretů...")
    covers_downloaded, missing_covers = fetch_missing_covers(conn)
    conn.commit()

    total_artists = c.execute("SELECT COUNT(DISTINCT artist) AS cnt FROM track_artists").fetchone()["cnt"]
    total_tracks = c.execute("SELECT COUNT(*) AS cnt FROM tracks").fetchone()["cnt"]
    conn.close()

    print("-" * 50)
    print("HOTOVO!")
    print(f"Celkem skladeb v DB   : {total_tracks}")
    print(f"Unikátních interpretů : {total_artists}")
    print(f"Nové skladby          : {count_new}")
    print(f"Aktualizované         : {count_updated}")
    print(f"Odebrané (smazané)    : {removed_count}")
    print(f"Přeskočené (beze změn): {count_skipped}")
    print(f"Sloučené duplicity    : {merged}")
    print(f"Obaly lokálně         : {covers_found}")
    print(f"Obaly stažené online  : {covers_downloaded}")
    print(f"Alba stále bez obalu  : {len(missing_covers)}")


# --- Dotazovací funkce pro UI ---

def increment_play_count(path):
    """Zvýší počítadlo přehrání skladby o 1."""
    if not path:
        return
    try:
        conn = get_db()
        conn.execute(
            "UPDATE tracks SET play_count = COALESCE(play_count, 0) + 1 WHERE path = ?",
            (path,),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_top_tracks(limit=50):
    """Vrátí TOP 50 nejhranějších skladeb (s alespoň 1 přehráním)."""
    init_db()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE COALESCE(play_count, 0) > 0
        ORDER BY play_count DESC, artist COLLATE CZECH, title COLLATE CZECH
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def get_random_track():
    """Vrátí jednu náhodnou existující skladbu z databáze pro Auto-DJ."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tracks ORDER BY RANDOM() LIMIT 15"
    ).fetchall()
    conn.close()
    for r in rows:
        if r["path"] and os.path.exists(r["path"]):
            return dict(r)
    return None


def get_genres(origin=None):
    conn = get_db()
    if origin:
        rows = conn.execute(
            "SELECT DISTINCT genre FROM tracks WHERE origin = ? ORDER BY genre COLLATE CZECH",
            (origin,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT genre FROM tracks ORDER BY genre COLLATE CZECH"
        ).fetchall()
    conn.close()
    return [r["genre"] for r in rows]


def get_artists(genre=None, origin=None):
    conn = get_db()
    sql = """
        SELECT DISTINCT ta.artist
        FROM track_artists ta
        JOIN tracks t ON t.id = ta.track_id
        WHERE 1=1
    """
    params = []
    if genre and genre != "VŠE":
        sql += " AND t.genre = ?"
        params.append(genre)
    if origin:
        sql += " AND t.origin = ?"
        params.append(origin)
    sql += " ORDER BY ta.artist COLLATE CZECH"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [r["artist"] for r in rows]


def get_albums(artist, origin=None):
    conn = get_db()
    sql = """
        SELECT DISTINCT t.album
        FROM tracks t
        JOIN track_artists ta ON t.id = ta.track_id
        WHERE ta.artist = ?
    """
    params = [artist]
    if origin:
        sql += " AND t.origin = ?"
        params.append(origin)
    sql += " ORDER BY t.album COLLATE CZECH"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [r["album"] for r in rows]


def get_tracks(artist, album=None, origin=None):
    conn = get_db()
    sql = """
        SELECT DISTINCT t.*
        FROM tracks t
        JOIN track_artists ta ON t.id = ta.track_id
        WHERE ta.artist = ?
    """
    params = [artist]
    if origin:
        sql += " AND t.origin = ?"
        params.append(origin)
    if album and album != "VŠE":
        sql += " AND t.album = ?"
        params.append(album)
        sql += " ORDER BY t.track_num, t.title COLLATE CZECH"
    else:
        sql += " ORDER BY t.album COLLATE CZECH, t.track_num, t.title COLLATE CZECH"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_cover_for_artist_album(artist, album):
    conn = get_db()
    row = conn.execute(
        """
        SELECT t.cover_path
        FROM tracks t
        JOIN track_artists ta ON t.id = ta.track_id
        WHERE ta.artist = ? AND t.album = ? AND t.cover_path IS NOT NULL
        LIMIT 1
        """,
        (artist, album),
    ).fetchone()
    conn.close()
    return row["cover_path"] if row else None


def get_total_tracks():
    init_db()
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) AS cnt FROM tracks").fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_videos():
    video_ext = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".mpg", ".mpeg", ".m4v")
    videos_dir = getattr(config, "VIDEOS_DIR", os.path.join(config.BASE_DIR, "videos"))
    if not os.path.isdir(videos_dir):
        return []

    items = []
    try:
        files = os.listdir(videos_dir)
    except Exception:
        return []

    for f in files:
        if f.startswith(".") or not f.lower().endswith(video_ext):
            continue
        full_path = os.path.join(videos_dir, f)
        if not os.path.isfile(full_path):
            continue

        base_name = os.path.splitext(f)[0]
        if " - " in base_name:
            artist_part, title_part = base_name.split(" - ", 1)
            artist = artist_part.strip()
            title = title_part.strip()
            display_name = base_name
        else:
            artist = "Videoklip"
            title = base_name
            display_name = base_name

        items.append({
            "path": full_path,
            "artist": artist,
            "title": title,
            "display_name": display_name,
            "album": "Videoklipy",
            "duration": 0,
            "cover_path": None,
            "is_video": True,
        })

    items.sort(key=lambda x: czech_sort_key(x["display_name"]))
    return items