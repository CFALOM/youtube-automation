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

UA = "ViralFactsShorts/Final/1.0"

# ============================================================
# TOPICS
# ============================================================

TOPICS = [
    # GAMING
    "Minecraft",
    "Minecraft history",
    "Minecraft mobs",
    "Minecraft secrets",
    "Minecraft development",
    "Minecraft updates",
    "Minecraft records",
    "Minecraft early versions",

    "Roblox",
    "Roblox history",
    "Roblox development",

    "Fortnite",
    "Fortnite history",

    "GTA",
    "GTA history",

    "Nintendo",
    "Nintendo history",
    "PlayStation",
    "PlayStation history",
    "Xbox",
    "video game history",
    "arcade games",

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
    "biology",
    "chemistry",
    "evolution",
    "quantum physics",

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
    "deep sea animals",

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
    "computer history",
    "robotics",
    "inventions",

    # HISTORY
    "ancient history",
    "Roman Empire",
    "ancient Egypt",
    "medieval history",
    "world history",
    "historical discoveries",
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
    "weird science",
    "weird history",
    "strange discoveries",
    "unusual inventions",
    "strange animals",
]


# ============================================================
# HOOKS
# ============================================================

HOOKS = [
    "WAIT — YOU NEED TO KNOW THIS.",
    "THIS SOUNDS COMPLETELY FAKE.",
    "YOU'VE PROBABLY NEVER HEARD THIS BEFORE.",
    "THIS GETS WEIRDER IN A SECOND.",
    "MOST PEOPLE HAVE NO IDEA THIS HAPPENED.",
    "THIS IS ONE OF THE STRANGEST FACTS I FOUND.",
    "YOU WON'T EXPECT WHAT HAPPENS NEXT.",
]


# ============================================================
# BRIDGES
# ============================================================

BRIDGES = [
    "But here's the part nobody talks about.",
    "And this is where it gets crazy.",
    "But there's a much stranger detail.",
    "Here's where things get interesting.",
    "And then something unexpected happened.",
]


# ============================================================
# WIKIPEDIA
# ============================================================

