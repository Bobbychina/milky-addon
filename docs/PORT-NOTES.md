# milky-addon 移植记录：1.21.4 (Yarn) → Minecraft 26.1.2（官方未混淆名）

## 结论
`gradlew build` 通过，产物 `build/libs/milkymod-0.0.6-26.1.2.jar`（5.76 MB，63 个 class）。
13 项 mixin 注入目标、4 处反射字段、access widener 全部按 26.1.2 真实 jar 核验通过。

## 构建环境
| 项 | 旧 | 新 |
|---|---|---|
| Minecraft | 1.21.4 | 26.1.2（官方未混淆，无 mappings 行） |
| 映射 | Yarn 1.21.4+build.7 | 无（Mojang 官方名） |
| Gradle | 8.10.2 | 9.6.1（腾讯镜像，官方源在国内 0 字节） |
| Loom | `fabric-loom` 1.8-SNAPSHOT | `net.fabricmc.fabric-loom` 1.17-SNAPSHOT |
| JDK | 21 | 25（Temurin 25.0.4.1，随包 `tools/`） |
| fabric-loader | 0.16.9 | 0.19.3 |
| Meteor | `meteordevelopment:meteor-client:1.21.4-SNAPSHOT` | `:26.1.2-SNAPSHOT` |
| Baritone | `:1.21.4-SNAPSHOT` | `meteordevelopment:baritone:26.1-SNAPSHOT` |
| Xaero | 1.21.4 版三件套 | minimap `fabric-26.1.2-26.5.0` / world-map `fabric-26.1.2-1.46.0` / XaeroPlus `2.36.2+fabric-26.1.2` |
| 依赖写法 | `modImplementation` + remap | `implementation` / `compileOnly`（26.1 起不再 remap） |
| Java 兼容 | `java >=21` | `java >=25`，`minecraft ~26.1` |

`libs/` 里放了 MAIN 端运行时同名 jar（meteor/baritone/xaero/orbit），仅用于 javac 快速编译校验。

## 迁移管线（tools/）
1. `migrate_mappings.py` — 用 obf 名做桥把 Yarn(1.21.4) 与 Mojang 官方映射对齐，导出 `docs/member-map.json`（按类的成员映射，**描述符精确配对**，避免同名串号），并重写源码里的 `net.minecraft.*` 类名/简单名/mixin 描述符。
2. `compile.py` — 直接复用 MAIN 启动脚本的真实 `-cp` + 本地 jar 跑 javac，拿英文错误清单（避开 libraries 里旧版 Forge/NeoForge 的 MC jar 污染）。
3. `port_loop.py` + `fix_classes.py` + `fix_symbols.py` — 编译→报错→按 (类,符号) 精确改名，自动把 879 个错误降到 181。
4. `fix_manual.py` / `fix_manual2.py` / `fix_sites.py` / `fix_sites3.py` — javap 逐个核对后的人工规则批（181 → 2）。
5. `fix_mixins.py` / `fix_screen_mixin.py` / `fix_pullup.py` — mixin 注入目标、影子成员、反射字段收尾。
6. `classhier.py` — 从 jar 解析继承链，用于查继承来的成员（`getPos`/`getStack` 这类）。
7. `verify_mixins.py` — 逐条核验 mixin 目标与影子成员是否真实存在。

