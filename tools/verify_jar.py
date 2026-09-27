#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产物核验：jar 结构 / fabric.mod.json / mixin 注入目标是否在 26.1.2 里真实存在"""
import os
import re
import json
import glob
import zipfile
import subprocess

PROJ = r'E:\Files\milky-addon-26.1.2'
MCJAR = r'D:\mc\.minecraft\versions\MAIN\MAIN.jar'
JDK = [os.path.join(PROJ, 'tools', d) for d in os.listdir(os.path.join(PROJ, 'tools'))
       if d.startswith('jdk-25')][0]

jar = sorted(glob.glob(os.path.join(PROJ, 'build', 'libs', '*.jar')))[-1]
print('=== jar:', os.path.basename(jar), '%.2f MB' % (os.path.getsize(jar) / 1048576))
z = zipfile.ZipFile(jar)
names = z.namelist()
print('entries=%d' % len(names))
for pat in ('fabric.mod.json', 'mixins.json', 'accesswidener', 'assets/'):
    hits = [n for n in names if pat in n]
    print('  %-18s %s' % (pat, hits[:4]))
print('  classes=%d' % len([n for n in names if n.endswith('.class')]))
print('\n=== fabric.mod.json (in jar) ===')
print(z.read('fabric.mod.json').decode('utf-8'))

mixins = json.load(z.open('milky-mod.mixins.json'))
print('=== mixins.json ===', mixins.get('package'), mixins.get('compatibilityLevel'), mixins.get('client'))

# 逐个核验注入目标是否存在
src = open(os.path.join(PROJ, 'src/main/java/com/milky/hunt/mixin',
                        'LivingEntityMixin.java'), encoding='utf-8').read()
targets = []
for f in glob.glob(os.path.join(PROJ, 'src/main/java/com/milky/hunt/mixin/*.java')):
    t = open(f, encoding='utf-8').read()
    cls = re.search(r'@Mixin\((\w+)\.class\)', t)
    for m in re.finditer(r'method = "L([\w/$]+);([\w$<>]+)(\([^"]*\)[^"]*)"', t):
        targets.append((os.path.basename(f), m.group(1).replace('/', '.'), m.group(2), m.group(3)))
    for m in re.finditer(r'method = "(\w+)"', t):
        targets.append((os.path.basename(f), '?', m.group(1), '?'))

print('\n=== 注入目标核验 ===')
cache = {}


def members(fqn):
    if fqn not in cache:
        r = subprocess.run([os.path.join(JDK, 'bin', 'javap.exe'), '-p', '-cp', MCJAR, fqn],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        cache[fqn] = r.stdout or ''
    return cache[fqn]


ok = True
for f, owner, name, desc in targets:
    body = members(owner)
    hit = name in body
    print('  %-24s %-46s %s' % (f, owner + '#' + name + desc, 'OK' if hit else 'MISSING'))
    ok = ok and hit
print('\n结论:', 'ALL TARGETS FOUND' if ok else '有目标缺失，需修')
