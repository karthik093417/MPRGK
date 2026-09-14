import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import webbrowser
import re
import queue
from queue import Queue


news_queue = Queue()

log_queue = Queue()

progress_queue = Queue()

all_rows = []
displayed_keys = set()

# ==========================================================
# CONFIGURATION
# ==========================================================

REFRESH_SECONDS = 300
REQUEST_TIMEOUT = 10

# ==============================
# GLOBAL TRACKERS (MUST BE FIRST)
# ==============================

known_headlines = set()
new_items = {}

# ==========================================================
# STATE NEWS DATASET
# ==========================================================

NEWS_SOURCES = {
    "Andhra Pradesh": [
        {"name": "TV9 Telugu", "url": "https://tv9telugu.com"},
        {"name": "Sakshi TV", "url": "https://www.sakshi.com"},
        {"name": "NTV Telugu", "url": "https://www.ntvtelugu.com"},
        {"name": "ETV Andhra Pradesh", "url": "https://www.etvandhrapradesh.com"}
    ],

    "Arunachal Pradesh": [
        {"name": "Arunachal Times", "url": "https://arunachaltimes.in"},
        {"name": "Arunachal24", "url": "https://arunachal24.in"}
    ],

    "Assam": [
        {"name": "News Live", "url": "https://newslivetv.com"},
        {"name": "Pratidin Time", "url": "https://www.pratidintime.com"},
        {"name": "DY365", "url": "https://dy365.in"}
    ],

    "Bihar": [
        {"name": "News18 Bihar", "url": "https://hindi.news18.com"},
        {"name": "Prabhat Khabar", "url": "https://www.prabhatkhabar.com"},
        {"name": "Zee Bihar Jharkhand", "url": "https://zeenews.india.com"}
    ],

    "Chhattisgarh": [
        {"name": "IBC24", "url": "https://www.ibc24.in"},
        {"name": "News18 MP/CG", "url": "https://hindi.news18.com"},
        {"name": "Patrika", "url": "https://www.patrika.com"}
    ],

    "Goa": [
        {"name": "Prudent Media", "url": "https://www.prudentmedia.in"},
        {"name": "Herald Goa", "url": "https://www.heraldgoa.in"}
    ],

    "Gujarat": [
        {"name": "TV9 Gujarati", "url": "https://tv9gujarati.com"},
        {"name": "GSTV", "url": "https://www.gstv.in"},
        {"name": "Sandesh News", "url": "https://sandesh.com"}
    ],

    "Haryana": [
        {"name": "News18 Haryana", "url": "https://hindi.news18.com"},
        {"name": "Aaj Tak Haryana", "url": "https://www.aajtak.in"},
        {"name": "Dainik Bhaskar", "url": "https://www.bhaskar.com"}
    ],

    "Himachal Pradesh": [
        {"name": "Amar Ujala", "url": "https://www.amarujala.com"},
        {"name": "Zee News HP", "url": "https://zeenews.india.com"}
    ],

    "Jharkhand": [
        {"name": "Prabhat Khabar", "url": "https://www.prabhatkhabar.com"},
        {"name": "News11 Bharat", "url": "https://news11.digital"}
    ],

    "Karnataka": [
        {"name": "TV9 Kannada", "url": "https://tv9kannada.com"},
        {"name": "Public TV", "url": "https://publictv.in"},
        {"name": "News18 Kannada", "url": "https://kannada.news18.com"},
        {"name": "Vijay Karnataka", "url": "https://vijaykarnataka.com"}
    ],

    "Kerala": [
        {"name": "Asianet News", "url": "https://www.asianetnews.com"},
        {"name": "Manorama News", "url": "https://www.manoramanews.com"},
        {"name": "Mathrubhumi News", "url": "https://www.mathrubhumi.com"}
    ],

    "Madhya Pradesh": [
        {"name": "News18 MP", "url": "https://hindi.news18.com"},
        {"name": "IBC24 MP", "url": "https://www.ibc24.in"},
        {"name": "Patrika MP", "url": "https://www.patrika.com"}
    ],

    "Maharashtra": [
        {"name": "ABP Majha", "url": "https://marathi.abplive.com"},
        {"name": "TV9 Marathi", "url": "https://www.tv9marathi.com"},
        {"name": "Lokmat News", "url": "https://www.lokmat.com"}
    ],

    "Manipur": [
        {"name": "Impact TV", "url": "https://impacttv.in"},
        {"name": "ISTV Network", "url": "https://istvnetwork.com"}
    ],

    "Meghalaya": [
        {"name": "Shillong Times", "url": "https://theshillongtimes.com"}
    ],

    "Mizoram": [
        {"name": "Zonet TV", "url": "https://zonet.in"}
    ],

    "Nagaland": [
        {"name": "Nagaland Post", "url": "https://nagalandpost.com"}
    ],

    "Odisha": [
        {"name": "OTV", "url": "https://odishatv.in"},
        {"name": "Kanak News", "url": "https://kanaknews.com"},
        {"name": "Sambad", "url": "https://sambad.in"}
    ],

    "Punjab": [
        {"name": "PTC News", "url": "https://www.ptcnews.tv"},
        {"name": "ABP Sanjha", "url": "https://punjabi.abplive.com"},
        {"name": "Jagbani", "url": "https://www.jagbani.com"}
    ],

    "Rajasthan": [
        {"name": "News18 Rajasthan", "url": "https://hindi.news18.com"},
        {"name": "Zee Rajasthan", "url": "https://zeenews.india.com"},
        {"name": "Patrika Rajasthan", "url": "https://www.patrika.com"}
    ],

    "Sikkim": [
        {"name": "Sikkim Express", "url": "https://www.sikkimexpress.com"}
    ],

    "Tamil Nadu": [
        {"name": "Sun News", "url": "https://www.sunnews.tv"},
        {"name": "Thanthi TV", "url": "https://www.thanthitv.com"},
        {"name": "Polimer News", "url": "https://www.polimernews.com"}
    ],

    "Telangana": [
        {"name": "TV9 Telugu", "url": "https://tv9telugu.com"},
        {"name": "NTV Telugu", "url": "https://www.ntvtelugu.com"},
        {"name": "Sakshi TV", "url": "https://www.sakshi.com"}
    ],

    "Tripura": [
        {"name": "Tripura Times", "url": "https://tripuratimes.com"}
    ],

    "Uttar Pradesh": [
        {"name": "Aaj Tak", "url": "https://www.aajtak.in"},
        {"name": "News18 UP", "url": "https://hindi.news18.com"},
        {"name": "Amar Ujala", "url": "https://www.amarujala.com"},
        {"name": "Dainik Jagran", "url": "https://www.jagran.com"}
    ],

    "Uttarakhand": [
        {"name": "Amar Ujala", "url": "https://www.amarujala.com"},
        {"name": "News18 Uttarakhand", "url": "https://hindi.news18.com"}
    ],

    "West Bengal": [
        {"name": "ABP Ananda", "url": "https://bengali.abplive.com"},
        {"name": "Zee 24 Ghanta", "url": "https://zeenews.india.com"},
        {"name": "Kolkata TV", "url": "https://www.kolkatatv.org"}
    ],

    "Delhi": [
        {"name": "NDTV", "url": "https://www.ndtv.com"},
        {"name": "Times Now", "url": "https://www.timesnownews.com"},
        {"name": "India TV", "url": "https://www.indiatvnews.com"},
        {"name": "Aaj Tak", "url": "https://www.aajtak.in"}
    ],

    "Jammu & Kashmir": [
        {"name": "Greater Kashmir", "url": "https://www.greaterkashmir.com"},
        {"name": "Rising Kashmir", "url": "https://www.risingkashmir.com"}
    ],

    "Ladakh": [
        {"name": "Reach Ladakh", "url": "https://www.reachladakh.com"}
    ],

    "Lakshadweep": [
        {"name": "Manorama News Coverage", "url": "https://www.manoramanews.com"}
    ],

    "Puducherry": [
        {"name": "The Hindu", "url": "https://www.thehindu.com"}
    ],

    "Chandigarh": [
        {"name": "The Tribune", "url": "https://www.tribuneindia.com"},
        {"name": "Punjab Kesari", "url": "https://www.punjabkesari.in"}
    ],

    "Andaman & Nicobar Islands": [
        {"name": "Andaman Chronicle", "url": "https://www.andamanchronicle.net"}
    ],

    "Dadra & Nagar Haveli and Daman & Diu": [
        {"name": "Divya Bhaskar", "url": "https://www.divyabhaskar.co.in"}
    ]
}

