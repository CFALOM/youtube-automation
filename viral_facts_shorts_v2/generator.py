import json
import random
import re
import html
import pathlib
import requests
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

UA = "ViralFactsShorts/FINAL-2.0 (educational-short-generator)"


# =========================================================
# HUGE RANDOM TOPIC POOL
# =========================================================

TOPICS = [

    # GAMING
    "Minecraft",
    "Minecraft history",
    "Minecraft mobs",
    "Minecraft updates",
    "Minecraft development",
    "Minecraft secrets",
    "Minecraft records",
    "Minecraft inventions",
    "Roblox",
    "Roblox history",
    "Roblox games",
    "Roblox development",
    "Fortnite",
    "Fortnite history",
    "GTA",
    "GTA history",
    "Nintendo",
    "PlayStation",
    "Xbox",
    "video game history",
    "arcade games",
    "gaming records",

    # SCIENCE
    "space",
    "planets",
    "Mars",
    "Venus",
    "Mercury",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "black holes",
    "stars",
    "astronomy",
    "NASA",
    "physics",
    "chemistry",
    "biology",
    "evolution",
    "quantum physics",
    "science discoveries",

    # ANIMALS
    "octopus",
    "crows",
    "sharks",
    "dogs",
    "cats",
    "whales",
    "dolphins",
    "penguins",
    "snakes",
    "spiders",
    "ants",
    "bees",
    "birds",
    "deep sea animals",
    "weird animals",

    # HUMAN
    "human body",
    "brain",
    "psychology",
    "memory",
    "sleep",
    "dreams",
    "human senses",

    # TECHNOLOGY
    "artificial intelligence",
    "internet history",
    "computers",
    "smartphones",
    "Google",
    "YouTube history",
    "social media history",
    "web history",
    "computer history",
    "robotics",
    "inventions",

    # HISTORY
    "ancient history",
    "Roman Empire",
    "ancient Egypt",
    "medieval history",
    "world history",
    "war history",
    "historical discoveries",
    "famous inventions",
    "lost cities",
    "historical mysteries",

    # PLACES / EARTH
    "oceans",
    "deep ocean",
    "mountains",
    "deserts",
    "volcanoes",
    "weather",
    "geography",
    "countries",
    "islands",
    "Antarctica",

    # CULTURE
    "movies",
    "movie history",
    "music history",
    "sports history",
    "Olympics",
    "cars",
    "aviation",
    "food history",
    "money history",

    # WEIRD
    "weird facts",
    "strange discoveries",
    "unusual inventions",
    "weird history",
    "strange places",
    "mysterious events",
]


# =========================================================
# HOOKS
# =========================================================

HOOKS = [
    "STOP SCROLLING — THIS IS REAL.",
    "THIS SOUNDS FAKE, BUT IT'S REAL.",
    "YOU PROBABLY DIDN'T KNOW THIS.",
    "THIS FACT GETS CRAZIER THE MORE YOU THINK ABOUT IT.",
    "ALMOST NOBODY KNOWS THIS.",
    "THIS IS ONE OF THE WEIRDEST FACTS YOU'LL HEAR TODAY.",
]


# =========================================================
# BRIDGES
# =========================================================

BRIDGES = [
    "But here's where it gets crazy.",
    "And that's not even the strange part.",
    "But there's one detail people miss.",
    "Now it gets even stranger.",
    "Here's the part that surprises people.",
]


# =========================================================
# WIKIPEDIA SEARCH
# =========================================================

