#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Yarn(1.21.4) -> Mojang official names 迁移 + 映射表导出。

思路：yarn 的 mergedv2 tiny 与 Mojang client.txt 都有 obf(official) 列，用 obf 名做桥：
  yarn 类名/成员名(obf 键)  <->  moj 类名/成员名(obf 键)
成员用 (obfOwner, obfName, desc) 精确配对（desc 由 obf 形翻成官方形），避免同名串号。
产物：docs/mapping-raw.json（类名表/全局名表）、docs/member-map.json（按类的成员映射 + 包映射）
副作用：按类名表重写 src 下的 net.minecraft.* 引用（类名、简单名、mixin 描述符）
"""
import os
import re
import json
import zipfile
from collections import defaultdict

ROOT = r'E:\Files\milky-addon-26.1.2'
APPLY_FIELDS = False
APPLY_METHODS = False          # 全局按名字替换成员名不安全，交给 javac 报错驱动
MAPDIR = os.path.join(ROOT, '.mappings')
SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, 'docs', 'mapping-report.txt')

PRIM = {'void': 'V', 'boolean': 'Z', 'byte': 'B', 'char': 'C', 'short': 'S',
        'int': 'I', 'long': 'J', 'float': 'F', 'double': 'D'}


def jvm_type(t):
    """'net.minecraft.core.BlockPos[]' -> '[Lnet/minecraft/core/BlockPos;'"""
    t = t.strip()
    if not t:
        return ''
    arr = 0
    while t.endswith('[]'):
        arr += 1
        t = t[:-2]
    if '<' in t:
        t = t[:t.index('<')]
    base = PRIM.get(t) or ('L' + t.replace('.', '/') + ';')
    return '[' * arr + base


def translate_desc(desc, obf2moj):
    """把 obf 形态描述符里的 L<obf>; 换成官方类名"""
    out, i = [], 0
    while i < len(desc):
        c = desc[i]
        if c == 'L':
            j = desc.find(';', i)
            if j < 0:
                out.append(c)
                i += 1
                continue
            obf = desc[i + 1:j]
            out.append('L' + obf2moj.get(obf, obf).replace('.', '/') + ';')
            i = j + 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


# ---------- 1. Mojang 官方映射 ----------
moj_class, moj_m_name, moj_f_name = {}, {}, {}
cls_re = re.compile(r'^(\S+) -> (\S+):$')
meth_re = re.compile(r'^\s+(?:\d+:\d+:)?(?P<ret>[^\s(]+)\s(?P<name>\S+)\((?P<params>[^)]*)\) -> (?P<obf>\S+)\s*$')
field_re = re.compile(r'^\s+(\S+) (\S+) -> (\S+)\s*$')
cur = None
for line in open(os.path.join(MAPDIR, 'client-1.21.4.txt'), encoding='utf-8'):
    line = line.rstrip('\n')
    m = cls_re.match(line)
    if m:
        cur = m.group(2)
        moj_class[cur] = m.group(1)
        continue
    if not cur or '->' not in line:
        continue
    m = meth_re.match(line)
    if m:
        name, obf = m.group('name'), m.group('obf')
        if name.startswith('lambda$') or name in ('<init>', '<clinit>'):
            continue
        desc = '(%s)%s' % (''.join(jvm_type(t) for t in m.group('params').split(',') if t.strip()),
                           jvm_type(m.group('ret')))
        moj_m_name.setdefault((cur, obf, desc), name)
        continue
    m = field_re.match(line)
    if m:
        if m.group(2).startswith(('lambda$', 'this$', 'val$')):
            continue
        moj_f_name.setdefault((cur, m.group(3)), m.group(2))

# ---------- 2. Yarn mergedv2 tiny（official / intermediary / named） ----------
z = zipfile.ZipFile(os.path.join(MAPDIR, 'yarn-mergedv2.jar'))
tiny = [n for n in z.namelist() if n.endswith('mappings.tiny')][0]
lines = z.read(tiny).decode('utf-8').splitlines()

yarn_class = {}                                  # obf -> yarn dotted
yarn_m = {}                                      # (obfOwner, obfName, obfDesc) -> {yarnName}
yarn_f = {}                                      # (obfOwner, obfName) -> {yarnName}
cur = None
for line in lines[1:]:
    if line.startswith('c\t'):
        p = line.split('\t')
        cur = p[1]
        named = p[3] if len(p) > 3 else p[2]
        if 'class_' in named or '/' not in named:
            continue
        yarn_class[cur] = named.replace('/', '.')
    elif line.startswith('\tm\t') or line.startswith('\tf\t'):
        p = line.lstrip('\t').split('\t')
        if not cur or len(p) < 5:                # m/f <obfDesc> <obfName> <intermediary> <named>
            continue
        if p[0] == 'm':
            yarn_m.setdefault((cur, p[2], p[1]), set()).add(p[4])
        else:
            yarn_f.setdefault((cur, p[2]), set()).add(p[4])

# ---------- 3. 类名映射 ----------
class_map = {yn: moj_class[obf] for obf, yn in yarn_class.items()
             if obf in moj_class and moj_class[obf] != yn}

pkg_votes = defaultdict(lambda: defaultdict(int))
for yn, mn in class_map.items():
    pkg_votes['.'.join(yn.split('.')[:-1])]['.'.join(mn.split('.')[:-1])] += 1
package_map = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in pkg_votes.items()}

# ---------- 4. 按类的成员映射（desc 精确配对） ----------
member_map = defaultdict(dict)                   # mojOwner -> {yarnName: mojName}
collide = defaultdict(set)
for (obf, obfname, obfdesc), ynames in yarn_m.items():
    desc = translate_desc(obfdesc, moj_class)
    mn = moj_m_name.get((obf, obfname, desc))
    if not mn:
        continue
    owner = moj_class.get(obf)
    if not owner:
        continue
    for yn in ynames:
        if yn == mn or 'method_' in yn:
            continue
        prev = member_map[owner].get(yn)
        if prev and prev != mn:
            collide[owner].add(yn)
        else:
            member_map[owner][yn] = mn
for (obf, obfname), ynames in yarn_f.items():
    mn = moj_f_name.get((obf, obfname))
    owner = moj_class.get(obf)
    if not mn or not owner:
        continue
    for yn in ynames:
        if yn == mn or 'field_' in yn:
            continue
        prev = member_map[owner].get(yn)
        if prev and prev != mn:
            collide[owner].add(yn)
        else:
            member_map[owner][yn] = mn
for owner, bad in collide.items():
    for yn in bad:
        member_map[owner].pop(yn, None)

json.dump({'member': {k: v for k, v in member_map.items() if v},
           'package': package_map,
           'owner_conflicts': {k: sorted(v) for k, v in collide.items() if v}},
          open(os.path.join(ROOT, 'docs', 'member-map.json'), 'w', encoding='utf-8'), indent=1)

# ---------- 5. 重写源码：类名 / 简单名 / mixin 描述符 ----------
mc_dot_re = re.compile(r'net\.minecraft(?:\.[A-Za-z0-9_$]+)+')
mc_slash_re = re.compile(r'net/minecraft(?:/[A-Za-z0-9_$]+)+')


def map_dot(full):
    if full in class_map:
        return class_map[full]
    base = full
    while '.' in base:
        base = base.rsplit('.', 1)[0]
        if base in class_map:
            return class_map[base] + full[len(base):]
    return None


def map_slash(full):
    r = map_dot(full.replace('/', '.'))
    return r.replace('.', '/') if r else None


changed, stats = 0, defaultdict(int)
for dirpath, _, files in os.walk(SRC):
    for fn in files:
        if not fn.endswith('.java'):
            continue
        p = os.path.join(dirpath, fn)
        text = open(p, encoding='utf-8').read()
        orig = text

        simple_pairs = {}
        for line in text.splitlines():
            m = re.match(r'^import (?:static )?(net\.minecraft\.[\w.$]+);', line)
            if m and map_dot(m.group(1)):
                new = map_dot(m.group(1))
                if new != m.group(1):
                    o, n = m.group(1).rsplit('.', 1)[-1], new.rsplit('.', 1)[-1]
                    if o != n:
                        simple_pairs[o] = n

        text = mc_dot_re.sub(lambda m: (map_dot(m.group(0)) or m.group(0)), text)
        text = mc_slash_re.sub(lambda m: (map_slash(m.group(0)) or m.group(0)), text)
        for o, n in simple_pairs.items():
            text, k = re.subn(r'\b%s\b' % re.escape(o), n, text)
            stats['simple'] += k
        if text != orig:
            open(p, 'w', encoding='utf-8', newline='\n').write(text)
            changed += 1
        stats['files'] = changed

report = ('class_map=%d  member owners=%d entries=%d  package_map=%d  changed_files=%d  %s'
          % (len(class_map), len(member_map), sum(len(v) for v in member_map.values()),
             len(package_map), changed, dict(stats)))
open(OUT, 'w', encoding='utf-8').write(report + '\n')
print(report)
json.dump({'class': class_map, 'package': package_map},
          open(os.path.join(ROOT, 'docs', 'mapping-raw.json'), 'w', encoding='utf-8'), indent=1)
