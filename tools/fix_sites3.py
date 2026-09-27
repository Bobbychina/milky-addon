#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批定点补丁 + 自动补 import"""
import os
import re
import glob

PROJ = r'E:\Files\milky-addon-26.1.2'
SRC = os.path.join(PROJ, 'src', 'main', 'java')
out = []


def patch(rel, pattern, repl, flags=re.S):
    path = os.path.join(SRC, rel)
    t = open(path, encoding='utf-8').read()
    t2, n = re.subn(pattern, repl, t, flags=flags)
    out.append('%s %s' % ('OK ' if n else 'MISS', rel))
    if n:
        open(path, 'w', encoding='utf-8', newline='\n').write(t2)
    return n


M = 'com/milky/hunt/modules/'
# 1) 容器点击包 -> 官方容器输入通道
patch(M + 'Trade.java',
      r'mc\.getConnection\(\)\.sendPacket\(new ServerboundContainerClickPacket\(.*?\)\);',
      'mc.gameMode.handleContainerInput(handler.containerId, resultSlot, 0, ContainerInput.QUICK_MOVE, mc.player);')
patch(M + 'BoostedBounce.java',
      r'mc\.player\.connection\.sendPacket\(new ServerboundContainerClickPacket\(.*?\)\);',
      'mc.gameMode.handleContainerInput(syncId, 6, buttonNum, ContainerInput.SWAP, mc.player);')
# 2) 实体交互：26.1.2 只剩 4 参重载
patch(M + 'RightClickEntity.java',
      r'mc\.gameMode\.interact\(mc\.player, target, hit, InteractionHand\.MAIN_HAND\);\s*\n\s*mc\.gameMode\.interact\(mc\.player, target, InteractionHand\.MAIN_HAND\);',
      'mc.gameMode.interact(mc.player, target, hit, InteractionHand.MAIN_HAND);   // 26.1.2 仅剩 4 参重载')
# 3) 其它零散
patch(M + 'RightClickBlock.java', r'pos\.offset\(face\)', 'pos.relative(face)')
patch(M + 'LeftClickBlock.java', r'state\.get\(ageProp\)', 'state.getValue(ageProp)')
patch(M + 'Magazine.java', r'BuiltInRegistries\.ITEM\.get\(id\)', 'BuiltInRegistries.ITEM.getValue(id)')
patch(M + 'Magazine.java', r'BuiltInRegistries\.BLOCK\.get\(id\)', 'BuiltInRegistries.BLOCK.getValue(id)')
patch(M + 'WaypointQueue.java', r'mc\.setScreen\(null\);', 'MeteorClient.mc.setScreen(null);')

# 4) 全局：ItemStack.isOf -> is；注册表 getId -> getKey
for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
    t = open(path, encoding='utf-8').read()
    o = t
    t = t.replace('.isOf(', '.is(')
    t = t.replace('BuiltInRegistries.ITEM.getId(', 'BuiltInRegistries.ITEM.getKey(')
    t = t.replace('BuiltInRegistries.ENTITY_TYPE.getId(', 'BuiltInRegistries.ENTITY_TYPE.getKey(')
    t = t.replace('BuiltInRegistries.BLOCK.getId(', 'BuiltInRegistries.BLOCK.getKey(')
    if t != o:
        open(path, 'w', encoding='utf-8', newline='\n').write(t)
        out.append('OK  global-fix %s' % os.path.basename(path))

# 5) 缺 import 的自动补：ItemStack / MeteorClient
need = {
    'net.minecraft.world.item.ItemStack': 'new ItemStack(',
    'meteordevelopment.meteorclient.MeteorClient': 'MeteorClient.mc',
}
for path in glob.glob(os.path.join(SRC, '**', '*.java'), recursive=True):
    t = open(path, encoding='utf-8').read()
    shorts = {k: k.rsplit('.', 1)[-1] for k in need}
    for fqn, probe in need.items():
        short = shorts[fqn]
        if probe in t and ('import %s;' % fqn) not in t and not re.search(r'\bclass %s\b' % short, t):
            # 插到第一个 import 之前
            m = re.search(r'^import ', t, re.M)
            if m:
                t = t[:m.start()] + 'import %s;\n' % fqn + t[m.start():]
                out.append('OK  add-import %s -> %s' % (short, os.path.basename(path)))
            else:
                t = t.replace('\n\n', '\n\nimport %s;\n' % fqn, 1)
                out.append('OK  add-import(no-imports) %s -> %s' % (short, os.path.basename(path)))
    open(path, 'w', encoding='utf-8', newline='\n').write(t)

print('\n'.join(out))