def wiki_search(query):

    url = "https://en.wikipedia.org/w/rest.php/v1/search/page"

    response = requests.get(
        url,
        params={
            "q": query,
            "limit": 8,
        },
        headers={
            "User-Agent": UA,
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("pages", [])


# =========================================================
# GET WIKIPEDIA PAGE
# =========================================================

def wiki_page(title):

    url = (
        "https://en.wikipedia.org/w/rest.php/v1/page/"
        + quote(title, safe="")
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": UA,
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("source", "")


# =========================================================
# CLEAN TEXT
# =========================================================

def clean(text):

    if not text:
        return ""

    text = html.unescape(text)

    # Remove Wikipedia-style references.
    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    # Remove URLs.
    text = re.sub(
        r"https?://\S+",
        "",
        text,
        flags=re.I
    )

    # Remove email-like strings.
    text = re.sub(
        r"\S+@\S+\.\S+",
        "",
        text
    )

    # Remove obvious identifiers.
    text = re.sub(
        r"\b(?:doi|isbn|issn|pmid|oclc|id)\s*[:#]?\s*[\w./-]+",
        "",
        text,
        flags=re.I
    )

    # Remove long random alphanumeric identifiers.
    text = re.sub(
        r"\b[a-zA-Z]*\d[a-zA-Z0-9_-]{8,}\b",
        "",
        text
    )

    # Remove standalone long numbers.
    text = re.sub(
        r"\b\d{7,}\b",
        "",
        text
    )

    # Remove obvious slash-number IDs.
    text = re.sub(
        r"\b\d+\s*/\s*\d+(?:[-_/]\d+)*\b",
        "",
        text
    )

    # Remove repeated punctuation.
    text = re.sub(
        r"[|]{1,}",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# SPLIT INTO SENTENCES
# =========================================================

def sentences_from(text):

    text = clean(text)

    pieces = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    result = []

    for sentence in pieces:

        sentence = sentence.strip()

        if len(sentence) < 45:
            continue

        if len(sentence) > 360:
            continue

        result.append(sentence)

    return result


# =========================================================
# EXTREMELY STRICT GARBAGE FILTER
# =========================================================

def is_bad(sentence):

    if not sentence:
        return True

    low = sentence.lower()

    # -----------------------------------------------------
    # Metadata words
    # -----------------------------------------------------

    bad_words = [

        "doi",
        "isbn",
        "issn",
        "pmid",
        "oclc",

        "article number",
        "citation needed",
        "retrieved",
        "archived",
        "references",
        "external links",

        "edit",
        "identifier",
        "bibliography",

        "accessed",
        "publisher",
        "journal",
        "volume",
        "issue",
        "pages",

    ]

    if any(
        word in low
        for word in bad_words
    ):
        return True

    # -----------------------------------------------------
    # URLs
    # -----------------------------------------------------

    if "http://" in low:
        return True

    if "https://" in low:
        return True

    if "www." in low:
        return True

    # -----------------------------------------------------
    # Random number IDs
    #
    # Examples rejected:
    #
    # 7647647
    # 7647647/48584
    # 7647647/48584-874584
    # -----------------------------------------------------

    if re.search(
        r"\d{6,}",
        sentence
    ):
        return True

    if re.search(
        r"\b\d+\s*/\s*\d+\b",
        sentence
    ):
        return True

    if re.search(
        r"\b\d+[-_/]\d+[-_/]?\d*\b",
        sentence
    ):
        return True

    # -----------------------------------------------------
    # Long mixed identifiers
    # -----------------------------------------------------

    if re.search(
        r"\b[a-zA-Z0-9_-]{13,}\b",
        sentence
    ):
        return True

    # -----------------------------------------------------
    # Weird technical strings
    # -----------------------------------------------------

    if re.search(
        r"[A-Za-z]+\d{4,}",
        sentence
    ):
        return True

    # -----------------------------------------------------
    # Too many numbers
    # -----------------------------------------------------

    numbers = re.findall(
        r"\d+",
        sentence
    )

    if len(numbers) > 5:
        return True

    # -----------------------------------------------------
    # Too much punctuation
    # -----------------------------------------------------

    if sentence.count("/") > 1:
        return True

    if sentence.count("_") > 0:
        return True

    if sentence.count("|") > 0:
        return True

    if sentence.count("{") > 0:
        return True

    if sentence.count("}") > 0:
        return True

    # -----------------------------------------------------
    # Sentence length
    # -----------------------------------------------------

    words = sentence.split()

    if len(words) < 8:
        return True

    if len(words) > 55:
        return True

    # -----------------------------------------------------
    # Reject obvious list/table fragments
    # -----------------------------------------------------

    if sentence.startswith(
        (
            "ISBN",
            "ISSN",
            "DOI",
            "PMID",
            "Retrieved",
            "Archived",
            "References",
        )
    ):
        return True

    # -----------------------------------------------------
    # Reject sentences with strange character density
    # -----------------------------------------------------

    letters = sum(
        c.isalpha()
        for c in sentence
    )

    if len(sentence) > 0:

        letter_ratio = (
            letters /
            len(sentence)
        )

        if letter_ratio < 0.55:
            return True

    return False


# =========================================================
# FACT QUALITY SCORE
# =========================================================

def score_sentence(sentence):

    low = sentence.lower()

    score = 0

    # -----------------------------------------------------
    # Concrete facts
    # -----------------------------------------------------

    if re.search(
        r"\d",
        sentence
    ):
        score += 3

    # -----------------------------------------------------
    # Interesting fact language
    # -----------------------------------------------------

    strong_words = [

        "first",
        "largest",
        "smallest",
        "longest",
        "shortest",

        "only",
        "record",

        "discovered",
        "invented",
        "created",
        "built",
        "developed",

        "originally",
        "became",
        "survived",

        "contains",
        "weighs",
        "measures",
        "takes",

        "can",
        "more than",
        "less than",

        "million",
        "billion",

        "rare",
        "unique",
        "unusual",
        "unexpected",

    ]

    for word in strong_words:

        if word in low:
            score += 2

    # -----------------------------------------------------
    # Good narration length
    # -----------------------------------------------------

    words = len(
        sentence.split()
    )

    if 12 <= words <= 35:
        score += 5

    elif 36 <= words <= 50:
        score += 2

    # -----------------------------------------------------
    # Penalize academic writing
    # -----------------------------------------------------

    academic_words = [

        "methodology",
        "hypothesis",
        "correlation",
        "statistical",
        "et al.",
        "theorem",
        "equation",
        "dataset",

    ]

    for word in academic_words:

        if word in low:
            score -= 4

    # -----------------------------------------------------
    # Penalize boring definitions
    # -----------------------------------------------------

    if low.startswith(
        (
            "is a",
            "is an",
            "refers to",
            "is the",
            "are the",
        )
    ):
        score -= 2

    return score


# =========================================================
# FIND FACT
# =========================================================

def choose_fact(topic):

    queries = [

        topic,

        f"{topic} interesting facts",

        f"{topic} unusual facts",

        f"{topic} history",

        f"{topic} records",

        f"{topic} discoveries",

    ]

    random.shuffle(
        queries
    )

    candidates = []

    for query in queries:

        print(
            "Searching:",
            query
        )

        try:

            pages = wiki_search(
                query
            )

        except Exception as error:

            print(
                "Search failed:",
                error
            )

            continue

        for page in pages:

            title = page.get(
                "title"
            )

            if not title:
                continue

            try:

                source = wiki_page(
                    title
                )

            except Exception as error:

                print(
                    "Page failed:",
                    title,
                    error
                )

                continue

            sentences = sentences_from(
                source
            )

            for sentence in sentences:

                if is_bad(
                    sentence
                ):
                    continue

                score = score_sentence(
                    sentence
                )

                # Random variation so the same
                # top sentence isn't always selected.
                score += random.uniform(
                    0,
                    3
                )

                candidates.append(
                    (
                        score,
                        title,
                        sentence
                    )
                )

    if not candidates:

        raise RuntimeError(
            "Could not find a clean fact from Wikipedia."
        )

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Don't always choose absolute #1.
    top_count = min(
        15,
        len(candidates)
    )

    top = candidates[
        :top_count
    ]

    chosen = random.choice(
        top
    )

    return (
        chosen[1],
        chosen[2]
    )


# =========================================================
# RANDOM TOPIC
# =========================================================

topic = random.choice(
    TOPICS
)

print()
print(
    "=" * 60
)

print(
    "RANDOM TOPIC:",
    topic
)

print(
    "=" * 60
)


# =========================================================
# FIND FACT
# =========================================================

title, fact = choose_fact(
    topic
)

fact = clean(
    fact
)


# =========================================================
# FINAL QUALITY CHECK
# =========================================================

if is_bad(
    fact
):

    raise RuntimeError(
        "Selected fact failed the garbage filter."
    )


# =========================================================
# HOOK + BRIDGES
# =========================================================

hook = random.choice(
    HOOKS
)

bridge1 = random.choice(
    BRIDGES
)

bridge2 = random.choice(
    BRIDGES
)


# =========================================================
# NARRATION
# =========================================================

lines = [

    hook,

    title.upper(),

    bridge1,

    fact,

    bridge2,

    "And that's what makes this so strange.",

    "Would you have guessed that?",

]


# =========================================================
# VISUAL SEARCH TERMS
# =========================================================

visual_terms = [

    topic,

    title,

    f"{topic} photo",

    f"{topic} close up",

    f"{topic} history",

    f"{topic} documentary",

    f"{title} photo",

    f"{title} history",

]


# Remove duplicates.

visual_terms = list(
    dict.fromkeys(
        visual_terms
    )
)


# =========================================================
# SAVE SELECTED FACT
# =========================================================

selected = {

    "topic": topic,

    "title": title,

    "fact": fact,

    "visual_terms": visual_terms,

}


(WORK / "selected.json").write_text(

    json.dumps(
        selected,
        ensure_ascii=False,
        indent=2
    ),

    encoding="utf-8"

)


# =========================================================
# SAVE SCRIPT
# =========================================================

(WORK / "script.txt").write_text(

    "\n".join(lines),

    encoding="utf-8"

)


# =========================================================
# PRINT RESULTS
# =========================================================

print()

print(
    "=" * 60
)

print(
    "FACT SELECTED"
)

print(
    "=" * 60
)

print(
    "Topic:",
    topic
)

print(
    "Wikipedia source:",
    title
)

print()

print(
    "NARRATION:"
)

print(
    "\n".join(lines)
)

print()

print(
    "VISUAL SEARCH TERMS:"
)

for term in visual_terms:

    print(
        "-",
        term
    )

print(
    "=" * 60
)

print(
    "Generator completed successfully."
)

print(
    "=" * 60
)
