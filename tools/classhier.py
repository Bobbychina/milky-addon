#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 MAIN.jar 解析每个类的父类/接口链（用于查继承来的成员）"""
import os
import json
import zipfile
import struct

PROJ = r'E:\Files\milky-addon-26.1.2'
MCJAR = r'D:\mc\.minecraft\versions\MAIN\MAIN.jar'


def parse_class(data):
    """返回 (this, super, [interfaces]) 全限定名，失败返回 None"""
    try:
        if data[:4] != b'\xca\xfe\xba\xbe':
            return None
        idx = 8
        cp_count = struct.unpack('>H', data[idx:idx + 2])[0]
        idx += 2
        cp = {}
        i = 1
        while i < cp_count:
            tag = data[idx]
            idx += 1
            if tag == 1:
                ln = struct.unpack('>H', data[idx:idx + 2])[0]
                idx += 2
                cp[i] = data[idx:idx + ln].decode('utf-8', 'replace')
                idx += ln
            elif tag in (7, 8, 16, 19, 20):
                cp[i] = struct.unpack('>H', data[idx:idx + 2])[0]
                idx += 2
            elif tag in (15,):
                idx += 3
            elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
                idx += 4
            elif tag in (5, 6):
                idx += 8
                i += 1
            else:
                return None
            i += 1
        idx += 2                                   # access_flags
        this_i = struct.unpack('>H', data[idx:idx + 2])[0]; idx += 2
        super_i = struct.unpack('>H', data[idx:idx + 2])[0]; idx += 2
        n_if = struct.unpack('>H', data[idx:idx + 2])[0]; idx += 2
        ifs = []
        for _ in range(n_if):
            ifs.append(struct.unpack('>H', data[idx:idx + 2])[0]); idx += 2

        def nm(ci):
            if ci == 0:
                return None
            v = cp.get(ci)
            if isinstance(v, int):          # Class 项指向常量池里的 Utf8 下标，要再解一层
                v = cp.get(v)
            return v.replace('/', '.') if isinstance(v, str) else None
        return nm(this_i), nm(super_i), [nm(x) for x in ifs]
    except Exception:
        return None


def main():
    z = zipfile.ZipFile(MCJAR)
    hier = {}
    for n in z.namelist():
        if not n.endswith('.class') or '$' in n:
            continue
        p = parse_class(z.read(n))
        if p and p[0]:
            hier[p[0]] = [x for x in ([p[1]] + p[2]) if x]
    z.close()
    out = os.path.join(PROJ, 'docs', 'hierarchy.json')
    json.dump(hier, open(out, 'w', encoding='utf-8'))
    print('classes=%d -> %s' % (len(hier), out))


if __name__ == '__main__':
    main()
