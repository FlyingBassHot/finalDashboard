<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  CheckCircle2,
  Home,
  Info,
  Loader2,
  MapPin,
  Save,
} from 'lucide-vue-next'
import {
  getHomeSettings,
  searchLocations,
  updateHomeSettings,
  type HomeSettings,
  type HomeSettingsUpdate,
  type LocationOption,
} from '@/api/settings'
import { useWeather } from '@/composables/useWeather'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import Input from '@/components/ui/Input.vue'
import SelectField from '@/components/settings/SelectField.vue'
import ClockPrefsCard from '@/components/settings/ClockPrefsCard.vue'

const router = useRouter()
const weather = useWeather()

/* ---------- 状态 ---------- */
const settings = ref<HomeSettings | null>(null)
const settingsLoading = ref(true)
const settingsError = ref('')

const homeName = ref('')

const provinces = ref<LocationOption[]>([])
const provincesLoading = ref(false)

const cities = ref<LocationOption[]>([])
const citiesLoading = ref(false)

const districts = ref<LocationOption[]>([])
const districtsLoading = ref(false)

const province = ref<LocationOption | null>(null)
const city = ref<LocationOption | null>(null)
const district = ref<LocationOption | null>(null)

const saving = ref(false)
const saveError = ref('')
const saved = ref(false)

/* ---------- 选项映射 ---------- */
const provinceOptions = computed(() =>
  provinces.value.map((p) => ({ value: p.adcode, label: p.name })),
)
const cityOptions = computed(() =>
  cities.value.map((c) => ({ value: c.adcode, label: c.name })),
)
const districtOptions = computed(() =>
  districts.value.map((d) => ({ value: d.adcode, label: d.name })),
)

/** 直辖市的下一级直接是区县，此时第二个选择器充当「区县」 */
const cityFieldLabel = computed(() =>
  cities.value[0]?.level === 'district' ? '区县' : '城市',
)
/** 第三个选择器仅在选中了「城市」级节点时出现 */
const showDistrictField = computed(() => city.value?.level === 'city')

/** 已选行政区划链（省 → 市 → 区） */
const chain = computed(() =>
  [province.value, city.value, district.value].filter(Boolean) as LocationOption[],
)

/** 选中的最末级节点（坐标与 adcode 以它为准） */
const deepest = computed(() => chain.value[chain.value.length - 1] ?? null)

const canSave = computed(
  () =>
    chain.value.length >= 2 &&
    homeName.value.trim().length > 0 &&
    deepest.value !== null &&
    !saving.value,
)

const selectedLocationText = computed(() => chain.value.map((n) => n.name).join(' · '))

/* ---------- 级联加载 ---------- */
async function loadProvinces(): Promise<void> {
  provincesLoading.value = true
  try {
    const result = await searchLocations('中国', 1)
    provinces.value = result[0]?.children ?? []
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : '省份数据加载失败'
  } finally {
    provincesLoading.value = false
  }
}

async function loadChildren(node: LocationOption): Promise<LocationOption[]> {
  const result = await searchLocations(node.adcode, 1)
  return result[0]?.children ?? []
}

async function onProvinceChange(adcode: string) {
  const next = provinces.value.find((p) => p.adcode === adcode) ?? null
  province.value = next
  city.value = null
  district.value = null
  cities.value = []
  districts.value = []
  if (!next) return

  citiesLoading.value = true
  try {
    cities.value = await loadChildren(next)
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : '城市数据加载失败'
  } finally {
    citiesLoading.value = false
  }
}

async function onCityChange(adcode: string) {
  const next = cities.value.find((c) => c.adcode === adcode) ?? null
  city.value = next
  district.value = null
  districts.value = []
  if (!next || next.level !== 'city') return

  districtsLoading.value = true
  try {
    districts.value = await loadChildren(next)
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : '区县数据加载失败'
  } finally {
    districtsLoading.value = false
  }
}

function onDistrictChange(adcode: string) {
  district.value = districts.value.find((d) => d.adcode === adcode) ?? null
}

/* ---------- 保存 ---------- */
function buildPayload(): HomeSettingsUpdate | null {
  const c = chain.value
  const last = deepest.value
  if (!c.length || !last) return null

  const cityNode = c.find((n) => n.level === 'city')
  const districtNode = c.find((n) => n.level === 'district')

  return {
    home_name: homeName.value.trim(),
    country: '中国',
    province: c[0]!.name,
    city: cityNode?.name ?? c[0]!.name,
    district: districtNode?.name ?? null,
    adcode: last.adcode,
    gcj02_latitude: last.gcj02_latitude ?? 0,
    gcj02_longitude: last.gcj02_longitude ?? 0,
    latitude: last.latitude ?? 0,
    longitude: last.longitude ?? 0,
    timezone: last.timezone || 'Asia/Shanghai',
  }
}

