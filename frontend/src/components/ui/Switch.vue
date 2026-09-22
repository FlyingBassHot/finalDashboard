<script setup lang="ts">
import { computed } from 'vue'
import { SwitchRoot, SwitchThumb } from 'radix-vue'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    label?: string
    description?: string
    /** 是否使用带边框的卡片式外观 */
    boxed?: boolean
  }>(),
  { modelValue: false, label: '', description: '', boxed: true },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const wrapperClass = computed(() =>
  props.boxed
    ? 'flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-white/5 bg-card/50 px-4 py-3 transition-colors hover:border-white/10'
    : 'flex cursor-pointer items-center justify-between gap-3',
)
</script>

<template>
  <label :class="wrapperClass">
    <span class="min-w-0">
      <span v-if="label" class="block text-sm text-text-primary">{{ label }}</span>
      <span v-if="description" class="block text-xs text-muted-foreground">{{ description }}</span>
    </span>

    <SwitchRoot
      :model-value="modelValue"
      class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border border-white/10 transition-colors data-[state=checked]:bg-cyan-500/80 data-[state=unchecked]:bg-muted"
      @update:model-value="emit('update:modelValue', $event)"
    >
      <SwitchThumb
        class="pointer-events-none block size-5 rounded-full bg-white shadow-md transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0"
      />
    </SwitchRoot>
  </label>
</template>
