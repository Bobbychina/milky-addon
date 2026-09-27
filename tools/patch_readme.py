#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""README 首段更新为 26.1.2 移植版说明；.gitignore 补 __pycache__"""
import os

P = r'E:\Files\milky-addon-26.1.2'
gi = os.path.join(P, '.gitignore')
t = open(gi, encoding='utf-8').read()
if '__pycache__/' not in t:
    open(gi, 'w', encoding='utf-8', newline='\n').write('__pycache__/\n' + t)
    print('.gitignore += __pycache__/')

r = os.path.join(P, 'README.md')
t = open(r, encoding='utf-8').read()
old = '# Milky Mod\nMeteor Addon For minecraft 1.21.4\n'
new = ('# Milky Mod\n'
       'Meteor Addon For Minecraft 26.1.2\n\n'
       '> **本分支是 26.1.2 移植版（fork）**：构建链升到 Loom 1.17 / Gradle 9.6.1 / JDK 25，'
       '源码从 Yarn 名整体迁移到 26.1 起的官方未混淆名，并修完 Meteor API 漂移（含 4 个 mixin 与 2 处反射）。\n'
       '> 迁移明细、API 对照表与复现命令见 [`docs/PORT-NOTES.md`](docs/PORT-NOTES.md)。\n')
if old in t:
    open(r, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))
    print('README 首段已更新')
else:
    print('README 首段未匹配（可能已改过）')
