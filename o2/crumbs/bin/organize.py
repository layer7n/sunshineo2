import json


with open('furn.json') as f:
    jfile = json.loads(f.read())


organized = open('organized.json', 'w')
organized.write(json.dumps(jfile, sort_keys=True, indent=True))
organized.close()