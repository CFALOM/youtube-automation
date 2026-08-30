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

UA = "FinalViralFactsShorts/1.0"

# Large rotating topic pool.
TOPICS = [
    "Minecraft",
    "Minecraft history",
    "Minecraft mobs",
    "Minecraft secrets",
    "Minecraft development",
    "Roblox",
    "Roblox history",
    "GTA",
    "GTA history",
    "Fortnite",
    "Fortnite history",
    "Nintendo",
    "PlayStation",
    "Xbox",
    "video game history",
    "gaming history",
    "space",
    "planets",
    "black holes",
    "NASA",
    "astronomy",
    "animals",
    "octopus",
    "crows",
    "sharks",
    "dogs",
    "cats",
    "human body",
    "psychology",
    "science",
    "physics",
    "chemistry",
    "technology",
    "artificial intelligence",
    "internet history",
    "social media history",
    "computers",
    "smartphones",
    "inventions",
    "aviation",
    "cars",
    "oceans",
    "weather",
    "geography",
    "ancient history",
    "medieval history",
    "world history",
    "famous inventions",
    "money history",
    "food history",
    "movies",
    "music history",
    "sports history",
    "weird facts",
]

HOOKS = [
    "STOP SCROLLING — YOU PROBABLY DIDN'T KNOW THIS.",
    "THIS SOUNDS FAKE, BUT IT'S REAL.",
    "WAIT UNTIL YOU HEAR THE LAST PART.",
    "THIS GETS WEIRDER THE MORE YOU THINK ABOUT IT.",
    "ALMOST NOBODY KNOWS THIS.",
    "HERE'S SOMETHING REALLY STRANGE.",
]

BRIDGES = [
    "But here's where it gets interesting.",
    "And this is the crazy part.",
    "But there's one detail people miss.",
    "Now it gets even stranger.",
    "Here's the part that surprises people.",
]


def wiki_search(query):
    url = "https://en.wikipedia.org/w/rest.php/v1/search/page"

    response = requests.get(
        url,
        params={
            "q": query,
            "limit": 10
        },
        headers={"User-Agent": UA},
        timeout=20
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
        headers={"User-Agent": UA},
        timeout=20
    )

    response.raise_for_status()

    return response.json().get("source", "")


def clean(text):
    text = html.unescape(text)

    # Remove references.
    text = re.sub(r"\[[0-9]+\]", "", text)

    # Remove excessive whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_paragraphs(text):
    text = clean(text)

    # Break approximately into useful chunks.
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []

    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) < 500:
            current += " " + sentence
        else:
            if len(current) > 120:
                chunks.append(current.strip())

            current = sentence

    if len(current) > 120:
        chunks.append(current.strip())

    return chunks


def choose_fact(topic):
    searches = [
        topic,
        f"{topic} history",
        f"strange {topic} fact",
        f"interesting {topic} fact",
        f"{topic} unusual",
    ]

    random.shuffle(searches)

    candidates = []

    for query in searches:

        try:
            pages = wiki_search(query)

            for page in pages[:8]:

                title = page.get("title")

                if not title:
                    continue

                try:
                    source = wiki_page(title)
                except Exception:
                    continue

                paragraphs = extract_paragraphs(source)

                for paragraph in paragraphs:
                    # Prefer paragraphs containing concrete details.
                    score = 0

                    if any(char.isdigit() for char in paragraph):
                        score += 2

                    if len(paragraph) > 180:
                        score += 1

                    if any(
                        word in paragraph.lower()
                        for word in [
                            "first",
                            "largest",
                            "longest",
                            "only",
                            "three",
                            "two",
                            "million",
                            "year",
                            "invented",
                            "created",
                            "discovered",
                            "originally",
                            "record",
                        ]
                    ):
                        score += 2

                    candidates.append(
                        (score + random.random(), title, paragraph)
                    )

        except Exception as error:
            print("Search failed:", error)

    if not candidates:
        raise RuntimeError(
            "Could not discover a fact from the web."
        )

    candidates.sort(reverse=True)

    return candidates[0][1], candidates[0][2]


topic = random.choice(TOPICS)

title, fact = choose_fact(topic)

fact = clean(fact)

hook = random.choice(HOOKS)
bridge1 = random.choice(BRIDGES)
bridge2 = random.choice(BRIDGES)

# Keep narration reasonably short.
if len(fact) > 700:
    fact = fact[:700].rsplit(".", 1)[0] + "."

# Scene-oriented script.
lines = [
    hook,
    title.upper(),
    bridge1,
    fact,
    bridge2,
    "And that's what makes this fact so strange.",
    "Would you have guessed that?",
]

# Visual search phrases.
visual_terms = [
    topic,
    title,
    f"{topic} {title}",
    f"{topic} close up",
    f"{topic} history",
    f"{topic} detail",
]

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

(WORK / "script.txt").write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print()
print("=" * 60)
print("FINAL VIRAL FACTS GENERATOR")
print("=" * 60)
print("Topic:", topic)
print("Source:", title)
print()
print("\n".join(lines))
print("=" * 60)
