<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp, Globe, Plus, Trash2 } from 'lucide-vue-next'
import { useClock } from '@/composables/useClock'
import { useClockPrefs } from '@/composables/useClockPrefs'
import {
  CITY_PRESETS,
  buildClockTime,
  cityLabel,
  utcOffsetText,
} from '@/lib/clock'
import SelectField from '@/components/settings/SelectField.vue'

const { nowMs } = useClock()
const { prefs, addCity, removeCity, moveCity } = useClockPrefs()

const rows = computed(() =>
  prefs.cities.map((tz) => {
    const date = new Date(nowMs.value)
    return {
      tz,
      label: cityLabel(tz),
      time: buildClockTime(date, tz),
      offset: utcOffsetText(date, tz),
    }
  }),
)

/** 可添加的城市（排除已存在的） */
const availableOptions = computed(() =>
  CITY_PRESETS.filter((city) => !prefs.cities.includes(city.tz)).map((city) => ({
    value: city.tz,
    label: `${city.name} · ${city.tz}`,
  })),
)

const pendingCity = ref<string | null>(null)

function onPick(timezone: string) {
  addCity(timezone)
  pendingCity.value = null
}
</script>

<template>
  <div class="glass-card flex flex-col p-5 sm:p-6">
    <div class="mb-5 flex items-center gap-2.5">
      <div class="flex size-10 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
        <Globe class="size-5" />
      </div>
      <div>
        <h3 class="text-[15px] font-semibold text-text-primary">世界时钟</h3>
        <p class="text-xs text-muted-foreground">多时区并排显示 · 可增删与排序</p>
      </div>
    </div>

    <ul class="flex-1 space-y-2">
      <li
        v-for="row in rows"
        :key="row.tz"
        class="group flex items-center gap-3 rounded-xl border border-white/5 bg-card/40 px-4 py-3 transition-colors hover:border-white/10"
      >
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="truncate text-sm font-medium text-text-primary">{{ row.label }}</span>
            <span class="shrink-0 rounded-full bg-white/5 px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
              {{ row.offset }}
            </span>
          </div>
          <div class="mt-0.5 truncate text-[11px] text-muted-foreground">
            {{ row.time.dateFullText }}
          </div>
        </div>

        <div class="shrink-0 text-right font-semibold tabular-nums text-text-primary">
          {{ row.time.timeText }}
          <span class="text-xs text-cyan-400/80">{{ row.time.secondText }}</span>
        </div>

        <div class="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            class="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30"
            :disabled="prefs.cities.indexOf(row.tz) === 0"
            title="上移"
            @click="moveCity(row.tz, -1)"
          >
            <ArrowUp class="size-3.5" />
          </button>
          <button
            class="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30"
            :disabled="prefs.cities.indexOf(row.tz) === prefs.cities.length - 1"
            title="下移"
            @click="moveCity(row.tz, 1)"
          >
            <ArrowDown class="size-3.5" />
          </button>
          <button
            class="rounded-md p-1 text-muted-foreground transition-colors hover:bg-status-offline/15 hover:text-status-offline disabled:opacity-30"
            :disabled="prefs.cities.length <= 1"
            title="移除"
            @click="removeCity(row.tz)"
          >
            <Trash2 class="size-3.5" />
          </button>
        </div>
      </li>
    </ul>

    <div class="mt-4 flex items-center gap-3">
      <Plus class="size-4 shrink-0 text-muted-foreground" />
      <SelectField
        :options="availableOptions"
        :model-value="pendingCity"
        placeholder="添加城市…"
        class="flex-1"
        @update:model-value="onPick"
      />
    </div>
  </div>
</template>
