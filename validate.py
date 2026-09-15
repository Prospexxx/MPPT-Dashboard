#!/usr/bin/env python3
"""Static validator for the portfolio index.html (stdlib only)."""
import html.parser, re, os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
IDX  = os.path.join(BASE, 'index.html')
src  = open(IDX, encoding='utf-8').read()
problems = []

# ---- 1. well-formedness via stdlib HTMLParser (strict balance check) ----
VOID = {'meta','link','br','hr','img','input','source','path','circle','rect','use','stop','line','polygon','i'}
class Bal(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.ids = [], [], set()
    def handle_startendtag(self, tag, attrs):
        for k, v in attrs:
            if k == 'id' and v: self.ids.add(v)
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)
        for k, v in attrs:
            if k == 'id' and v: self.ids.add(v)
    def handle_endtag(self, tag):
        if tag in VOID: return
        if tag not in self.stack:
            self.errors.append(f'stray </{tag}>'); return
        # pop until match, reporting anything left open in between
        while self.stack:
            top = self.stack.pop()
            if top == tag: break
            self.errors.append(f'unclosed <{top}> inside </{tag}>')
p = Bal(); p.feed(src)
for tag in p.stack:
    if tag not in ('html','body'):
        problems.append(f'document ended with <{tag}> still open')
problems += p.errors[:25]

# ---- 2. JS-referenced element ids must exist ----
ids_used = set(re.findall(r"\$\(\s*'#([A-Za-z0-9_-]+)'\s*\)", src))
ids_used |= set(re.findall(r'getElementById\(\s*[\'"]([^\'"]+)[\'"]\s*\)', src))
ids_used |= set(re.findall(r"querySelector\(\s*'#([A-Za-z0-9_-]+)'\s*\)", src))
missing = sorted(i for i in ids_used if i not in p.ids)
if missing: problems.append(f'missing ids referenced by JS: {missing}')

# ---- 3. local asset references must resolve ----
refs = re.findall(r'(?:src|href)="([^"]+)"', src)
local = [r for r in refs if not re.match(r'^https?://|^mailto:|^tel:|^wa\.me|^#', r)]
bad = sorted({r for r in local if not os.path.exists(os.path.join(BASE, r.replace('/', os.sep)))})
if bad: problems.append(f'broken local refs: {bad}')

# ---- 4. inline <script> blocks must be syntactically valid JS ----
blocks = re.findall(r'<script>(.*?)</script>', src, re.S)
tmp = os.path.join(os.environ.get('LOCALAPPDATA', '/tmp'), 'mnh_check.js')
with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
    for i, b in enumerate(blocks):
        f.write(f'\n// block {i}\n' + b)
r = os.system(f'node --check "{tmp}"')
if r != 0:
    problems.append('inline JS failed node --check (see above)')
else:
    print(f'JS OK: {len(blocks)} inline block(s), {len(src)} chars total')

# ---- 5. embedded data sanity ----
m = re.search(r'const EXP\s*=\s*(\{.*?\});', src, re.S)
if not m:
    problems.append('EXP data object not found')
else:
    try:
        d = json.loads(m.group(1))
        for k in ('tele', 'pv'):
            if k not in d: problems.append(f'EXP missing key {k}')
        for k, v in d.get('tele', {}).items():
            if not v or len(v[0]) != 8: problems.append(f'tele[{k}] bad shape')
        for k, v in d.get('pv', {}).items():
            if not v or len(v[0]) != 7: problems.append(f'pv[{k}] bad shape')
        n = sum(len(v) for v in d.get('tele', {}).values()) + sum(len(v) for v in d.get('pv', {}).values())
        print(f'DATA OK: tele={ {k: len(v) for k, v in d["tele"].items()} } pv={ {k: len(v) for k, v in d["pv"].items()} } total={n} samples')
    except Exception as e:
        problems.append(f'EXP JSON invalid: {e}')

print()
if problems:
    print(f'FAIL: {len(problems)} problem(s)')
    for x in problems: print('  -', x)
    sys.exit(1)
print('PASS: structure, ids, assets, JS, data all valid.')
