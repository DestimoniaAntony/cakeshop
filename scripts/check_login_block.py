p = r'templates/customer/login.html'
s = open(p, 'r', encoding='utf-8').read()
print('Count:', s.count('{% block page_title %}'))
for i, line in enumerate(s.splitlines(), 1):
    if '{% block page_title %}' in line:
        print(i, line)