# ==========================================================
# PRIORITY CATEGORIES
# ==========================================================

CATEGORY_PRIORITY = {
    "War": 1,
    "Foreign Alert": 2,
    "Disaster": 3,
    "Breaking": 4,
    "Crime": 5,
    "Protest": 6,
    "Government": 7,
    "Economy": 8,
    "Technology": 9,
    "Viral": 10,
    "General":11 
}

KEYWORDS = {
    "War": [
        "war", "missile", "attack", "airstrike",
        "military", "drone", "border"
    ],

    "Foreign Alert": [
        "foreign", "international", "global",
        "embassy", "world leaders"
    ],

    "Disaster": [
        "earthquake", "flood", "cyclone",
        "storm", "fire", "landslide",
        "tsunami"
    ],

    "Breaking": [
        "breaking", "urgent", "live",
        "developing"
    ],

    "Crime": [
        "crime", "murder", "arrest",
        "fraud", "police", "robbery"
    ],

    "Protest": [
        "protest", "riot", "strike",
        "demonstration"
    ],

    "Government": [
        "government", "cabinet",
        "minister", "scheme",
        "policy", "announcement"
    ],

    "Economy": [
        "economy", "gdp", "market",
        "inflation", "stock"
    ],

    "Technology": [
        "ai", "technology",
        "startup", "innovation",
        "robotics"
    ],

    "Viral": [
        "viral", "trending",
        "social media"
    ]
}

