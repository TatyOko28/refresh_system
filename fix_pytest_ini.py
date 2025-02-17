with open('pytest.ini', 'r', encoding='utf-8-sig') as f:
    content = f.read()
with open('pytest.ini', 'w', encoding='utf-8') as f:
    f.write(content)
