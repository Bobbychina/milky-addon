p=r"E:\Files\milky-addon-26.1.2\src\main\java\com\milky\hunt\modules\PullUp.java"
t=open(p,encoding="utf-8").read()
old='Minecraft.class.getDeclaredField("itemUseCooldown");'
new='Minecraft.class.getDeclaredField("rightClickDelay");   // Yarn itemUseCooldown -> 官方 rightClickDelay'
assert old in t
open(p,"w",encoding="utf-8",newline="\n").write(t.replace(old,new))
print("OK PullUp reflection field updated")