# ==========================================================
# CLASSIFICATION
# ==========================================================

def classify_headline(text):

    txt = text.lower()

    for category, words in KEYWORDS.items():

        for word in words:

            if word in txt:
                return category

    return "General"



def build_state_source_maps():

    state_list = list(NEWS_SOURCES.keys())

    state_to_sources = {}

    all_sources = []

    for state, sources in NEWS_SOURCES.items():

        state_to_sources[state] = [
            s["name"] for s in sources
        ]

        for s in sources:
            all_sources.append(s["name"])

    return state_list, state_to_sources, all_sources

STATE_LIST, STATE_TO_SOURCES, ALL_SOURCES = build_state_source_maps()


# ==========================================================
# HEADLINE EXTRACTION
# ==========================================================

REQUEST_TIMEOUT = 10


def is_today(publish_time):

    if not publish_time:
        return False

    try:

        publish_time = publish_time.strip()

        if publish_time.endswith("Z"):
            publish_time = publish_time.replace(
                "Z",
                "+00:00"
            )

        dt = datetime.fromisoformat(
            publish_time
        )

        if dt.tzinfo:
            dt = dt.replace(
                tzinfo=None
            )

        now = datetime.now()

        return (
            dt.day == now.day and
            dt.month == now.month and
            dt.year == now.year
        )

    except:
        return False


import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

def extract_headlines(url):

    items = []
    seen = set()

    try:

        r = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            verify=False,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        r.raise_for_status()

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        articles = soup.find_all(
            "article"
        )

        if not articles:

            articles = soup.find_all(
                ["div", "section", "li"]
            )

        for article in articles:

            headline_tag = (
                article.find("h1")
                or article.find("h2")
                or article.find("h3")
                or article.find("a")
            )

            if not headline_tag:
                continue

            headline = headline_tag.get_text(
                " ",
                strip=True
            )

            if len(headline) < 20:
                continue

            if headline in seen:
                continue

            publish_time = None

            # Method 1: <time>
            time_tag = article.find("time")

            if time_tag:

                publish_time = (
                    time_tag.get(
                        "datetime"
                    )
                    or time_tag.get_text(
                        " ",
                        strip=True
                    )
                )

            # Method 2: article:published_time
            if not publish_time:

                meta = article.find(
                    "meta",
                    attrs={
                        "property":
                        "article:published_time"
                    }
                )

                if meta:

                    publish_time = meta.get(
                        "content"
                    )

            # Method 3: datePublished
            if not publish_time:

                meta = article.find(
                    "meta",
                    attrs={
                        "itemprop":
                        "datePublished"
                    }
                )

                if meta:

                    publish_time = meta.get(
                        "content"
                    )

            # Method 4: pubdate
            if not publish_time:

                meta = article.find(
                    "meta",
                    attrs={
                        "name":
                        "pubdate"
                    }
                )

                if meta:

                    publish_time = meta.get(
                        "content"
                    )

            # Method 5: date/time classes
            if not publish_time:

                date_tag = article.find(
                    lambda tag:
                    tag.name in (
                        "span",
                        "div",
                        "p"
                    )
                    and tag.get("class")
                    and any(
                        "date" in c.lower()
                        or "time" in c.lower()
                        for c in tag.get("class")
                    )
                )

                if date_tag:

                    publish_time = (
                        date_tag.get_text(
                            " ",
                            strip=True
                        )
                    )

            if not publish_time:
                continue

            seen.add(headline)

            items.append({

                "headline":
                headline,

                "publish_time":
                publish_time
            })

    except requests.exceptions.Timeout:

        log(
            f"TIMEOUT: {url}"
        )

    except requests.exceptions.SSLError:

        log(
            f"SSL ERROR: {url}"
        )

    except requests.exceptions.ConnectionError:

        log(
            f"CONNECTION ERROR: {url}"
        )

    except Exception as e:

        log(
            f"ERROR: {url} | {e}"
        )

    return items

