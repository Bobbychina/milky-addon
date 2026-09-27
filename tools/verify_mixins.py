#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产物核验 v2：解析 @Mixin 目标类 + 注入描述符（长/短两式）+ @Shadow 成员，逐一在 26.1.2 jar 里验证"""
import os
import re
import glob
import zipfile
import subprocess

PROJ = r'E:\Files\milky-addon-26.1.2'
MCJAR = r'D:\mc\.minecraft\versions\MAIN\MAIN.jar'
JDK = [os.path.join(PROJ, 'tools', d) for d in os.listdir(os.path.join(PROJ, 'tools'))
       if d.startswith('jdk-25')][0]
MIXDIR = os.path.join(PROJ, 'src/main/java/com/milky/hunt/mixin')

cache = {}


def members(fqn):
    if fqn not in cache:
        r = subprocess.run([os.path.join(JDK, 'bin', 'javap.exe'), '-p', '-cp', MCJAR, fqn],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        cache[fqn] = r.stdout or ''
    return cache[fqn]


SIMPLE2FQN = {}
z = zipfile.ZipFile(MCJAR)
for n in z.namelist():
    if n.endswith('.class') and '$' not in n:
        f = n[:-6].replace('/', '.')
        SIMPLE2FQN.setdefault(f.rsplit('.', 1)[-1], set()).add(f)
z.close()

rows = []
for f in sorted(glob.glob(os.path.join(MIXDIR, '*.java'))):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'@Mixin\((\w+)\.class\)', t)
    owner_simple = m.group(1) if m else '?'
    owners = SIMPLE2FQN.get(owner_simple, set())
    fqn = sorted(owners)[0] if len(owners) == 1 else ('?', owners)

    for tgt in re.finditer(r'method\s*=\s*"([^"]+)"', t):
        v = tgt.group(1)
        mm = re.match(r'L([\w/$]+);([\w$<>]+)(\(.*\).*)$', v)
        if mm:
            cls, name, desc = mm.group(1).replace('/', '.'), mm.group(2), mm.group(3)
        else:
            mm = re.match(r'([\w$<>]+)(\(.*\).*)$', v)
            if mm:
                cls, name, desc = fqn, mm.group(1), mm.group(2)
            else:
                cls, name, desc = fqn, v, '  (仅方法名，按名核验)'
        body = members(cls)
        rows.append((os.path.basename(f), '%s#%s%s' % (cls.rsplit('.', 1)[-1], name, desc), name in body))

    for sh in re.finditer(r'@Shadow[^;]*?\s([\w$<>\[\]]+)\s+(\w+)\s*[;(]', t, re.S):
        rows.append((os.path.basename(f), '%s (shadow member %s)' % (owner_simple, sh.group(2)),
                     sh.group(2) in members(fqn)))

print('%-24s %-58s %s' % ('mixin', 'target', 'exists'))
bad = 0
for f, tgt, ok in rows:
    if not ok:
        bad += 1
    print('%-24s %-58s %s' % (f, tgt, 'OK' if ok else '*** MISSING ***'))
print('\n%d 项核验，%d 项缺失' % (len(rows), bad))
