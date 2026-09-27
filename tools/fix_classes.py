#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 javac 报错自动纠正类引用：
   - 从 MAIN.jar 建 26.1.2 真实类表；
   - 解析 "cannot find symbol: class X / location: package P" 的 import 错误；
   - 用简单名在真实类表里找候选（唯一即替换；多个取包名最接近的）；
   - 附带一批已知改名/API 变化特例。
"""
import os
import re
import sys
import glob
import json
import zipfile

PROJ = r'E:\Files\milky-addon-26.1.2'
MCJAR = r'D:\mc\.minecraft\versions\MAIN\MAIN.jar'
LOG = os.path.join(PROJ, 'build', 'javac.log')
SRC = os.path.join(PROJ, 'src')

# 已知特例：1.21.4 官方名 -> 26.1.2 官方名（含 Meteor 侧）
SPECIAL = {
    'meteordevelopment.meteorclient.mixininterface.IVec3d': 'meteordevelopment.meteorclient.mixininterface.IVec3',
    'net.minecraft.resources.ResourceLocation': 'net.minecraft.resources.Identifier',
    'net.minecraft.Util': 'net.minecraft.util.Util',
    # 26.1.2 里 ClickType 又改名成 ContainerInput
    'net.minecraft.world.inventory.ClickType': 'net.minecraft.world.inventory.ContainerInput',
}


def strip_nullable():
    """org.jetbrains.annotations 不在编译期 classpath 上：去掉 @Nullable 注解与其 import"""
    n = 0
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        o = t
        t = re.sub(r'^import org\.jetbrains\.annotations\.Nullable;\n', '', t, flags=re.M)
        t = t.replace('@Nullable ', '')
        if t != o:
            open(path, 'w', encoding='utf-8', newline='\n').write(t)
            n += 1
    return n


def mc_classes():
    z = zipfile.ZipFile(MCJAR)
    names = {n[:-6].replace('/', '.') for n in z.namelist() if n.endswith('.class')}
    z.close()
    return names


def load_extra_classes():
    """Meteor / baritone / xaero 等 jar 里的类，用于修非 MC 的引用"""
    extra = set()
    for j in glob.glob(os.path.join(PROJ, 'libs', '*.jar')):
        try:
            z = zipfile.ZipFile(j)
            extra |= {n[:-6].replace('/', '.') for n in z.namelist() if n.endswith('.class')}
            z.close()
        except Exception:
            pass
    return extra


def parse_class_errors(text):
    """返回 [(file, line, missing_fqn)]"""
    out = []
    blocks = re.split(r'(?=^[A-Z]:\\[^\n]*?: error:)', text, flags=re.M)
    for b in blocks:
        m = re.match(r'^([A-Z]:\\[^\n]*?):(\d+): error: cannot find symbol', b)
        if not m:
            continue
        f, ln = m.group(1), int(m.group(2))
        sm = re.search(r'symbol:\s+class (\S+)', b)
        pm = re.search(r'location:\s+package (\S+)', b)
        if sm and pm:
            out.append((f, ln, pm.group(1) + '.' + sm.group(1)))
    return out


def main():
    print('nullable stripped in %d files' % strip_nullable())
    log = open(LOG, encoding='utf-8', errors='replace').read()
    errs = parse_class_errors(log)
    if not errs:
        print('no class-level errors')
        return
    mc = mc_classes()
    extra = load_extra_classes()
    index = {}
    for fqn in list(mc) + list(extra):
        index.setdefault(fqn.rsplit('.', 1)[-1], []).append(fqn)

    missing = sorted({fqn for _, _, fqn in errs})
    fixes = {}
    manual = []
    for fqn in missing:
        if fqn in SPECIAL:
            fixes[fqn] = SPECIAL[fqn]
            continue
        simple = fqn.rsplit('.', 1)[-1]
        cands = index.get(simple, [])
        if len(cands) == 1:
            fixes[fqn] = cands[0]
        elif len(cands) > 1:
            # 取与旧包名公共前缀最长的候选
            oldpkg = fqn.rsplit('.', 1)[0].split('.')
            def score(c):
                cp = c.rsplit('.', 1)[0].split('.')
                n = 0
                for a, b in zip(oldpkg, cp):
                    if a != b:
                        break
                    n += 1
                return -n
            cands.sort(key=score)
            fixes[fqn] = cands[0]
            print('MULTI %s -> %s  (cands: %s)' % (fqn, cands[0], ', '.join(cands[:4])))
        else:
            manual.append(fqn)

    # 应用
    changed = 0
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        o = t
        for old, new in fixes.items():
            t = t.replace(old, new)
        if t != o:
            open(path, 'w', encoding='utf-8', newline='\n').write(t)
            changed += 1
    print('class-errors=%d  fixed=%d  files=%d' % (len(missing), len(fixes), changed))
    if manual:
        print('MANUAL NEEDED (%d):' % len(manual))
        for m in manual:
            print('   ', m)


if __name__ == '__main__':
    main()
