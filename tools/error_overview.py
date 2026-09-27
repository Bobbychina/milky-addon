#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""当前 javac 报错全貌：按错误信息/符号分组"""
import os
import re
from collections import Counter, defaultdict

PROJ = r'E:\Files\milky-addon-26.1.2'
LOG = os.path.join(PROJ, 'build', 'javac.log')
text = open(LOG, encoding='utf-8', errors='replace').read()
blocks = re.split(r'(?=^[A-Z]:\\[^\n]*?: error:)', text, flags=re.M)

msgs = Counter()
sym = Counter()
files = Counter()
for b in blocks:
    m = re.match(r'^([A-Z]:\\[^\n]*?):(\d+): error: (.*)', b)
    if not m:
        continue
    files[os.path.basename(m.group(1))] += 1
    msg = m.group(3).strip()
    msgs[msg] += 1
    if msg == 'cannot find symbol':
        sm = re.search(r'symbol:\s+(method|variable|class)\s+(\S+)', b)
        loc = re.search(r'location:\s+(?:variable \S+ of type|class|interface)\s+([\w.$]+)', b)
        sym[((loc.group(1) if loc else '?'), sm.group(2) if sm else '?')] += 1

print('== 错误信息分布 ==')
for k, v in msgs.most_common(12):
    print('%5d  %s' % (v, k))
print('\n== 非“cannot find symbol”的错误样例 ==')
n = 0
for b in blocks:
    m = re.match(r'^([A-Z]:\\[^\n]*?):(\d+): error: (.*)', b)
    if m and m.group(3).strip() != 'cannot find symbol':
        print('---', b.strip()[:600])
        n += 1
        if n >= 8:
            break
print('\n== 缺失符号 Top 25 ==')
for (loc, s), v in sym.most_common(25):
    print('%5d  %-30s %s' % (v, loc, s))
print('\n== 按文件 ==')
for f, v in files.most_common(15):
    print('%5d  %s' % (v, f))