async function save() {
  const payload = buildPayload()
  if (!payload || !canSave.value) return

  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    settings.value = await updateHomeSettings(payload)
    // 后端保存后已自动刷新天气，清空前端缓存让页面重新拉取
    weather.invalidate()
    saved.value = true
    setTimeout(() => {
      saved.value = false
    }, 5000)
  } catch (err) {
    saveError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    saving.value = false
  }
}

/* ---------- 初始化 + 回显当前设置 ---------- */
onMounted(async () => {
  settingsLoading.value = true
  try {
    const [s] = await Promise.all([getHomeSettings(), loadProvinces()])
    settings.value = s
    homeName.value = s.home_name

    // 回显已保存的位置
    if (s.province) {
      const p = provinces.value.find((x) => x.name === s.province)
      if (p) {
        province.value = p
        citiesLoading.value = true
        try {
          cities.value = await loadChildren(p)
        } finally {
          citiesLoading.value = false
        }

        if (s.city) {
          const c = cities.value.find((x) => x.name === s.city)
          if (c) {
            city.value = c
            if (c.level === 'city') {
              districtsLoading.value = true
              try {
                districts.value = await loadChildren(c)
              } finally {
                districtsLoading.value = false
              }
              if (s.district) {
                district.value =
                  districts.value.find((x) => x.name === s.district) ?? null
              }
            }
          }
        }
      }
    }
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : '设置加载失败'
  } finally {
    settingsLoading.value = false
  }
})

/* ---------- 当前配置展示 ---------- */
const currentLocationText = computed(() => {
  const s = settings.value
  if (!s?.is_configured) return '未配置'
  return [s.province, s.city, s.district].filter(Boolean).join(' · ') || '未配置'
})

const infoRows = computed(() => {
  const s = settings.value
  if (!s) return []
  return [
    { label: '行政区划代码', value: s.adcode ?? '--' },
    {
      label: 'WGS84 坐标',
      value:
        s.latitude !== null && s.longitude !== null
          ? `${Number(s.latitude).toFixed(4)}, ${Number(s.longitude).toFixed(4)}`
          : '--',
    },
    {
      label: 'GCJ02 坐标',
      value:
        s.gcj02_latitude !== null && s.gcj02_longitude !== null
          ? `${Number(s.gcj02_latitude).toFixed(4)}, ${Number(s.gcj02_longitude).toFixed(4)}`
          : '--',
    },
    { label: '时区', value: s.timezone ?? '--' },
    { label: '数据来源', value: s.location_source === 'amap_district' ? '高德行政区' : s.location_source },
  ]
})
</script>

