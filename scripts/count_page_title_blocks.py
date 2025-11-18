import os
base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
results = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                txt = fh.read()
            count = txt.count('{% block page_title %}')
            if count > 0:
                results.append((p, count))

if not results:
    print('No page_title blocks found')
else:
    for p, c in sorted(results, key=lambda x: (-x[1], x[0])):
        print(f'{c}x  {p}')
