#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""javac 报错驱动修复：
   1) 通配符 import 按包映射改写
   2) 特殊改名的简单名同步（ClickType->ContainerInput 等）
   3) 依据“按类成员映射表”把缺失的成员名改成 26.1.2 官方名（按报错行列精确定位）
"""
import os
import re
import json
import glob
import zipfile
from collections import defaultdict

PROJ = r'E:\Files\milky-addon-26.1.2'
LOG = os.path.join(PROJ, 'build', 'javac.log')
SRC = os.path.join(PROJ, 'src')
MCJAR = r'D:\mc\.minecraft\versions\MAIN\MAIN.jar'

mm = json.load(open(os.path.join(PROJ, 'docs', 'member-map.json'), encoding='utf-8'))
MEMBER = mm['member']
PKG = mm['package']
HIER = json.load(open(os.path.join(PROJ, 'docs', 'hierarchy.json'), encoding='utf-8'))


def ancestors(fqn):
    """自己 + 所有父类/接口（去环）"""
    seen, stack = [], [fqn]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.append(c)
        for p in HIER.get(c, []):
            if p and p not in seen:
                stack.append(p)
    return seen

SPECIAL_SIMPLE = {
    'ClickType': 'ContainerInput',      # SlotActionType -> ClickType -> ContainerInput
    'ResourceLocation': 'Identifier',
}


def build_index():
    idx = defaultdict(set)
    jars = [MCJAR] + glob.glob(os.path.join(PROJ, 'libs', '*.jar'))
    for j in jars:
        try:
            z = zipfile.ZipFile(j)
        except Exception:
            continue
        for n in z.namelist():
            if n.endswith('.class') and '$' not in n:
                fqn = n[:-6].replace('/', '.')
                idx[fqn.rsplit('.', 1)[-1]].add(fqn)
        z.close()
    return idx


def fix_wildcard_imports():
    n = 0
    pat = re.compile(r'^import (net\.minecraft(?:\.[\w$]+)*)\.\*;\s*$', re.M)
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        def rep(m):
            pkg = m.group(1)
            return 'import %s.*;' % PKG.get(pkg, pkg)
        nt = pat.sub(rep, t)
        if nt != t:
            open(path, 'w', encoding='utf-8', newline='\n').write(nt)
            n += 1
    return n


def fix_special_simple():
    n = 0
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        o = t
        for old, new in SPECIAL_SIMPLE.items():
            t = re.sub(r'\b%s\b' % re.escape(old), new, t)
        if t != o:
            open(path, 'w', encoding='utf-8', newline='\n').write(t)
            n += 1
    return n


def parse_errors(text):
    errs = []
    blocks = re.split(r'(?=^[A-Z]:\\[^\n]*?: error:)', text, flags=re.M)
    for b in blocks:
        m = re.match(r'^([A-Z]:\\[^\n]*?):(\d+): error: cannot find symbol', b)
        if not m:
            continue
        f, ln = m.group(1), int(m.group(2))
        sm = re.search(r'symbol:\s+(method|variable|class)\s+(\S+)', b)
        if not sm:
            continue
        kind, name = sm.group(1), sm.group(2)
        loc = re.search(r'location:\s+(?:variable \S+ of type|class|interface)\s+([\w.$]+)', b)
        if not loc:
            continue
        # 定位 caret：lines[0] 是 "file:line: error:"，其后是若干源码行 + caret 行；
        # caret 行上面那一行才是它对应的源码行（相对源码块起点偏移）
        lines = b.splitlines()
        sline, col = None, None
        for i, l in enumerate(lines):
            if '^' in l:
                col = l.index('^')
                sline = ln + (i - 2)          # i=2 时对应首行 ln
                break
        if sline is None or sline < 1:
            continue
        errs.append(dict(file=f, line=ln, kind=kind, sym=re.sub(r'\(.*', '', name),
                         owner=loc.group(1), sline=sline, col=col))
    return errs


def main():
    print('wildcard imports fixed in %d files' % fix_wildcard_imports())
    print('special simple names fixed in %d files' % fix_special_simple())

    idx = build_index()
    errs = parse_errors(open(LOG, encoding='utf-8', errors='replace').read())
    print('errors parsed=%d' % len(errs))

    edits = defaultdict(list)
    manual = defaultdict(int)
    for e in errs:
        cands = idx.get(e['owner'], set())
        props = set()
        for c in cands:
            for anc in ancestors(c):
                m = MEMBER.get(anc, {})
                if e['sym'] in m:
                    props.add(m[e['sym']])
                    break
        if len(props) == 1:
            edits[e['file']].append((e['sline'], e['col'], e['sym'], next(iter(props))))
        else:
            manual[(e['owner'], e['sym'], e['kind'])] += 1

    total = 0
    for path, lst in edits.items():
        lines = open(path, encoding='utf-8').read().split('\n')
        for sline, col, old, new in sorted(lst, key=lambda x: (-x[0], -x[1])):
            i = sline - 1
            if i < 0 or i >= len(lines):
                continue
            s = lines[i]
            pos = None
            for c in (col, col - 1, col + 1, col - 2, col + 2):
                if c >= 0 and s.startswith(old, c) and (c == 0 or not (s[c - 1].isalnum() or s[c - 1] in '_$')):
                    pos = c
                    break
            if pos is None:
                for m in re.finditer(r'(?<![\w$])%s(?![\w$])' % re.escape(old), s):
                    if pos is None or abs(m.start() - col) < abs(pos - col):
                        pos = m.start()
            if pos is None:
                continue
            lines[i] = s[:pos] + new + s[pos + len(old):]
            total += 1
        open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('member renames applied=%d' % total)
    if manual:
        print('MANUAL (%d 类不同符号):' % len(manual))
        for (owner, sym, kind), n in sorted(manual.items(), key=lambda kv: -kv[1])[:40]:
            print('   %-32s %-24s %-9s x%d' % (owner, sym, kind, n))


if __name__ == '__main__':
    main()
