package com.milky.hunt.mixin;

import meteordevelopment.meteorclient.MeteorClient;
import com.milky.hunt.modules.BoostedBounce;
import meteordevelopment.meteorclient.systems.modules.Modules;
import net.minecraft.client.KeyMapping;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import static meteordevelopment.meteorclient.MeteorClient.mc;

@Mixin(KeyMapping.class)
public abstract class KeyBindingMixin {

    @Final
    @Shadow
    private String name;

    @Unique
    BoostedBounce efly = null;

    @Inject(at = @At("RETURN"), method = "isDown", cancellable = true)
    public void isDown(CallbackInfoReturnable<Boolean> cir)
    {
        // 启动早期（Minecraft 构造 → releaseAll → isDown）Meteor 尚未初始化，Modules.get() 会是 null
        if (efly == null) {
            var modules = Modules.get();
            if (modules == null) return;
            efly = modules.get(BoostedBounce.class);
            if (efly == null) return;
        }
        if (efly.isActive() && efly.enabled() && name.equals("key.forward"))
        {
            cir.setReturnValue(true);
        }
    }
}
