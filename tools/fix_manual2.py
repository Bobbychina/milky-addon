#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二批人工规则（javap 核对过）"""
import os
import re
import glob

PROJ = r'E:\Files\milky-addon-26.1.2'
SRC = os.path.join(PROJ, 'src')

RULES2 = [
    # 护甲槽：Inventory.getItem(36+i)（36 靴/37 腿/38 胸/39 头）
    (r'\.getInventory\(\)\.getArmor\(([^)]+)\)', r'.getInventory().getItem(36 + \1)'),
    # 朝向访问器改名
    (r'\.getYaw\(\)', '.getYRot()'),
    (r'\.getPitch\(\)', '.getXRot()'),
    (r'\.setYaw\(', '.setYRot('),
    (r'\.setPitch\(', '.setXRot('),
    # AABB / 交互
    (r'\.stretch\(', '.expandTowards('),
    (r'\.interactAt\(', '.interact('),
    # Item.getName() 在 26.1.2 需要 ItemStack 参数
    (r'\bneeded\.getName\(\)', 'new ItemStack(needed).getHoverName()'),
    (r'\b([\w.]+)\.get\(\)\.asItem\(\)\.getName\(\)', r'new ItemStack(\1.get()).getHoverName()'),
    (r'\btargetItem\.get\(\)\.getName\(\)', 'new ItemStack(targetItem.get()).getHoverName()'),
    (r'\b(mainHandItem|offHandItem)\.get\(\)\.getName\(\)', r'new ItemStack(\1.get()).getHoverName()'),
    (r'\bitemEntity\.getItem\(\)\.getItem\(\)\.getName\(\)', 'itemEntity.getItem().getHoverName()'),
    (r'\bblockUnder\.getName\(\)', 'new ItemStack(blockUnder).getHoverName()'),
    # 打开文件夹
    (r'Util\.getPlatform\(\)\.open\(', 'Util.getPlatform().openFile('),
    # GameProfile 改成 record 风格访问器
    (r'\.getGameProfile\(\)\.getName\(\)', '.getGameProfile().name()'),
]


def main():
    files, hits = 0, 0
    for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
        t = open(path, encoding='utf-8').read()
        o = t
        for pat, rep in RULES2:
            t, k = re.subn(pat, rep, t)
            hits += k
        if t != o:
            open(path, 'w', encoding='utf-8', newline='\n').write(t)
            files += 1
    print('rules2: files=%d hits=%d' % (files, hits))


if __name__ == '__main__':
    main()
