#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计 javac 报错里的缺失符号：按 (所属类型, 符号名) 归类，并给出 1.21.4 映射表里的建议名"""
import os
import re
import json
from collections import Counter, defaultdict

PROJ = r'E:\Files\milky-addon-26.1.2'
LOG = os.path.join(PROJ, 'build', 'javac.log')

raw = json.load(open(os.path.join(PROJ, 'docs', 'mapping-raw.json'), encoding='utf-8'))
method_map = raw.get('method', {})
conf_m = raw.get('conflict_method', {})
conf_f = raw.get('conflict_field', {})

text = open(LOG, encoding='utf-8', errors='replace').read()
blocks = re.split(r'(?=^[A-Z]:\\[^\n]*?: error:)', text, flags=re.M)

pat = Counter()
items = []
for b in blocks:
    m = re.match(r'^([A-Z]:\\[^\n]*?):(\d+): error: (cannot find symbol|.*)', b)
    if not m:
        continue
    f, ln, kind = m.group(1), int(m.group(2)), m.group(3)
    if kind != 'cannot find symbol':
        continue
    sm = re.search(r'symbol:\s+(method|variable|class)\s+(\S+)', b)
    if not sm:
        continue
    s_kind, s_name = sm.group(1), sm.group(2)
    loc = re.search(r'location:\s+(?:variable \S+ of type|class|interface)\s+([\w.$]+)', b)
    locname = loc.group(1) if loc else '?'
    s_name_clean = re.sub(r'\(.*', '', s_name)
    pat[(locname, s_name_clean, s_kind)] += 1
    items.append((f, ln, locname, s_name_clean, s_kind))

print('缺失符号类别数=%d  总出现次数=%d' % (len(pat), sum(pat.values())))
print('%-34s %-26s %-9s %5s  %s' % ('所属类型', '缺失符号', '种类', '次数', '1.21.4 映射建议'))
for (loc, name, kind), n in pat.most_common(60):
    sug = method_map.get(name, '')
    if not sug and name in conf_m:
        sug = 'CONFLICT:' + ','.join(conf_m[name])
    print('%-34s %-26s %-9s %5d  %s' % (loc, name, kind, n, sug))
