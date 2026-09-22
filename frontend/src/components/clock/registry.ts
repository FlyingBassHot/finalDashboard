import type { Component } from 'vue'
import type { ClockFaceId } from '@/composables/useClockPrefs'
import DigitalFace from './faces/DigitalFace.vue'
import FlipFace from './faces/FlipFace.vue'
import AnalogFace from './faces/AnalogFace.vue'

/* ============================================
   时钟面孔注册表 —— 插件化入口
   新增一种时钟样式：实现一个接收 ClockFaceProps 的组件，
   然后在这里加一行即可（详情页样式切换器与设置页会自动出现新选项）
   ============================================ */

export interface ClockFaceMeta {
  id: ClockFaceId
  /** 样式切换器里显示的名称 */
  name: string
  description: string
  component: Component
  /** 是否适合小尺寸（首页卡片 / 顶栏迷你钟） */
  compact: boolean
}

export const DEFAULT_FACE: ClockFaceMeta = {
  id: 'digital',
  name: '数字钟',
  description: '极简大号数字，清晰易读',
  component: DigitalFace,
  compact: true,
}

export const CLOCK_FACES: ClockFaceMeta[] = [
  DEFAULT_FACE,
  {
    id: 'flip',
    name: '翻页钟',
    description: '机械翻页动画，复古质感',
    component: FlipFace,
    compact: true,
  },
  {
    id: 'analog',
    name: '模拟表盘',
    description: 'SVG 指针平滑扫秒，适合壁挂展示',
    component: AnalogFace,
    compact: false,
  },
]

export function getFace(id: string): ClockFaceMeta {
  return CLOCK_FACES.find((face) => face.id === id) ?? DEFAULT_FACE
}
