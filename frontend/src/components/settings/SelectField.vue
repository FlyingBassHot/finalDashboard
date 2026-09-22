<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Check, ChevronDown, Loader2 } from 'lucide-vue-next'

export interface SelectOption {
  value: string
  label: string
}

const props = withDefaults(
  defineProps<{
    label?: string
    options: SelectOption[]
    modelValue?: string | null
    placeholder?: string
    loading?: boolean
    disabled?: boolean
  }>(),
  {
    label: '',
    options: () => [],
    modelValue: null,
    placeholder: '请选择',
    loading: false,
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

const selected = computed(
  () => props.options.find((o) => o.value === props.modelValue) ?? null,
)

function toggle() {
  if (props.disabled || props.loading) return
  open.value = !open.value
}

function pick(option: SelectOption) {
  emit('update:modelValue', option.value)
  open.value = false
}

function onDocClick(event: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div ref="rootRef" class="relative">
    <label v-if="label" class="mb-1.5 block text-xs font-medium text-muted-foreground">
      {{ label }}
    </label>

    <button
      type="button"
      class="flex h-11 w-full items-center justify-between gap-2 rounded-xl border border-input bg-card/60 px-3.5 text-left text-sm transition-colors hover:border-ring/40 disabled:cursor-not-allowed disabled:opacity-50"
      :class="open ? 'border-ring/60 ring-2 ring-ring/25' : ''"
      :disabled="disabled || loading"
      @click="toggle"
    >
      <Loader2 v-if="loading" class="size-4 shrink-0 animate-spin text-muted-foreground" />
      <span v-else-if="selected" class="truncate text-foreground">{{ selected.label }}</span>
      <span v-else class="truncate text-muted-foreground/70">{{ placeholder }}</span>
      <ChevronDown
        class="size-4 shrink-0 text-muted-foreground transition-transform duration-200"
        :class="open ? 'rotate-180' : ''"
      />
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="-translate-y-1 opacity-0"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="-translate-y-1 opacity-0"
    >
      <div
        v-if="open"
        class="absolute z-40 mt-1.5 max-h-60 w-full overflow-y-auto rounded-xl border border-border bg-popover/95 p-1.5 shadow-2xl shadow-black/50 backdrop-blur-xl"
      >
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          class="flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition-colors hover:bg-accent"
          :class="option.value === modelValue ? 'bg-accent/70 text-cyan-300' : 'text-foreground/90'"
          @click="pick(option)"
        >
          <span class="truncate">{{ option.label }}</span>
          <Check v-if="option.value === modelValue" class="size-4 shrink-0 text-cyan-400" />
        </button>
        <div v-if="!options.length" class="px-2.5 py-3 text-center text-xs text-muted-foreground">
          暂无选项
        </div>
      </div>
    </Transition>
  </div>
</template>
