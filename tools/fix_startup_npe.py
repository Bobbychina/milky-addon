#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机测试抓到的启动崩溃修复：
   Minecraft 构造期（setScreen -> KeyMapping.releaseAll -> isDown）就会走到我们的 mixin，
   而那时 Meteor 的 Modules 单例还没建好 -> Modules.get() 为 null -> NPE。
   三处 mixin 改为懒加载 + 空守卫。"""
import os

PROJ = r'E:\Files\milky-addon-26.1.2'
MX = os.path.join(PROJ, 'src', 'main', 'java', 'com', 'milky', 'hunt', 'mixin')
out = []


def rw(fn, pairs):
    p = os.path.join(MX, fn)
    t = open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            out.append('MISS %s :: %s' % (fn, old[:70].replace('\n', '\\n')))
            continue
        t = t.replace(old, new)
        out.append('OK   %s' % fn)
    open(p, 'w', encoding='utf-8', newline='\n').write(t)


# 1) KeyBindingMixin：加空守卫
rw('KeyBindingMixin.java', [(
    """        // setting it beforehand caused a crash because meteor wasnt loaded yet
        efly = efly == null ? Modules.get().get(BoostedBounce.class) : efly;
        if (efly != null && efly.isActive() && efly.enabled() && name.equals("key.forward"))""",
    """        // 启动早期（Minecraft 构造 → releaseAll → isDown）Meteor 尚未初始化，Modules.get() 会是 null
        if (efly == null) {
            var modules = Modules.get();
            if (modules == null) return;
            efly = modules.get(BoostedBounce.class);
            if (efly == null) return;
        }
        if (efly.isActive() && efly.enabled() && name.equals("key.forward"))""")])

# 2) EntityMixin / LivingEntityMixin：字段初始化改懒加载
LAZY = """    @Unique
    private BoostedBounce efly = null;

    /** 启动早期 Modules.get() 可能为 null，必须懒取 */
    private BoostedBounce efly() {
        if (efly == null) {
            var mods = Modules.get();
            if (mods != null) efly = mods.get(BoostedBounce.class);
        }
        return efly;
    }
"""
for fn in ('EntityMixin.java', 'LivingEntityMixin.java'):
    rw(fn, [
        ('    BoostedBounce efly = Modules.get().get(BoostedBounce.class);', LAZY),
        ('efly != null && efly.enabled()', 'efly() != null && efly().enabled()'),
    ])
    # 补 @Unique 的 import
    p = os.path.join(MX, fn)
    t = open(p, encoding='utf-8').read()
    if 'import org.spongepowered.asm.mixin.Unique;' not in t:
        t = t.replace('import org.spongepowered.asm.mixin.Shadow;',
                      'import org.spongepowered.asm.mixin.Shadow;\nimport org.spongepowered.asm.mixin.Unique;')
        open(p, 'w', encoding='utf-8', newline='\n').write(t)
        out.append('OK   %s (+Unique import)' % fn)

print('\n'.join(out))