def wiki_search(query):

    url = "https://en.wikipedia.org/w/rest.php/v1/search/page"

    response = requests.get(
        url,
        params={
            "q": query,
            "limit": 10,
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


# ============================================================
# CLEAN TEXT
# ============================================================

def clean(text):

    text = html.unescape(text)

    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SENTENCES
# ============================================================

def get_sentences(text):

    text = clean(text)

    pieces = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    output = []

    for sentence in pieces:

        sentence = sentence.strip()

        words = sentence.split()

        if len(words) < 12:
            continue

        if len(words) > 55:
            continue

        output.append(sentence)

    return output


# ============================================================
# BORING / BAD FACT FILTER
# ============================================================

def bad_fact(sentence):

    low = sentence.lower()

    banned = [
        "citation needed",
        "references",
        "external links",
        "isbn",
        "doi",
        "pmid",
        "retrieved",
        "archived",
        "according to",
        "statistical",
        "methodology",
        "bibliography",
        "et al",
    ]

    if any(x in low for x in banned):
        return True

    # Don't select sentences that are mostly dates/numbers.
    numbers = re.findall(r"\d+", sentence)

    if len(numbers) > 5:
        return True

    # Avoid extremely technical writing.
    technical = [
        "algorithm",
        "implementation",
        "parameter",
        "coefficient",
        "derivative",
        "equation",
        "specification",
        "protocol",
        "architecture",
    ]

    technical_count = sum(
        1 for word in technical
        if word in low
    )

    if technical_count >= 2:
        return True

    return False


# ============================================================
# INTEREST SCORE
# ============================================================

def score_fact(sentence):

    low = sentence.lower()
    words = sentence.split()

    score = 0

    # Ideal short-form length.
    if 15 <= len(words) <= 32:
        score += 8

    elif 33 <= len(words) <= 42:
        score += 4

    else:
        score -= 3

    # Numbers often create concrete facts.
    if re.search(r"\d", sentence):
        score += 4

    # Strong curiosity words.
    exciting = [
        "first",
        "only",
        "never",
        "secret",
        "strange",
        "unexpected",
        "accidentally",
        "originally",
        "hidden",
        "discovered",
        "invented",
        "created",
        "destroyed",
        "survived",
        "record",
        "largest",
        "smallest",
        "longest",
        "shortest",
        "rare",
        "ancient",
        "million",
        "billion",
        "failed",
        "changed",
        "banned",
        "lost",
        "forgotten",
        "actually",
    ]

    for word in exciting:

        if word in low:
            score += 3

    # Good story verbs.
    story_words = [
        "happened",
        "became",
        "found",
        "made",
        "built",
        "used",
        "caused",
        "turned",
        "changed",
        "led",
    ]

    for word in story_words:

        if word in low:
            score += 2

    # Penalize academic language.
    boring = [
        "consists of",
        "is defined as",
        "is characterized by",
        "classification",
        "taxonomy",
        "species include",
        "chemical composition",
        "mathematical",
        "theoretical",
    ]

    for word in boring:

        if word in low:
            score -= 5

    # Randomness prevents identical results.
    score += random.uniform(0, 4)

    return score


# ============================================================
# FIND FACT
# ============================================================

def choose_fact(topic):

    searches = [
        topic,
        f"{topic} strange",
        f"{topic} surprising",
        f"{topic} unusual",
        f"{topic} history",
        f"{topic} first",
        f"{topic} discovered",
        f"{topic} secret",
    ]

    random.shuffle(searches)

    candidates = []

    for query in searches:

        print("Searching:", query)

        try:

            pages = wiki_search(query)

        except Exception as error:

            print("Search failed:", error)

            continue

        # Randomize page order.
        random.shuffle(pages)

        for page in pages:

            title = page.get("title")

            if not title:
                continue

            try:

                source = wiki_page(title)

            except Exception:

                continue

            sentences = get_sentences(source)

            random.shuffle(sentences)

            for sentence in sentences:

                if bad_fact(sentence):
                    continue

                score = score_fact(sentence)

                # Extra boost when page title is highly relevant.
                if topic.lower() in title.lower():
                    score += 4

                candidates.append(
                    (
                        score,
                        title,
                        sentence,
                    )
                )

    if not candidates:

        raise RuntimeError(
            "Could not find an interesting fact."
        )

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Choose from the strongest group instead of
    # always choosing exactly the same result.
    top_count = min(
        10,
        len(candidates)
    )

    selected = random.choice(
        candidates[:top_count]
    )

    return selected[1], selected[2]


# ============================================================
# CREATE SHORT-FORM SCRIPT
# ============================================================

topic = random.choice(TOPICS)

print()
print("=" * 60)
print("SELECTED TOPIC:", topic)
print("=" * 60)

title, fact = choose_fact(topic)

fact = clean(fact)

hook = random.choice(HOOKS)

bridge1 = random.choice(BRIDGES)

bridge2 = random.choice(BRIDGES)


# ============================================================
# MAKE FACT EASIER TO LISTEN TO
# ============================================================

# Remove awkward Wikipedia-style parenthetical sections.
fact = re.sub(
    r"\([^)]{0,100}\)",
    "",
    fact
)

fact = re.sub(
    r"\s+",
    " ",
    fact
).strip()


# ============================================================
# VISUAL TERMS
# ============================================================

# IMPORTANT:
# These are specific enough to find visuals related to
# the actual subject instead of generic stock imagery.

visual_terms = [
    title,
    f"{title} photo",
    f"{title} image",
    topic,
    f"{topic} photo",
    f"{topic} history",
]


# Remove duplicates.
visual_terms = list(
    dict.fromkeys(visual_terms)
)


# ============================================================
# SAVE
# ============================================================

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
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# NARRATION
# ============================================================

lines = [
    hook,
    f"Here's the weird part about {title}.",
    bridge1,
    fact,
    bridge2,
    "And that's why this fact is so crazy.",
    "Did you know that?",
]


(WORK / "script.txt").write_text(
    "\n".join(lines),
    encoding="utf-8",
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 60)
print("FACT SELECTED")
print("=" * 60)

print("Topic:", topic)
print("Source:", title)

print()
print("NARRATION:")
print()

for line in lines:
    print(line)

print()
print("VISUAL SEARCH TERMS:")

for term in visual_terms:
    print("-", term)

print("=" * 60)