def log(message):

    timestamp = datetime.now().strftime("%H:%M:%S")

    log_queue.put(
        f"[{timestamp}] {message}"
    )




# ==========================================================
# FETCH ALL SOURCES
# ==========================================================

def fetch_all_news():

    rows = []

    selected_date = datetime(
        int(year_var.get()),
        datetime.strptime(
            month_var.get(),
            "%B"
        ).month,
        int(day_var.get())
    ).date()

    total_sources = sum(
        len(v)
        for v in NEWS_SOURCES.values()
    )

    completed = 0
    count = 1

    progress_queue.put(
        (0, total_sources, 0)
    )

    for state, sources in NEWS_SOURCES.items():

        for source in sources:

            completed += 1

            progress_queue.put(
                (
                    completed,
                    total_sources,
                    completed * 100 / total_sources
                )
            )

            log(
                f"{state} -> "
                f"{source['name']}"
            )

            try:

                headlines_data = extract_headlines(
                    source["url"]
                )

            except Exception as e:

                log(
                    f"ERROR: "
                    f"{source['name']} -> {e}"
                )

                continue

            for item in headlines_data:

                headline = item.get(
                    "headline"
                )

                publish_time = item.get(
                    "publish_time"
                )

                if not headline:
                    continue

                try:

                    dt = safe_time(
                        publish_time
                    )

                    if dt.date() != selected_date:
                        continue

                except:

                    continue

                category = classify_headline(
                    headline
                )

                row = {

                    "no": count,

                    "rank":
                    CATEGORY_PRIORITY.get(
                        category,
                        999
                    ),

                    "state": state,

                    "source":
                    source["name"],

                    "topic":
                    category,

                    "headline":
                    headline,

                    "publish_time":
                    publish_time,

                    "url":
                    source["url"]
                }

                rows.append(row)

                news_queue.put(row)

                count += 1

    return rows

def load_news_worker():

    rows = fetch_all_news()

    for row in rows:
        news_queue.put(row)

from datetime import datetime

import queue

import queue

import queue

displayed_headlines = set()

def process_news_queue():

    try:

        while True:

            row = news_queue.get_nowait()

            # Skip invalid queue items
            if row is None:
                continue

            if not isinstance(row, dict):
                continue

            headline = str(
                row.get("headline", "")
            ).strip()

            if not headline:
                continue

            headline_key = (
                headline.lower()
                + "|"
                + row.get("source", "")
            )

            if headline_key in displayed_headlines:
                continue

            displayed_headlines.add(
                headline_key
            )

            tree.insert(
                "",
                "end",
                values=(
                    row.get("no"),
                    row.get("rank"),
                    row.get("state"),
                    row.get("source"),
                    row.get("topic"),
                    headline,
                    row.get(
                        "publish_time",
                        "N/A"
                    ),
                    row.get("url")
                ),
                tags=(
                    row.get(
                        "topic",
                        ""
                    ),
                )
            )

    except queue.Empty:
        pass

    root.after(
        100,
        process_news_queue
    )
    
def load_news_worker():

    global all_rows

    all_rows = fetch_all_news()

    news_queue.put(all_rows)
                                
def process_queue():

    try:

        while True:

            rows = news_queue.get_nowait()

            load_news(rows)

    except:

        pass

    root.after(
        500,
        process_queue
    )