<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div>
      <h2 class="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">设置</h2>
      <p class="mt-1.5 text-sm text-muted-foreground">
        家庭位置决定天气模块的监测地点，保存后自动刷新天气数据
      </p>
    </div>

    <!-- 全局错误 -->
    <div
      v-if="settingsError"
      class="glass-card flex items-center gap-3 border-status-offline/30 p-4 text-sm text-status-offline"
    >
      <Info class="size-4 shrink-0" />
      {{ settingsError }}
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <!-- 家庭与位置设置 -->
      <div class="glass-card p-6 sm:p-7 xl:col-span-2">
        <div class="mb-6 flex items-center gap-2.5">
          <div class="flex size-10 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
            <MapPin class="size-5" />
          </div>
          <div>
            <h3 class="text-[15px] font-semibold text-text-primary">家庭与位置</h3>
            <p class="text-xs text-muted-foreground">行政区划数据来自高德，坐标已转换为 WGS84</p>
          </div>
        </div>

        <!-- 加载骨架 -->
        <div v-if="settingsLoading" class="space-y-5">
          <Skeleton class="h-11 w-full" />
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Skeleton v-for="i in 3" :key="i" class="h-[74px]" />
          </div>
          <Skeleton class="h-11 w-32" />
        </div>

        <template v-else>
          <!-- 家庭名称 -->
          <div class="mb-5">
            <label class="mb-1.5 block text-xs font-medium text-muted-foreground">
              家庭名称
            </label>
            <div class="relative">
              <Home class="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60" />
              <Input v-model="homeName" class="pl-9" placeholder="给家起个名字，如「温馨小家」" />
            </div>
          </div>

          <!-- 位置级联选择 -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <SelectField
              label="省份"
              :options="provinceOptions"
              :model-value="province?.adcode ?? null"
              :loading="provincesLoading"
              placeholder="选择省份"
              @update:model-value="onProvinceChange"
            />
            <SelectField
              :label="cityFieldLabel"
              :options="cityOptions"
              :model-value="city?.adcode ?? null"
              :loading="citiesLoading"
              :disabled="!province"
              :placeholder="province ? '请选择' : '请先选择省份'"
              @update:model-value="onCityChange"
            />
            <SelectField
              v-if="showDistrictField"
              label="区县（可选）"
              :options="districtOptions"
              :model-value="district?.adcode ?? null"
              :loading="districtsLoading"
              placeholder="不选则精确到城市"
              @update:model-value="onDistrictChange"
            />
          </div>

          <!-- 已选位置预览 -->
          <div
            v-if="selectedLocationText"
            class="mt-4 flex flex-wrap items-center gap-2 rounded-xl border border-white/5 bg-card/50 px-4 py-3"
          >
            <MapPin class="size-4 text-cyan-400" />
            <span class="text-sm text-text-primary">{{ selectedLocationText }}</span>
            <span v-if="deepest" class="ml-auto font-mono text-xs text-muted-foreground">
              adcode {{ deepest.adcode }} ·
              {{ deepest.latitude?.toFixed(4) }}, {{ deepest.longitude?.toFixed(4) }} (WGS84)
            </span>
          </div>

          <!-- 保存反馈 -->
          <div
            v-if="saved"
            class="mt-4 flex flex-wrap items-center gap-2 rounded-xl border border-status-online/25 bg-status-online/8 px-4 py-3 text-sm text-status-online"
          >
            <CheckCircle2 class="size-4" />
            已保存，天气已按新位置刷新
            <button
              class="ml-auto inline-flex items-center gap-1 text-xs text-cyan-400 hover:underline"
              @click="router.push('/weather')"
            >
              查看天气
              <ArrowRight class="size-3" />
            </button>
          </div>
          <div
            v-if="saveError"
            class="mt-4 rounded-xl border border-status-offline/25 bg-status-offline/8 px-4 py-3 text-sm text-status-offline"
          >
            {{ saveError }}
          </div>

          <!-- 保存按钮 -->
          <div class="mt-6 flex items-center gap-3">
            <Button variant="gradient" :disabled="!canSave" :loading="saving" @click="save">
              <Save class="size-4" />
              保存设置
            </Button>
            <span v-if="!canSave && !settingsLoading" class="text-xs text-muted-foreground">
              请先选择家庭名称与所在城市
            </span>
            <Loader2
              v-if="citiesLoading || districtsLoading"
              class="size-4 animate-spin text-muted-foreground"
            />
          </div>
        </template>
      </div>

      <!-- 当前配置 -->
      <div class="glass-card p-6 sm:p-7">
        <div class="mb-5 flex items-center gap-2.5">
          <div class="flex size-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-400">
            <Info class="size-5" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-[15px] font-semibold text-text-primary">当前配置</h3>
            <p class="truncate text-xs text-muted-foreground">
              {{ settings?.home_name ?? '—' }}
            </p>
          </div>
          <Badge :variant="settings?.is_configured ? 'online' : 'warning'">
            {{ settings?.is_configured ? '已配置' : '未配置' }}
          </Badge>
        </div>

        <div v-if="settingsLoading" class="space-y-3">
          <Skeleton v-for="i in 5" :key="i" class="h-10" />
        </div>

        <template v-else-if="settings">
          <div
            class="mb-4 flex items-center gap-2 rounded-xl border border-white/5 bg-card/50 px-4 py-3"
          >
            <MapPin class="size-4 shrink-0 text-cyan-400" />
            <span class="text-sm font-medium text-text-primary">{{ currentLocationText }}</span>
          </div>

          <dl class="space-y-3">
            <div
              v-for="row in infoRows"
              :key="row.label"
              class="flex items-center justify-between gap-3 border-b border-white/5 pb-2.5 last:border-0"
            >
              <dt class="shrink-0 text-xs text-muted-foreground">{{ row.label }}</dt>
              <dd class="truncate font-mono text-xs text-text-secondary">{{ row.value }}</dd>
            </div>
          </dl>

          <p class="mt-5 text-[11px] leading-relaxed text-muted-foreground/60">
            WGS84 坐标用于 Open-Meteo 天气服务；GCJ02 坐标保留供高德地图功能使用。
          </p>
        </template>
      </div>
    </div>

    <!-- 时钟偏好（存本机 localStorage，不写入服务器） -->
    <ClockPrefsCard />
  </div>
</template>
