#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mixin 注入目标/影子成员的 Yarn -> 官方名修（javap 核对过）"""
import os

PROJ = r'E:\Files\milky-addon-26.1.2'
MX = os.path.join(PROJ, 'src', 'main', 'java', 'com', 'milky', 'hunt', 'mixin')
out = []


def patch(fn, pairs):
    path = os.path.join(MX, fn)
    t = open(path, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            out.append('MISS %s :: %s' % (fn, old[:60]))
            continue
        t = t.replace(old, new)
        out.append('OK   %s :: %s' % (fn, old[:60]))
    open(path, 'w', encoding='utf-8', newline='\n').write(t)


patch('LivingEntityMixin.java', [
    ('private int jumpingCooldown;', 'private int noJumpDelay;'),                     # Yarn jumpingCooldown
    ('this.jumpingCooldown = 0;', 'this.noJumpDelay = 0;'),
    ('Lnet/minecraft/world/entity/LivingEntity;tickMovement()V',
     'Lnet/minecraft/world/entity/LivingEntity;aiStep()V'),                            # Yarn tickMovement
    ('Lnet/minecraft/world/entity/LivingEntity;isGliding()Z',
     'Lnet/minecraft/world/entity/LivingEntity;isFallFlying()Z'),                      # Yarn isGliding
    ('private void tickMovement(CallbackInfo ci)', 'private void aiStep(CallbackInfo ci)'),
    ('private void isGliding(CallbackInfoReturnable<Boolean> cir)',
     'private void isFallFlying(CallbackInfoReturnable<Boolean> cir)'),
])

patch('EntityMixin.java', [
    ('method = "pushAwayFrom"',
     'method = "Lnet/minecraft/world/entity/Entity;push(Lnet/minecraft/world/entity/Entity;)V"'),
    ('private void pushAwayFrom(Entity entity, CallbackInfo ci)',
     'private void push(Entity entity, CallbackInfo ci)'),
])

patch('KeyBindingMixin.java', [
    ('private String translationKey;', 'private String name;'),                       # Yarn translationKey
    ('translationKey.equals(', 'name.equals('),
    ('method = "isPressed"', 'method = "isDown"'),                                    # Yarn isPressed
    ('public void isPressed(CallbackInfoReturnable<Boolean> cir)',
     'public void isDown(CallbackInfoReturnable<Boolean> cir)'),
])

patch('ScreenInitMixin.java', [
    ('T addDrawableChild(T drawable);', 'T addRenderableWidget(T drawable);'),         # Yarn addDrawableChild
    ('this.addDrawableChild(', 'this.addRenderableWidget('),
])

print('\n'.join(out))
