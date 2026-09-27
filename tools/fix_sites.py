#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定点补丁：语义性改动（多行/需换 API 用法），每处替换都做命中校验"""
import os
import re

PROJ = r'E:\Files\milky-addon-26.1.2'
SRC = os.path.join(PROJ, 'src')
results = []


def patch(rel, pattern, repl, flags=re.S, expect=1):
    path = os.path.join(SRC, rel)
    t = open(path, encoding='utf-8').read()
    t2, n = re.subn(pattern, repl, t, flags=flags)
    status = 'OK' if n == expect else 'MISS(%d/%d)' % (n, expect)
    results.append('%s %s' % (status, rel))
    if n:
        open(path, 'w', encoding='utf-8', newline='\n').write(t2)
    return n


# 1) Trade: RegistryAccess.getOptional -> lookupOrThrow，Registry.getId -> getKey
patch('main/java/com/milky/hunt/modules/Trade.java',
      r'var optReg = mc\.level\.registryAccess\(\)\.getOptional\(Registries\.ENCHANTMENT\);\s*\n\s*if \(optReg\.isEmpty\(\)\) continue;\s*\n\s*Identifier onBook = optReg\.get\(\)\.getId\(key\.value\(\)\);',
      'var reg = mc.level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);\n                Identifier onBook = reg.getKey(key.value());')

# 2) AirLanding: Level.getTopPosition -> getHeight(int) + 自行拼 BlockPos
patch('main/java/com/milky/hunt/modules/AirLanding.java',
      r'BlockPos surface = mc\.level\.getTopPosition\(\s*\n\s*Heightmap\.Types\.MOTION_BLOCKING_NO_LEAVES,\s*\n\s*new BlockPos\(playerPos\.getX\(\) \+ dx, 0, playerPos\.getZ\(\) \+ dz\)\s*\n\s*\);',
      'int surfaceY = mc.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, playerPos.getX() + dx, playerPos.getZ() + dz);\n'
      '                BlockPos surface = new BlockPos(playerPos.getX() + dx, surfaceY, playerPos.getZ() + dz);')

# 3) EventLog: 截图 API 回调化
patch('main/java/com/milky/hunt/modules/EventLog.java',
      r'try \(NativeImage img = Screenshot\.takeScreenshot\(mc\.getMainRenderTarget\(\)\)\) \{\s*\n\s*img\.writeToFile\(out\);\s*\n\s*\}',
      'final Path outFinal = out;\n'
      '                // 26.1.2: takeScreenshot 改为回调式，NativeImage 由回调提供\n'
      '                Screenshot.takeScreenshot(mc.getMainRenderTarget(), img -> {\n'
      '                    try (img) {\n'
      '                        img.writeToFile(outFinal);\n'
      '                    } catch (Throwable t) {\n'
      '                        Addon.LOG.error("Failed to write screenshot", t);\n'
      '                    }\n'
      '                });')

# 4) EventLog: 断线改用 DisconnectionDetails
patch('main/java/com/milky/hunt/modules/EventLog.java',
      r'new ClientboundDisconnectPacket\(buildDisconnectText\(reason\)\)',
      'new DisconnectionDetails(buildDisconnectText(reason))')
patch('main/java/com/milky/hunt/modules/EventLog.java',
      r'import net\.minecraft\.network\.protocol\.common\.ClientboundDisconnectPacket;\n',
      'import net.minecraft.network.DisconnectionDetails;\n')

# 5) BoostedBounce: 手搓 ContainerClick 包 -> 走官方 gameMode 通道
patch('main/java/com/milky/hunt/modules/BoostedBounce.java',
      r'mc\.player\.connection\.sendPacket\(new ServerboundContainerClickPacket\(.*?\)\);\s*\n\s*\n',
      '// 26.1.2: 包结构大改（short/byte/HashedStack），改走官方容器输入通道\n'
      '        mc.gameMode.handleContainerInput(syncId, 6, buttonNum, ContainerInput.SWAP, mc.player);\n\n')

# 6) CommandExample: Meteor Command.build 换成 ClientSuggestionProvider
patch('main/java/com/milky/hunt/commands/CommandExample.java',
      r'import net\.minecraft\.commands\.SharedSuggestionProvider;',
      'import net.minecraft.client.multiplayer.ClientSuggestionProvider;')
patch('main/java/com/milky/hunt/commands/CommandExample.java',
      r'LiteralArgumentBuilder<SharedSuggestionProvider>',
      'LiteralArgumentBuilder<ClientSuggestionProvider>')

# 7) WaypointQueue: WindowScreen 没有 close()，直接关屏
patch('main/java/com/milky/hunt/modules/WaypointQueue.java',
      r'(onPick\.accept\(new BlockPos\(w\.getX\(\), w\.getY\(\), w\.getZ\(\)\)\);\s*\n\s*)close\(\);',
      r'\1mc.setScreen(null);')

# 8) access widener: named -> official，方法改名
aw = os.path.join(SRC, 'main/resources/milkymod.accesswidener')
open(aw, 'w', encoding='utf-8', newline='\n').write(
    'accessWidener v2 official\n'
    'accessible method net/minecraft/client/multiplayer/ClientLevel getBlockStatePredictionHandler '
    '()Lnet/minecraft/client/multiplayer/prediction/BlockStatePredictionHandler;\n')
results.append('OK main/resources/milkymod.accesswidener')

# 9) fabric.mod.json: 版本约束（26.1 官方名 + Java 25）
patch('main/resources/fabric.mod.json',
      r'"java": ">=21",\s*\n\s*"minecraft": ">=\$\{mc_version\}"',
      '"java": ">=25",\n    "minecraft": "~26.1"')

print('\n'.join(results))
