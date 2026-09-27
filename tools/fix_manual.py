#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人工规则修复：把 javap 核对过的 26.1.2 API 变更一次性打到源码上"""
import os
import re
import glob

PROJ = r'E:\Files\milky-addon-26.1.2'
SRC = os.path.join(PROJ, 'src')
LOG = os.path.join(PROJ, 'build', 'javac.log')

RULES = [
    # 玩家背包（Inventory）
    (r'\.getInventory\(\)\.selected\s*=\s*([^;]+);', r'.getInventory().setSelectedSlot(\1);'),
    (r'\.getInventory\(\)\.selected(?!\s*=)', r'.getInventory().getSelectedSlot()'),
    (r'\.getInventory\(\)\.items\b', r'.getInventory().getNonEquipmentItems()'),
    (r'\.getInventory\(\)\.armor\.get\((\d+)\)', r'.getInventory().getItem(36 + \1)'),
    # 静态工厂/工具改名
    (r'\.ofCenter\(', r'.atCenterOf('),
    (r'\bIdentifier\.of\(([^,()]+),\s*([^()]+?)\)', r'Identifier.fromNamespaceAndPath(\1, \2)'),
    (r'\bIdentifier\.of\(', r'Identifier.parse('),
    (r'\bComponent\.of\(', r'Component.literal('),
    (r'\bUtil\.getOperatingSystem\(\)', r'Util.getPlatform()'),
    # 距离/范围比较
    (r'\.getSquaredDistance\(', r'.distSqr('),
    (r'\.isWithinDistance\(', r'.closerThan('),
    (r'\.squaredDistanceTo\(', r'.distanceToSqr('),
    # 注册键 / 音效
    (r'\.dimension\(\)\.location\(\)', r'.dimension().identifier()'),
    (r'\.unwrapKey\(\)\.get\(\)\.location\(\)', r'.unwrapKey().get().identifier()'),
    (r'\bkey\.get\(\)\.location\(\)', r'key.get().identifier()'),
    (r'\.getLocation\(\)', r'.getIdentifier()'),
    # 实体遍历（Level.getEntities 变 protected）
    (r'mc\.level\.getEntities\(\)', r'mc.level.entitiesForRendering()'),
    # 杂项
    (r'\bHeightmap\.Type\.', r'Heightmap.Types.'),
    (r'\(IVec3d\)', r'(IVec3)'),
    (r'\.expand\((?=[\d.])', r'.inflate('),
    (r'\.dimensions\(', r'.bounds('),
    (r'handleInventoryMouseClick\(', r'handleContainerInput('),
    (r'ServerboundPlayerCommandPacket\.Mode\b', r'ServerboundPlayerCommandPacket.Action'),
    # ChunkPos 字段私有化
    (r'pos\.x \* 16 \+ x', r'pos.getMinBlockX() + x'),
    (r'pos\.z \* 16 \+ z', r'pos.getMinBlockZ() + z'),
]


def apply_rules():
    n_files, n_hits = 0, 0
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        o = t
        for pat, rep in RULES:
            t, k = re.subn(pat, rep, t)
            n_hits += k
        if t != o:
            open(path, 'w', encoding='utf-8', newline='\n').write(t)
            n_files += 1
    return n_files, n_hits


def fix_multiply():
    """Vec3.multiply(double) -> scale(double)：按报错行定位"""
    if not os.path.exists(LOG):
        return 0
    text = open(LOG, encoding='utf-8', errors='replace').read()
    sites = re.findall(r'^([A-Z]:\\[^\n]*?):(\d+): error: incompatible types: double cannot be converted to Vec3',
                       text, flags=re.M)
    n = 0
    for f, ln in sites:
        lines = open(f, encoding='utf-8').read().split('\n')
        i = int(ln) - 1
        if 0 <= i < len(lines) and '.multiply(' in lines[i]:
            lines[i] = lines[i].replace('.multiply(', '.scale(', 1)
            open(f, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
            n += 1
    return n


if __name__ == '__main__':
    print('rules: files=%d hits=%d ; multiply->scale=%d' % (apply_rules() + (fix_multiply(),)) if False
          else 'rules: %s ; multiply->scale=%d' % (apply_rules(), fix_multiply()))
