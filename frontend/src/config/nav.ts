import type { Component } from 'vue'
import {
  Clock,
  CloudSun,
  Database,
  LayoutDashboard,
  Monitor,
  Server,
  Settings,
  Users,
  Wifi,
} from 'lucide-vue-next'

export interface NavItem {
  label: string
  to: string
  icon: Component
  /** 搜索关键词（支持中英文别名） */
  keywords: string[]
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: '总览',
    items: [
      {
        label: 'Dashboard',
        to: '/dashboard',
        icon: LayoutDashboard,
        keywords: ['总览', '仪表盘', '首页', 'home', 'dashboard'],
      },
      {
        label: '天气',
        to: '/weather',
        icon: CloudSun,
        keywords: ['天气', '温度', '气象', 'weather', '温度站'],
      },
      {
        label: '时钟',
        to: '/clock',
        icon: Clock,
        keywords: ['时钟', '时间', '钟表', '秒表', 'clock', 'time', '世界时钟'],
      },
    ],
  },
  {
    label: '设备',
    items: [
      {
        label: 'NAS 存储',
        to: '/nas',
        icon: Database,
        keywords: ['nas', '存储', '硬盘', '群晖', 'storage'],
      },
      {
        label: '路由器',
        to: '/router',
        icon: Wifi,
        keywords: ['路由', '网络', 'wifi', 'router', '宽带'],
      },
      {
        label: '服务器',
        to: '/server',
        icon: Server,
        keywords: ['server', '服务器', '主机', 'linux'],
      },
      {
        label: '我的电脑',
        to: '/pc',
        icon: Monitor,
        keywords: ['pc', '电脑', '桌面', 'desktop'],
      },
    ],
  },
  {
    label: '家庭',
    items: [
      {
        label: '家庭中心',
        to: '/family',
        icon: Users,
        keywords: ['family', '家庭', '成员', '家人'],
      },
    ],
  },
  {
    label: '系统',
    items: [
      {
        label: '设置',
        to: '/settings',
        icon: Settings,
        keywords: ['settings', '设置', '配置', '选项'],
      },
    ],
  },
]

export const ALL_NAV_ITEMS = NAV_GROUPS.flatMap((group) => group.items)