from queue import Empty

def process_log_queue():

    try:

        while True:

            msg = log_queue.get_nowait()

            log_text.insert(
                "end",
                msg + "\n"
            )

            log_text.see("end")

    except Empty:
        pass

    root.after(
        100,
        process_log_queue
    )

def update_sources(*args):

    state = state_var.get()

    if state == "ALL":

        sources = []

        for state_sources in NEWS_SOURCES.values():

            for src in state_sources:

                sources.append(
                    src["name"]
                )

    else:

        sources = [

            src["name"]

            for src in NEWS_SOURCES.get(
                state,
                []
            )
        ]

    source_combo["values"] = (
        ["ALL"] +
        sorted(set(sources))
    )

    source_var.set("ALL")
    
def update_progress(
    completed=0,
    total_sources=0,
    percent=0
):

    progress.configure(
        maximum=max(total_sources, 1)
    )

    progress["value"] = completed

    status_var.set(
        f"Extracting "
        f"{completed}/{total_sources} "
        f"({percent:.1f}%)"
    )
    
from queue import Empty

def process_progress_queue():

    try:

        while True:

            completed, total, percent = (
                progress_queue.get_nowait()
            )

            progress.configure(
                maximum=total
            )

            progress["value"] = completed

            status_var.set(
                f"Extracting "
                f"{completed}/{total} "
                f"({percent:.1f}%)"
            )

    except Empty:
        pass

    root.after(
        100,
        process_progress_queue
    )
    
def blink_row(item_id, count=10):

    if not tree.exists(item_id):
        return

    if count <= 0:

        tree.item(
            item_id,
            tags=("NEW",)
        )

        return

    tags = tree.item(
        item_id,
        "tags"
    )

    if "BREAKING_RED" in tags:

        tree.item(
            item_id,
            tags=("BREAKING_YELLOW",)
        )

    else:

        tree.item(
            item_id,
            tags=("BREAKING_RED",)
        )

    root.after(
        500,
        lambda:
        blink_row(
            item_id,
            count - 1
        )
    )
    

def is_breaking(headline):

    headline = headline.lower()

    keywords = [
        "breaking",
        "urgent",
        "alert",
        "live",
        "developing",
        "exclusive",
        "attack",
        "war",
        "missile",
        "earthquake",
        "flood",
        "cyclone",
        "riot",
        "protest",
        "fire"
    ]

    return any(
        k in headline
        for k in keywords
    )


from datetime import datetime

def safe_time(value):

    if not value:
        return datetime.min

    if isinstance(value, datetime):

        if value.tzinfo:
            return value.replace(
                tzinfo=None
            )

        return value

    value = str(value).strip()

    if value.lower() in (
        "unknown",
        "none",
        ""
    ):
        return datetime.min

    formats = [

        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",

        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",

        "%d-%m-%Y",
        "%d/%m/%Y",

        "%d %b %Y",
        "%d %B %Y",

        "%d %b %Y %H:%M",
        "%d %B %Y %H:%M",

        "%B %d, %Y",
        "%b %d, %Y"
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt
            )

            if dt.tzinfo:
                dt = dt.replace(
                    tzinfo=None
                )

            return dt

        except:
            pass

    try:

        value = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            value
        )

        if dt.tzinfo:
            dt = dt.replace(
                tzinfo=None
            )

        return dt

    except:
        pass

    return datetime.min        

def passes_filter(row):

    state = state_var.get().strip()
    source = source_var.get().strip()

    if (
        state != "ALL"
        and row.get("state") != state
    ):
        return False

    if (
        source != "ALL"
        and row.get("source") != source
    ):
        return False

    # Apply date filter only if enabled
    if date_filter_var.get():

        publish_time = row.get(
            "publish_time"
        )

        if publish_time:

            try:

                dt = safe_time(
                    publish_time
                )

                selected_day = int(
                    day_var.get()
                )

                selected_month = datetime.strptime(
                    month_var.get(),
                    "%B"
                ).month

                selected_year = int(
                    year_var.get()
                )

                if (
                    dt.day != selected_day
                    or dt.month != selected_month
                    or dt.year != selected_year
                ):
                    return False

            except:
                return False

    return True


