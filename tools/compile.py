#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""javac 编译驱动：classpath 直接复用 MAIN 端启动脚本里的真实 -cp + 本地 libs。
   输出 build/javac.log（英文错误），并打印错误数。"""
import os
import re
import sys
import glob
import subprocess

PROJ = r'E:\Files\milky-addon-26.1.2'
BAT = r'D:\mc\PCL\LatestLaunch.bat'


def find_jdk():
    for d in os.listdir(os.path.join(PROJ, 'tools')):
        if d.startswith('jdk-25'):
            return os.path.join(PROJ, 'tools', d)
    raise SystemExit('jdk-25 not found')


def classpath():
    cp = []
    if os.path.exists(BAT):
        raw = open(BAT, encoding='utf-8', errors='replace').read()
        m = re.search(r'-cp\s+"([^"]+)"', raw)
        if m:
            cp += [p for p in m.group(1).split(';') if p.lower().endswith('.jar')]
        del raw                                        # 绝不落盘/回显启动脚本内容
    cp += sorted(glob.glob(os.path.join(PROJ, 'libs', '*.jar')))
    return cp


def main():
    jdk = find_jdk()
    cp = classpath()
    srcs = sorted(glob.glob(os.path.join(PROJ, 'src', '**', '*.java'), recursive=True))
    out = os.path.join(PROJ, 'build', 'classes')
    os.makedirs(out, exist_ok=True)
    argfile = os.path.join(PROJ, 'build', 'javac.args')
    args = ['-encoding', 'UTF-8', '-proc:none', '-nowarn', '-Xmaxerrs', '10000',
            '-d', out, '-cp', ';'.join(cp)] + srcs
    with open(argfile, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(args) + '\n')
    log = os.path.join(PROJ, 'build', 'javac.log')
    with open(log, 'w', encoding='utf-8') as lf:
        r = subprocess.run([os.path.join(jdk, 'bin', 'javac.exe'),
                            '-J-Duser.language=en', '-J-Duser.country=US', '@' + argfile],
                           stdout=lf, stderr=subprocess.STDOUT)
    text = open(log, encoding='utf-8', errors='replace').read()
    errs = text.count(': error:')
    print('exit=%d errors=%d sources=%d cpJars=%d' % (r.returncode, errs, len(srcs), len(cp)))
    if errs == 0 and r.returncode == 0:
        print('BUILD OK ->', out)
    else:
        print(text[:1500])


if __name__ == '__main__':
    main()
