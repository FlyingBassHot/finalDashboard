<script setup lang="ts">
import { computed, ref } from 'vue'
import { CheckCircle2, Globe, Plus, RotateCcw, SlidersHorizontal, X } from 'lucide-vue-next'
import { useClockPrefs } from '@/composables/useClockPrefs'
import { CLOCK_FACES } from '@/components/clock/registry'
import { CITY_PRESETS, cityLabel } from '@/lib/clock'
import Switch from '@/components/ui/Switch.vue'
import Button from '@/components/ui/Button.vue'
import SelectField from '@/components/settings/SelectField.vue'

const { prefs, setFace, update, addCity, removeCity, reset } = useClockPrefs()

const pendingCity = ref<string | null>(null)

const availableOptions = computed(() =>
  CITY_PRESETS.filter((city) => !prefs.cities.includes(city.tz)).map((city) => ({
    value: city.tz,
    label: `${city.name} · ${city.tz}`,
  })),
)

function onPick(timezone: string) {
  addCity(timezone)
  pendingCity.value = null
}
</script>

<template>
  <div class="glass-card p-6 sm:p-7">
    <div class="mb-6 flex flex-wrap items-center gap-2.5">
      <div class="flex size-10 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
        <SlidersHorizontal class="size-5" />
      </div>
      <div class="min-w-0 flex-1">
        <h3 class="text-[15px] font-semibold text-text-primary">时钟偏好</h3>
        <p class="text-xs text-muted-foreground">
          保存在本机浏览器，不写入服务器数据库
        </p>
      </div>
      <Button variant="ghost" size="sm" @click="reset()">
        <RotateCcw class="size-3.5" />
        恢复默认
      </Button>
    </div>

    <!-- 时钟样式 -->
    <div class="mb-5">
      <div class="mb-2 text-xs font-medium text-muted-foreground">时钟样式</div>
      <div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <button
          v-for="face in CLOCK_FACES"
          :key="face.id"
          class="rounded-xl border px-4 py-3 text-left transition-all"
          :class="
            prefs.face === face.id
              ? 'border-cyan-400/40 bg-cyan-500/10 ring-1 ring-inset ring-cyan-400/20'
              : 'border-white/5 bg-card/40 hover:border-white/15'
          "
          @click="setFace(face.id)"
        >
          <span class="flex items-center gap-1.5 text-sm font-medium text-text-primary">
            <CheckCircle2
              class="size-3.5"
              :class="prefs.face === face.id ? 'text-cyan-400' : 'text-transparent'"
            />
            {{ face.name }}
          </span>
          <span class="mt-0.5 block pl-5 text-[11px] leading-snug text-muted-foreground">
            {{ face.description }}
          </span>
        </button>
      </div>
    </div>

    <!-- 开关 -->
    <div class="mb-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
      <Switch
        :model-value="prefs.hour12"
        label="12 小时制"
        description="关闭为 24 小时制"
        @update:model-value="update('hour12', $event)"
      />
      <Switch
        :model-value="prefs.showSeconds"
        label="显示秒"
        @update:model-value="update('showSeconds', $event)"
      />
      <Switch
        :model-value="prefs.showUptime"
        label="显示服务运行时长"
        description="首页时钟卡底部"
        @update:model-value="update('showUptime', $event)"
      />
    </div>

    <!-- 世界时钟城市 -->
    <div>
      <div class="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Globe class="size-3.5" />
        世界时钟城市
        <span class="text-muted-foreground/50">（{{ prefs.cities.length }} 个）</span>
      </div>

      <div class="flex flex-wrap gap-2">
        <span
          v-for="tz in prefs.cities"
          :key="tz"
          class="inline-flex items-center gap-1.5 rounded-full border border-white/8 bg-card/60 py-1.5 pl-3 pr-2 text-xs text-text-secondary"
        >
          {{ cityLabel(tz) }}
          <span class="font-mono text-[10px] text-muted-foreground/70">{{ tz }}</span>
          <button
            class="rounded-full p-0.5 text-muted-foreground transition-colors hover:bg-status-offline/15 hover:text-status-offline disabled:opacity-30"
            :disabled="prefs.cities.length <= 1"
            title="移除"
            @click="removeCity(tz)"
          >
            <X class="size-3" />
          </button>
        </span>
      </div>

      <div class="mt-3 flex items-center gap-3">
        <Plus class="size-4 shrink-0 text-muted-foreground" />
        <SelectField
          :options="availableOptions"
          :model-value="pendingCity"
          placeholder="添加城市…"
          class="max-w-xs flex-1"
          @update:model-value="onPick"
        />
      </div>
    </div>
  </div>
</template>
