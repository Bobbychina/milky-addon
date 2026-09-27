# Milky Mod
Meteor Addon For Minecraft 26.1.2

> **本分支是 26.1.2 移植版（fork）**：构建链升到 Loom 1.17 / Gradle 9.6.1 / JDK 25，源码从 Yarn 名整体迁移到 26.1 起的官方未混淆名，并修完 Meteor API 漂移（含 4 个 mixin 与 2 处反射）。
> 迁移明细、API 对照表与复现命令见 [`docs/PORT-NOTES.md`](docs/PORT-NOTES.md)。

This mod may include copy-pasted code from Meteor, Hybridious, Jeff Mod, Trouser Streak, Zenith Proxy and others.

I would like to extend special thanks to xiaohe66 for sharing the early-stage code of a module similar to PitStop.

### MilkyMod Modules

- AirLanding
  - Biome-aware landing: free-fall, re-equip elytra, perform a landing burn, then air-place a platform.
- AutoGolem
  - Do you want to build a snowman? ♪♪ Maybe an iron one... or even a dark one.
- AutoInvertedY
  - Automatically constructs your favorite, uh... iconic shape — using any block you choose. Ideal for establishing a proudly ridiculous *rocket garden*.
- ChestDeposit
  - Automatically deposits items from your inventory into chests.
- ChestRestock
  - Automatically refill your inventory with chosen item from chests.
- GotoMultiPoints
   - Walks between multiple coordinates using Baritone.
- InHand
  - Fills your mainhand and offhand with chosen items.
- LeftClickBlock
  - Automatically interacts with blocks in range.
- PhantomStatistics
  - Detect phantoms, optionally mark Xaero waypoints, and show Y layer density on HUD.
- PitStop
  - Restock elytras and two other item types from an ender chest.
- PullUp
  - Automatically takes off from the ground and climbs to your target altitude. 
- RightClickBlock
  - Automatically interacts with blocks in range.
- RightClickEntity
  - Automatically interacts with entities in range.
- SpiralFlight
  - Adjusts your yaw to follow an Archimedean spiral path.
- Trade
  - Auto trades with villagers.
- WaypointQueue
  - Adjusts your yaw to sequentially aim at waypoints from XaeroMap.

### MilkyWay Modules

- Magazine
  - Automatically switch parameters of your Meteor modules.
- QuickCommand
  - Send your message/command (with rich placeholders) to gamechat with a single click.
- Timeline
  - Orchestrates your Meteor modules—start and stop modules in a defined order or in parallel.
  - Write a short script to schedule routines and optionally loop them.

### Borrowed Magic

- BoostedBounce
  - Ported from Jeff Mod and adapted for Minecraft 1.21.4 with a reworked soft-collision check and a build-in elytra/gold auto-replace.
- Cruise
  - Ported from Jeff Mod, with Elytra auto-replace added and modules combined.
- EventLog
  - Ported from Meteor and Jeff Mod, with additional triggers (including a Vy test), a more detailed HUD, and screenshot options.
- RotationLock
  - Ported from Meteor, with a stricter angle lock.
- ValuableESP
  - Ported from Trouser Streak.
- WavPlayer
  - Ported from Hybridious. Plays WAV files, with a default dancing Polish 🐮.


### About
This mod isn’t meant to be serious or useful — it’s just 🐮 and friends talking big. (Back on July 30, 🐮 complained about the lack of decent open-source PVP mods for 2b2t.org.) 🐮 has no idea how to code. Realistically, there’s a 99% chance this gets abandoned in three days. But in that glorious 1%, you just might witness 🐮 learn everything from scratch, grinding hard and sprinting full speed toward building a real PVP module. If that sounds fun, stick around — 🐮’s Discord: dandelion_94876.

What’s new (Dec 24): 🐮 is back. The direction of the module is shifting toward automated survival utilities that aim to handle more complex scenarios — at least in theory.

P.S. Long story short, GPT is hard-carrying. XD
