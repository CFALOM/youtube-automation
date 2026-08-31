#!/usr/bin/env python3
import json, os, random, re, textwrap, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'work'
WORK.mkdir(exist_ok=True)

TOPICS = [
    ('science', 'Why Your Brain Misses Things Right in Front of You', ['inattentional blindness','attention science','brain perception']),
    ('history', 'The Strange Reason Ancient Cities Put Doors in Weird Places', ['ancient city doors','ancient architecture','city archaeology']),
    ('technology', 'Why Your Phone Battery Seems to Die Faster at 20%', ['smartphone battery percentage','lithium ion battery','battery calibration']),
    ('gaming', 'The Minecraft Feature Players Almost Never Notice', ['Minecraft old feature','Minecraft mechanics','Minecraft history']),
    ('money', 'Why Supermarkets Put the Things You Need at the Back', ['supermarket layout','consumer psychology','grocery store design']),
    ('space', 'Why Space Is Silent Even During Huge Explosions', ['space vacuum explosion','sound in space','vacuum physics']),
    ('everyday', 'Why Airplane Windows Have a Tiny Hole in Them', ['airplane window tiny hole','aircraft window design','aviation window']),
    ('internet', 'The Weird Reason Old Websites Look Completely Different', ['early web design','internet history','old websites']),
    ('animals', 'Why Some Animals Can See Colors We Cannot', ['animal color vision','ultraviolet vision','biology eyesight']),
    ('engineering', 'Why Bridges Move Even When They Look Completely Still', ['bridge movement','thermal expansion bridge','bridge engineering']),
    ('psychology', 'Why Your Brain Sometimes Makes You Remember Things Wrong', ['false memory psychology','human memory','memory reconstruction']),
    ('food', 'Why Popcorn Jumps When It Heats Up', ['popcorn science','corn kernel pressure','food science']),
    ('ocean', 'Why the Deep Ocean Is Colder Than You Think', ['deep ocean temperature','ocean thermocline','deep sea']),
    ('history', 'Why Some Maps Put a Country in the Center', ['map projection','world maps','cartography']),
    ('technology', 'Why Wi-Fi Can Slow Down When Nobody Is Downloading Anything', ['wifi interference','wireless congestion','wifi channels']),
    ('science', 'Why Hot Water Can Sometimes Freeze Faster Than Cold Water', ['Mpemba effect','water freezing','physics']),
    ('gaming', 'Why Games Put Invisible Walls in Places You Never See', ['game invisible walls','level design','video game boundaries']),
    ('mystery', 'The Odd Object Scientists Found Inside an Old Machine', ['archaeology unusual object','historical machine discovery','engineering artifact']),
    ('space', 'Why the Moon Looks Bigger Near the Horizon', ['moon illusion','visual perception','horizon moon']),
    ('everyday', 'Why Your Shower Gets Cold When Someone Uses Another Tap', ['water pressure shower','home plumbing','shower temperature']),
]

HOOKS = [
    'There is a weird reason this happens, and most people never notice it.',
    'You have probably seen this hundreds of times without asking why.',
    'At first this sounds wrong. Then you see what is actually happening.',
    'This looks completely normal, but there is a surprising reason behind it.',
    'The strange part is that the obvious explanation is not the real one.'
]


def clean(s):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s


def fetch_wikipedia(title):
    url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
    req = urllib.request.Request(url, headers={'User-Agent':'LongVideoFactory/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', 'ignore')
        # Minimal extraction: paragraphs from Wikipedia HTML without dependencies.
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.S|re.I)
        texts = []
        for p in paras:
            p = re.sub(r'<sup.*?</sup>', '', p, flags=re.S|re.I)
            p = re.sub(r'<.*?>', ' ', p)
            p = clean(p)
            p = re.sub(r'\[[0-9]+\]', '', p)
            if len(p) > 120:
                texts.append(p)
        return texts[:8]
    except Exception:
        return []


def extract_keyword_facts(topic_data, paragraphs):
    facts = []
    for p in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', p)
        for s in sentences:
            s = clean(s)
            if 70 <= len(s) <= 260 and len(s.split()) >= 12:
                facts.append(s)
    random.shuffle(facts)
    return facts[:24]


def build_script(title, category, keywords, facts):
    hook = random.choice(HOOKS)
    usable = facts or [
        f'The reason behind {title.lower()} is tied to how systems behave in ways that are easy to miss.',
        'Small details often matter because the system was designed around limits that are invisible during normal use.',
        'Once you know the basic mechanism, the strange part becomes much easier to understand.'
    ]

    target_words = 1450  # roughly 9–11 minutes at a natural pace
    sections = []
    sections.append(hook)
    sections.append(f'Today we are looking at {title.lower()}. The interesting part is not just what happens, but why it happens.')

    # Build a human-sounding sequence from research sentences. Avoid overclaiming.
    for i, fact in enumerate(usable[:18], 1):
        transitions = [
            'But that raises another question.',
            'Here is where it gets more interesting.',
            'There is one detail that changes the whole picture.',
            'Now look at what happens next.',
            'And this is the part people usually miss.',
            'That sounds simple, but there is another layer.'
        ]
        sections.append(random.choice(transitions))
        sections.append(fact)

    sections.extend([
        'Put all of that together and the strange result starts to make sense.',
        'The next time you see this, you will probably notice the detail that was easy to miss before.',
        'And that is what makes this topic so interesting: the answer was visible the whole time, but the reason was hiding in the background.'
    ])

    text = ' '.join(clean(x) for x in sections)
    words = text.split()
    if len(words) < target_words:
        filler = [
            'The important point is not that this happens by accident. It usually comes from a real limit, design choice, or physical effect.',
            'That small detail can have a much bigger effect than you would expect.',
            'Once the pieces are connected, the explanation becomes surprisingly simple.'
        ]
        while len(words) < target_words:
            text += ' ' + random.choice(filler)
            words = text.split()
    text = ' '.join(words[:target_words])
    return text


def main():
    random.seed()
    previous = []
    hist = WORK / 'topic_history.json'
    if hist.exists():
        try:
            previous = json.loads(hist.read_text())
        except Exception:
            previous = []

    candidates = TOPICS[:]
    previous_titles = {x.get('title') for x in previous if isinstance(x, dict)}
    fresh = [x for x in candidates if x[1] not in previous_titles] or candidates
    category, title, keywords = random.choice(fresh)

    paragraphs = []
    for kw in keywords:
        paragraphs.extend(fetch_wikipedia(kw))
    facts = extract_keyword_facts((category, title, keywords), paragraphs)
    script = build_script(title, category, keywords, facts)

    data = {
        'title': title,
        'category': category,
        'keywords': keywords,
        'hook': script.split('.')[0].strip() + '.',
        'script': script,
        'word_count': len(script.split()),
        'research_notes': facts[:12]
    }
    (WORK / 'script.json').write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    (WORK / 'script.txt').write_text(script + '\n', encoding='utf-8')
    previous.append({'title': title, 'category': category})
    hist.write_text(json.dumps(previous[-100:], indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'title': title, 'words': len(script.split()), 'category': category}))


if __name__ == '__main__':
    main()
