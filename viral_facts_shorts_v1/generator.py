import json, random, pathlib
ROOT = pathlib.Path(__file__).parent
facts = json.loads((ROOT/'facts/facts.json').read_text(encoding='utf-8'))
item = random.choice(facts)
hooks = ['This sounds fake, but it is actually real.','Most people do not know this.','Here is a fact that sounds completely impossible.','This is one of the strangest facts in science.']
payoffs = ['And that is what makes this so strange.','Nature is more bizarre than fiction.','So yes, this really happens.']
script = f"{random.choice(hooks)}\n\n{item['fact']}\n\n{item['detail']}\n\n{random.choice(payoffs)}\n\nDid you know this one? Follow for another fact."
out=ROOT/'work'; out.mkdir(exist_ok=True)
(out/'selected.json').write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'script.txt').write_text(script,encoding='utf-8')
print(script)
