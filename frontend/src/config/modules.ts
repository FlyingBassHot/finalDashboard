import type { Component } from 'vue'
import {
  Database,
  Monitor,
  Server,
  UserCircle,
  Users,
  Wifi,
} from 'lucide-vue-next'

export interface ModuleInfo {
  key: string
  title: string
  subtitle: string
  icon: Component
  description: string
  /** 未来将提供的能力点 */
  features: string[]
}

/** 尚未开发后端的模块配置（占位页使用） */
export const MODULES: Record<string, ModuleInfo> = {
  profile: {
    key: 'profile',
    title: '个人中心',
    subtitle: 'PROFILE',
    icon: UserCircle,
    description: '管理你的账号信息、家庭角色与个人偏好。',
    features: ['账号资料', '家庭角色', '个人偏好'],
  },
  nas: {
    key: 'nas',
    title: 'NAS 存储',
    subtitle: 'NAS STORAGE',
    icon: Database,
    description: '集中查看 NAS 存储状态、文件空间与备份任务。',
    features: ['存储空间', '文件浏览', '备份任务'],
  },
  router: {
    key: 'router',
    title: '网络中心',
    subtitle: 'ROUTER',
    icon: Wifi,
    description: '监控家庭网络状态、在线设备与带宽使用情况。',
    features: ['设备列表', '实时带宽', '信号质量'],
  },
  server: {
    key: 'server',
    title: '服务器',
    subtitle: 'SERVER',
    icon: Server,
    description: '跟踪家庭服务器的运行状态与资源占用。',
    features: ['CPU / 内存', '磁盘读写', '服务进程'],
  },
  pc: {
    key: 'pc',
    title: '我的电脑',
    subtitle: 'MY PC',
    icon: Monitor,
    description: '查看电脑在线状态、硬件信息与远程控制入口。',
    features: ['在线状态', '硬件信息', '远程控制'],
  },
  family: {
    key: 'family',
    title: '家庭中心',
    subtitle: 'FAMILY',
    icon: Users,
    description: '管理家庭成员与家庭设备的使用权限。',
    features: ['成员管理', '设备授权', '家庭日程'],
  },
}
