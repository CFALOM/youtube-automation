import json, random, pathlib
ROOT=pathlib.Path(__file__).parent
facts=json.loads((ROOT/'facts/facts.json').read_text(encoding='utf-8'))
item=random.choice(facts)
hooks=['STOP SCROLLING — THIS IS REAL.','WAIT FOR THE LAST PART.','THIS FACT GETS STRANGER EVERY FEW SECONDS.','ALMOST NOBODY KNOWS THIS.','THIS SOUNDS LIKE SCIENCE FICTION.']
bridges=['But here is where it gets crazy.','And that is not even the strangest part.','Now comes the weird part.','But one detail changes everything.']
lines=[random.choice(hooks),item['fact'],random.choice(bridges),item['detail'],random.choice(bridges),item['payoff'],'Would you have guessed that? Follow for the next one.']
work=ROOT/'work'; work.mkdir(exist_ok=True)
(work/'selected.json').write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
(work/'script.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))
