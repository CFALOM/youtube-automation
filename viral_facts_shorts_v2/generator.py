```python
import json
import os
import random
import re
import html
import pathlib
import requests
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

UA = "ViralFactsShorts/2.0"

# =========================================================
# HUGE TOPIC POOL
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

    # PLACES
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


HOOKS = [
    "STOP SCROLLING — THIS IS REAL.",
    "THIS SOUNDS FAKE, BUT IT'S REAL.",
    "YOU PROBABLY DIDN'T KNOW THIS.",
    "THIS FACT GETS CRAZIER THE MORE YOU THINK ABOUT IT.",
    "ALMOST NOBODY KNOWS THIS.",
    "THIS IS ONE OF THE WEIRDEST FACTS YOU'LL HEAR TODAY.",
]


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

    return response.json().get("pages", [])


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

    return response.json().get("source", "")


# =========================================================
# TEXT CLEANING
# =========================================================

def clean(text):

    text = html.unescape(text)

    # Remove Wikipedia references.
    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    # Remove URLs.
    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    # Remove obvious article identifiers.
    text = re.sub(
        r"\b(?:doi|isbn|issn|article|pmid|id)\s*[:#]?\s*[\w./-]*\d[\w./-]*",
        "",
        text,
        flags=re.I
    )

    # Remove long garbage alphanumeric strings.
    text = re.sub(
        r"\b[a-zA-Z]*\d[a-zA-Z0-9_-]{8,}\b",
        "",
        text
    )

    # Remove repeated punctuation.
    text = re.sub(
        r"[|]{2,}",
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
# SENTENCE EXTRACTION
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

        if len(sentence) > 320:
            continue

        result.append(sentence)

    return result


# =========================================================
# GARBAGE DETECTOR
# =========================================================

def is_bad(sentence):

    low = sentence.lower()

    # Obvious metadata.
    bad_words = [
        "doi",
        "isbn",
        "issn",
        "pmid",
        "article number",
        "citation needed",
        "edit",
        "retrieved",
        "archived",
        "references",
        "external links",
    ]

    if any(
        word in low
        for word in bad_words
    ):
        return True

    # URLs.
    if "http://" in low or "https://" in low:
        return True

    # Too many numbers = probably metadata.
    numbers = re.findall(
        r"\d+",
        sentence
    )

    if len(numbers) > 6:
        return True

    # Long strings containing mixed letters/numbers.
    garbage = re.findall(
        r"\b\w*\d\w{7,}\b",
        sentence
    )

    if garbage:
        return True

    # Weird punctuation.
    if sentence.count("/") > 3:
        return True

    if sentence.count("_") > 1:
        return True

    if len(sentence.split()) < 8:
        return True

    return False


# =========================================================
# FACT SCORING
# =========================================================

def score_sentence(sentence):

    low = sentence.lower()

    score = 0

    # Concrete information.
    if re.search(
        r"\d",
        sentence
    ):
        score += 3

    # Strong fact words.
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
    ]

    for word in strong_words:

        if word in low:
            score += 2

    # Prefer medium-length narration.
    words = len(
        sentence.split()
    )

    if 12 <= words <= 35:
        score += 4

    elif 36 <= words <= 50:
        score += 2

    # Penalize extremely academic language.
    academic = [
        "according to",
        "methodology",
        "et al.",
        "statistical",
        "hypothesis",
        "correlation",
    ]

    for word in academic:

        if word in low:
            score -= 3

    return score


# =========================================================
# FIND A FACT
# =========================================================

def choose_fact(topic):

    queries = [
        topic,
        f"{topic} interesting facts",
        f"{topic} history",
        f"{topic} unusual facts",
        f"{topic} records",
    ]

    random.shuffle(
        queries
    )

    candidates = []

    for query in queries:

        try:

            print(
                "Searching:",
                query
            )

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

            except Exception:

                continue

            for sentence in sentences_from(
                source
            ):

                if is_bad(
                    sentence
                ):
                    continue

                score = score_sentence(
                    sentence
                )

                # Small randomness prevents identical
                # top-ranked facts every time.
                score += random.uniform(
                    0,
                    3
                )

                candidates.append(
                    (
                        score,
                        title,
                        sentence,
                    )
                )

    if not candidates:

        raise RuntimeError(
            "Could not find a clean fact from the web."
        )

    candidates.sort(
        reverse=True
    )

    # Pick from the strongest candidates instead
    # of always taking exactly #1.
    top = candidates[
        :min(12, len(candidates))
    ]

    chosen = random.choice(
        top
    )

    return (
        chosen[1],
        chosen[2]
    )


# =========================================================
# SELECT TOPIC
# =========================================================

topic = random.choice(
    TOPICS
)

print()
print(
    "Selected topic:",
    topic
)

title, fact = choose_fact(
    topic
)

fact = clean(
    fact
)

# =========================================================
# FINAL SAFETY CHECK
# =========================================================

if is_bad(
    fact
):

    raise RuntimeError(
        "The selected fact failed the quality filter."
    )

# =========================================================
# CREATE SCRIPT
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

# Keep individual narration lines short enough
# for fast captions and good pacing.

lines = [
    hook,
    title.upper(),
    bridge1,
    fact,
    bridge2,
    "And that's what makes this so strange.",
    "Would you have guessed that?"
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
    f"{title} photo",
    f"{title} history",
    f"{topic} documentary",
]


# Remove duplicates while preserving order.

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
# SAVE NARRATION
# =========================================================

(WORK / "script.txt").write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# =========================================================
# OUTPUT
# =========================================================

print()
print("=" * 60)
print("VIRAL FACTS GENERATOR")
print("=" * 60)

print(
    "Topic:",
    topic
)

print(
    "Source:",
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

print("=" * 60)
```