def matches_selected_date(
    publish_time
):

    try:

        publish_time = (
            publish_time
            .replace("Z", "+00:00")
        )

        dt = datetime.fromisoformat(
            publish_time
        )

        if dt.tzinfo:
            dt = dt.replace(
                tzinfo=None
            )

        return (
            dt.day ==
            int(day_var.get())
            and
            dt.month ==
            datetime.strptime(
                month_var.get(),
                "%B"
            ).month
            and
            dt.year ==
            int(year_var.get())
        )

    except:
        return False

def update_years():

    current_year = datetime.now().year

    year_combo["values"] = [
        str(y)
        for y in range(
            1900,
            current_year + 1
        )
    ]

def apply_filter():

    state = state_var.get().strip()
    source = source_var.get().strip()

    try:
        selected_day = int(day_var.get())
        selected_month = datetime.strptime(
            month_var.get(),
            "%B"
        ).month
        selected_year = int(year_var.get())
    except:
        selected_day = None
        selected_month = None
        selected_year = None

    tree.delete(*tree.get_children())

    filtered_rows = []
    seen = set()

    for row in all_rows:

        # State filter
        if (
            state != "ALL"
            and row.get("state") != state
        ):
            continue

        # Source filter
        if (
            source != "ALL"
            and row.get("source") != source
        ):
            continue

        # Date filter
        publish_time = row.get(
            "publish_time"
        )

        if publish_time:

            try:

                dt = safe_time(
                    publish_time
                )

                if (
                    selected_day
                    and selected_month
                    and selected_year
                ):
                    if (
                        dt.day != selected_day
                        or dt.month != selected_month
                        or dt.year != selected_year
                    ):
                        continue

            except:
                pass

        # Duplicate removal
        headline_key = (
            row.get(
                "headline",
                ""
            ).strip().lower()
            + "|"
            + row.get(
                "source",
                ""
            )
        )

        if headline_key in seen:
            continue

        seen.add(headline_key)

        filtered_rows.append(row)

    # Sort by rank then newest time
    filtered_rows.sort(
        key=lambda r: (
            r.get("rank", 999),
            safe_time(
                r.get(
                    "publish_time"
                )
            )
        ),
        reverse=True
    )

    count = 0

    for row in filtered_rows:

        tags = [row.get("topic", "")]

        if is_breaking(
            row.get(
                "headline",
                ""
            )
        ):
            tags.append(
                "BREAKING_RED"
            )

        tree.insert(
            "",
            "end",
            values=(

                row.get("no"),

                row.get("rank"),

                row.get("state"),

                row.get("source"),

                row.get("topic"),

                row.get("headline"),

                row.get(
                    "publish_time",
                    "LIVE"
                ),

                row.get("url")

            ),
            tags=tuple(tags)
        )

        count += 1

    headline_var.set(
        f"Headlines: {count}"
    )

    status_var.set(
        f"Showing {count} headlines"
    )

    last_update_var.set(
        "Last Filter: "
        + datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    log(
        f"FILTER -> "
        f"State={state} | "
        f"Source={source} | "
        f"Rows={count}"
    )

    tree.yview_moveto(0)
    
def clear_old_highlights():

    now = datetime.now()

    for item_id, ts in list(
        new_items.items()
    ):

        age = (
            now - ts
        ).total_seconds()

        if age > 60:

            if tree.exists(item_id):

                tree.item(
                    item_id,
                    tags=()
                )

            del new_items[item_id]

    root.after(
        10000,
        clear_old_highlights
    )

def load_news(rows):

    global all_rows

    status_var.set(
        "Displaying headlines..."
    )

    log(
        f"Fetched rows = {len(rows)}"
    )

    try:

        selected_day = int(
            day_var.get()
        )

        selected_month = datetime.strptime(
            month_var.get(),
            "%B"
        ).month

        selected_year = int(
            year_var.get()
        )

    except Exception:

        selected_day = None
        selected_month = None
        selected_year = None

    filtered_rows = []

    for row in rows:

        publish_time = row.get(
            "publish_time"
        )

        try:

            if publish_time:

                dt = safe_time(
                    publish_time
                )

            else:

                dt = datetime.now()

            row["_dt"] = dt

            # Apply date filter only if selected
            if (
                selected_day
                and selected_month
                and selected_year
            ):

                if (
                    dt.day != selected_day
                    or dt.month != selected_month
                    or dt.year != selected_year
                ):
                    continue

            filtered_rows.append(
                row
            )

        except Exception:

            row["_dt"] = datetime.now()

            filtered_rows.append(
                row
            )

    log(
        f"Filtered rows = "
        f"{len(filtered_rows)}"
    )

    # Latest publish time first
    filtered_rows.sort(
        key=lambda r: (
            safe_time(
                r.get(
                    "publish_time"
                )
            ),
            -r.get(
                "rank",
                999
            )
        ),
        reverse=True
    )

    tree.delete(
        *tree.get_children()
    )

    known_headlines.clear()

    new_count = 0

    for row in filtered_rows:

        headline = (
            row.get(
                "headline",
                ""
            )
            .strip()
        )

        if not headline:
            continue

        headline_key = (
            headline.lower()
            + "|"
            + row.get(
                "source",
                ""
            )
        )

        if headline_key in known_headlines:
            continue

        known_headlines.add(
            headline_key
        )

        publish_time = row.get(
            "publish_time"
        )

        if not publish_time:

            publish_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        values = (

            row.get("no"),

            row.get("rank"),

            row.get("state"),

            row.get("source"),

            row.get("topic"),

            headline,

            publish_time,

            row.get("url")
        )

        try:

            item_id = tree.insert(
                "",
                "end",
                values=values,
                tags=(
                    row.get(
                        "topic",
                        ""
                    ),
                )
            )

            new_items[item_id] = (
                datetime.now()
            )

            new_count += 1

        except Exception as e:

            log(
                f"Insert Error: {e}"
            )

    headline_var.set(
        f"Headlines: {new_count}"
    )

    status_var.set(
        f"Loaded {new_count} headlines"
    )

    last_update_var.set(
        "Last Update: "
        + datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    log(
        f"Displayed rows = "
        f"{new_count}"
    )

    tree.yview_moveto(0)

    
import threading

def start_load():

    threading.Thread(
        target=load_news_worker,
        daemon=True
    ).start()


# ==========================================================
# GUI
# ==========================================================

root = tk.Tk()
root.title("News Table")
root.geometry("1400x800")

style = ttk.Style()

style.theme_use("clam")

style.configure(
    "Treeview",
    background="#ffffff",
    foreground="#000000",
    fieldbackground="#ffffff",
    rowheight=28,
    font=("Segoe UI", 10),
    borderwidth=0
)

style.configure(
    "Treeview.Heading",
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    padding=5
)

style.map(
    "Treeview",
    background=[
        ("selected", "#4a90e2")
    ],
    foreground=[
        ("selected", "white")
    ]
)



# Main Frame
table_frame = ttk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True)

columns = (
    "No",
    "Rank",
    "State",
    "Source",
    "Topic",
    "Headline",
    "Publish Time",
    "URL"
)

tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

# Scrollbars
vsb = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=tree.yview
)