## 关键 API 变更（本次实际踩到的）
| 1.21.4 (Yarn/旧官方) | 26.1.2 |
|---|---|
| `MinecraftClient` / `mc.world` / `mc.interactionManager` | `Minecraft` / `mc.level` / `mc.gameMode` |
| `Vec3d.ofCenter(pos)` / `vec.multiply(d)` | `Vec3.atCenterOf(pos)` / `vec.scale(d)` |
| `Box` / `getPos()` / `setYaw()` | `AABB` / `position()` / `setYRot()` |
| `ItemStack.isOf()` / `getName()` | `is()` / `getHoverName()`（`Item.getName()` 现在要 ItemStack 参数） |
| `Identifier.of(...)` | `Identifier.parse(...)` / `fromNamespaceAndPath(...)` |
| `ResourceLocation` / `ResourceKey.getValue()` | `Identifier` / `identifier()` |
| `Inventory.selected` / `armor` / `items` | `getSelectedSlot()/setSelectedSlot()` / `getItem(36+i)`（36靴37腿38胸39头） / `getNonEquipmentItems()` |
| `Registry.getId()` | `getKey()`；`RegistryAccess.getOptional()` → `lookupOrThrow()`；`Registry.getItem(id)` → `getValue(id)` |
| `Level.getEntities()`（变 protected） | `ClientLevel.entitiesForRendering()` |
| `Level.getTopPosition(Heightmap.Type, pos)` | `Level.getHeight(Heightmap.Types, x, z)` + 自己拼 `BlockPos` |
| `clickSlot(...)` / `ServerboundContainerClickPacket(7 参旧式)` | `gameMode.handleContainerInput(id, slot, button, ContainerInput.X, player)` |
| `interactAt(...)` / `ScreenshotRecorder.takeScreenshot()` | `interact(4 参)` / `Screenshot.takeScreenshot(rt, Consumer<NativeImage>)` 回调式 |
| `ClientboundDisconnectPacket` 断线 | `net.minecraft.network.DisconnectionDetails` |
| `Util.getOperatingSystem().open()` / `Heightmap.Type` | `Util.getPlatform().openFile()` / `Heightmap.Types` |
| `getBlockStatePredictionHandler()` 包私有 | access widener 换成 `v2 official` 开放 |
| Meteor `mixininterface.IVec3d` | `IVec3` |
| mixin: `tickMovement` / `isGliding` / `addDrawableChild` / `pushAwayFrom` / `isPressed` / `translationKey` / `jumpingCooldown` | `aiStep` / `isFallFlying` / `addRenderableWidget` / `push` / `isDown` / `name` / `noJumpDelay` |
| mixin: `Screen.init(Minecraft,II)V` | `Screen.init(II)V`（26.1.2 重构） |
| 反射 `Minecraft.itemUseCooldown` | `Minecraft.rightClickDelay` |

## 已验证 / 未验证
- ✅ `gradlew build` 通过（Loom 1.17.21 / JDK 25），`validateAccessWidener` 通过
- ✅ fabric.mod.json 展开正确（`0.0.6-26.1.2` / `~26.1` / `java >=25`），jar 内含 mixins.json + accesswidener + 素材
- ✅ 13 项 mixin 目标 + 4 处反射字段在 26.1.2 真实 jar 中逐一核验存在
- ⚠️ **未做游戏内实机验证**（本次只做到静态核验 + 构建通过）：建议装进 `D:\mc\.minecraft\versions\MAIN\mods` 启动一次，确认 Meteor GUI 里出现 MilkyMod/MilkyWay 两个分类、模块可开关、无 mixin 报错
- ⚠️ `Magazine` 依赖 Meteor 内部字段反射（`Module.settings`/`Settings.groups`/`Setting.name`/`IntSetting.min|max`）—— 26.1.2-41 里这些字段都还在，但 Meteor 改内部结构时会静默失效
- ⚠️ Xaero 系闭源，`WaypointQueue`/`PhantomStatistics` 只在编译期对齐了 API，行为需实机确认

## 复现
```powershell
$env:JAVA_HOME = "E:\Files\milky-addon-26.1.2\tools\jdk-25.0.4.1+1"
cd E:\Files\milky-addon-26.1.2
.\gradlew.bat build          # 产物在 build\libs\milkymod-0.0.6-26.1.2.jar
```

## 实机冒烟测试（2026-09-28 00:57）
- 装入 `D:\mc\.minecraft\versions\MAIN\mods\milkymod-0.0.6-26.1.2.jar` 启动 MC 26.1.2（Fabric 0.19.3 / Meteor 26.1.2-41）
- **第一次启动就崩溃**：`Minecraft.<init>` → `setScreen` → `KeyMapping.releaseAll` → `isDown` 走到我们的 mixin，此时 `Modules.get()` 仍为 null → NPE。
  - 修复：`KeyBindingMixin` 加空守卫；`EntityMixin`/`LivingEntityMixin` 的 `efly` 字段改懒加载 `efly()`（`tools/fix_startup_npe.py`）
- 第二次启动通过：日志出现 `milkymod 0.0.6-26.1.2` 与 `Initializing Milky Mod`，4 个 mixin 全部应用且**零 mixin 报错**，无新崩溃报告，游戏正常停在主菜单
- 证据：`E:\Files\archive\sessions\2026-09\shots\mc-meteor-gui.png`、`logs\latest.log`
- 备注：`LatestLaunch.bat` 里的 accessToken 已失效（401），实机联机测试请用 PCL 正常启动
