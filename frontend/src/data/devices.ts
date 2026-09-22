/**
 * 设备占位数据 —— 后端设备接口开发完成后替换为真实数据。
 */
export interface Device {
  id: string
  name: string
  /** 设备英文名/型号（副标题） */
  model: string
  /** 图标 key（对应 DeviceCard 中的图标映射表） */
  icon: string
  /** 图标底色 */
  tint: string
  status: 'online' | 'offline'
  /** 状态描述（在线显示指标，离线显示上次在线时间） */
  metric: string
}

/**
 * 设备占位数据 —— 后端设备接口开发完成后替换为真实数据。
 */
export const DEVICES: Device[] = [
  {
    id: 'nas',
    name: 'NAS 存储',
    model: 'Synology DS923+',
    icon: 'Database',
    tint: 'bg-cyan-500/15 text-cyan-400',
    status: 'online',
    metric: 'CPU 23% · 存储 62%',
  },
  {
    id: 'router',
    name: '主路由器',
    model: 'AX6000 · 双频',
    icon: 'Wifi',
    tint: 'bg-violet-500/15 text-violet-400',
    status: 'online',
    metric: '信号 强 · 延迟 12ms',
  },
  {
    id: 'server',
    name: '家庭服务器',
    model: 'Home Server',
    icon: 'Server',
    tint: 'bg-sky-500/15 text-sky-400',
    status: 'online',
    metric: 'CPU 18% · 内存 54%',
  },
  {
    id: 'pc',
    name: '我的电脑',
    model: 'Desktop · Win11',
    icon: 'Monitor',
    tint: 'bg-slate-400/15 text-slate-300',
    status: 'offline',
    metric: '上次在线：昨天 22:31',
  },
  {
    id: 'light',
    name: '客厅灯光',
    model: '智能吸顶灯',
    icon: 'Lightbulb',
    tint: 'bg-amber-500/15 text-amber-400',
    status: 'online',
    metric: '亮度 80% · 暖白 3500K',
  },
  {
    id: 'ac',
    name: '客厅空调',
    model: '变频挂机 · 3匹',
    icon: 'AirVent',
    tint: 'bg-emerald-500/15 text-emerald-400',
    status: 'online',
    metric: '制冷 24°C · 风速 自动',
  },
]