hsb = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=tree.xview
)

tree.configure(
    yscrollcommand=vsb.set,
    xscrollcommand=hsb.set
)

# Layout
tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

# Relative Width Ratios
column_ratios = {
    "No": 4,
    "Rank": 4,
    "State": 8,
    "Source": 10,
    "Topic": 8,
    "Headline": 40,
    "Publish Time": 12,
    "URL": 14
}

for col in columns:
    tree.heading(col, text=col)

def resize_columns(event=None):

    total_width = tree.winfo_width()

    total_ratio = sum(column_ratios.values())

    for col in columns:

        width = int(
            total_width *
            column_ratios[col] /
            total_ratio
        )

        tree.column(
            col,
            width=width,
            stretch=True,
            anchor="w"
        )

# Auto-resize when window changes
tree.bind("<Configure>", resize_columns)

def open_url(self, event):

        item = self.tree.selection()

        if not item:
            return

        values = self.tree.item(
            item[0],
            "values"
        )

        url = values[9]

        webbrowser.open(url)

filter_frame = ttk.Frame(root)
filter_frame.pack(fill="x", padx=5, pady=5)

state_var = tk.StringVar()
source_var = tk.StringVar()

ttk.Label(filter_frame, text="State:").pack(side="left", padx=5)

state_combo = ttk.Combobox(
    filter_frame,
    textvariable=state_var,
    state="readonly",
    values=["ALL"] + STATE_LIST
)
state_combo.pack(side="left", padx=5)

