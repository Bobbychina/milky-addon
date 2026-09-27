#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""移植主循环：compile -> fix_classes -> fix_symbols -> 再 compile，直到无错或不再有改动"""
import os
import re
import subprocess
import sys

PROJ = r'E:\Files\milky-addon-26.1.2'
PY = r'D:\python313\python.exe'
LOG = os.path.join(PROJ, 'build', 'javac.log')


def run(script, capture=True):
    r = subprocess.run([PY, os.path.join(PROJ, 'tools', script)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout or ''


def err_count():
    if not os.path.exists(LOG):
        return -1
    return open(LOG, encoding='utf-8', errors='replace').read().count(': error:')


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    for i in range(rounds):
        out = run('compile.py')
        n = err_count()
        print('--- round %d: errors=%d' % (i + 1, n))
        if n == 0:
            print('BUILD OK')
            return
        a = run('fix_classes.py')
        b = run('fix_symbols.py')
        fixed = re.search(r'member renames applied=(\d+)', b)
        n_fix = int(fixed.group(1)) if fixed else 0
        cfix = re.search(r'class-errors=(\d+)\s+fixed=(\d+)', a)
        print('    class-fix: %s' % (cfix.group(0) if cfix else 'n/a'))
        print('    member-fix: %d' % n_fix)
        if n_fix == 0 and (not cfix or cfix.group(2) == '0'):
            print('    无更多可自动修复，停止')
            break


if __name__ == '__main__':
    main()
