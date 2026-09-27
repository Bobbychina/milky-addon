import os
p=r"E:\Files\milky-addon-26.1.2\src\main\java\com\milky\hunt\mixin\ScreenInitMixin.java"
t=open(p,encoding="utf-8").read()
old='@Inject(method = "init(Lnet/minecraft/client/Minecraft;II)V", at = @At("TAIL"))\n    private void eventlog$addOpenFolderButton(Minecraft client, int w, int h, CallbackInfo ci) {'
new='// 26.1.2: Screen.init(Minecraft,II) 已重构为 final init(int,int)\n    @Inject(method = "init(II)V", at = @At("TAIL"))\n    private void eventlog$addOpenFolderButton(int w, int h, CallbackInfo ci) {'
assert old in t, "pattern not found"
open(p,"w",encoding="utf-8",newline="\n").write(t.replace(old,new))
print("OK ScreenInitMixin target -> init(II)V")