ttk.Label(filter_frame, text="Source:").pack(side="left", padx=5)

source_combo = ttk.Combobox(
    filter_frame,
    textvariable=source_var,
    state="readonly"
)
source_combo.pack(side="left", padx=5)

state_combo.current(0)

update_sources()


state_var.trace_add(
    "write",
    update_sources
)

status_frame = ttk.Frame(root)
status_frame.pack(fill="x")

status_var = tk.StringVar()
status_var.set("Ready")

status_label = ttk.Label(
    status_frame,
    textvariable=status_var,
    font=("Segoe UI", 10, "bold")
)
status_label.pack(side="left", padx=10)

# Day
day_var = tk.StringVar(value=str(datetime.now().day))

day_combo = ttk.Combobox(
    filter_frame,
    textvariable=day_var,
    values=[str(i) for i in range(1, 32)],
    width=5,
    state="readonly"
)
day_combo.pack(side="left", padx=5)

# Month
month_var = tk.StringVar(
    value=datetime.now().strftime("%B")
)

month_combo = ttk.Combobox(
    filter_frame,
    textvariable=month_var,
    values=[
        "January","February","March",
        "April","May","June",
        "July","August","September",
        "October","November","December"
    ],
    width=12,
    state="readonly"
)
month_combo.pack(side="left", padx=5)

# Year
current_year = datetime.now().year

year_var = tk.StringVar(
    value=str(current_year)
)

year_combo = ttk.Combobox(
    filter_frame,
    textvariable=year_var,
    values=[
        str(y)
        for y in range(
            1900,
            current_year + 1
        )
    ],
    width=8,
    state="readonly"
)
year_combo.pack(side="left", padx=5)

last_update_var = tk.StringVar()

last_update_var.set("Last Update: Never")

last_update_label = ttk.Label(
    status_frame,
    textvariable=last_update_var
)

last_update_label.pack(
    side="right",
    padx=20
)

tree.tag_configure(
    "NEW",
    background="#fff799"
)

tree.tag_configure(
    "NEW",
    background="#fff799"
)

tree.tag_configure(
    "BREAKING_RED",
    background="#ff0000",
    foreground="white",
    font=("Segoe UI", 10, "bold")
)

tree.tag_configure(
    "BREAKING_YELLOW",
    background="#ffff00",
    foreground="black",
    font=("Segoe UI", 10, "bold")
)

tree.tag_configure(
    "War",
    background="#ffd0d0"
)

tree.tag_configure(
    "Disaster",
    background="#ffe0c0"
)

tree.tag_configure(
    "Crime",
    background="#ffd6d6"
)

tree.tag_configure(
    "Technology",
    background="#d9ffd9"
)

tree.tag_configure(
    "Government",
    background="#d9e6ff"
)

headline_var = tk.StringVar()

headline_var.set("Headlines: 0")

headline_label = ttk.Label(
    status_frame,
    textvariable=headline_var,
    font=("Segoe UI", 10, "bold")
)

headline_label.pack(
    side="right",
    padx=10
)


progress = ttk.Progressbar(
    status_frame,
    mode="determinate"
)
progress.pack(
    side="left",
    fill="x",
    expand=True,
    padx=10,
    pady=5
)

log_frame = ttk.LabelFrame(
    root,
    text="Extraction Log"
)
log_frame.pack(fill="x", padx=5, pady=5)

log_text = tk.Text(
    log_frame,
    height=10
)

log_text.pack(
    fill="both",
    expand=True
)

ttk.Button(
    filter_frame,
    text="Apply Filter",
    command=lambda:
    threading.Thread(
        target=apply_filter,
        daemon=True
    ).start()
).pack(side="left", padx=10)

state_var.trace_add("write", lambda *a: update_progress())
source_var.trace_add("write", lambda *a: apply_filter())

def auto_refresh():

    threading.Thread(
        target=load_news_worker,
        daemon=True
    ).start()

    root.after(
        300000,
        auto_refresh
    )

# Schedule background systems after GUI is ready
root.after(
    100,
    update_progress,
    0,
    0,
    0
)
root.after(100, process_queue)
root.after(100, process_log_queue)
root.after(100, process_progress_queue)
root.after(
    100,
    process_news_queue
)
root.after(1000, clear_old_highlights)
root.after(2000, auto_refresh)


root.mainloop()
