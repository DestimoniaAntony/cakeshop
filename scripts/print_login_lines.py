p = r'templates/customer/login.html'
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        print(f'{i:03}: {line.rstrip()}')
