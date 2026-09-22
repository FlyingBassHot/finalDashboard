import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: 'Dashboard', breadcrumb: '总览' },
        },
        {
          path: 'weather',
          name: 'weather',
          component: () => import('@/views/WeatherView.vue'),
          meta: { title: '天气', breadcrumb: '天气站' },
        },
        {
          path: 'clock',
          name: 'clock',
          component: () => import('@/views/ClockView.vue'),
          meta: { title: '时钟', breadcrumb: '时钟' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: '个人中心', breadcrumb: '个人中心', module: 'profile' },
        },
        {
          path: 'nas',
          name: 'nas',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: 'NAS 存储', breadcrumb: '设备', module: 'nas' },
        },
        {
          path: 'router',
          name: 'router',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: '网络中心', breadcrumb: '设备', module: 'router' },
        },
        {
          path: 'server',
          name: 'server',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: '服务器', breadcrumb: '设备', module: 'server' },
        },
        {
          path: 'pc',
          name: 'pc',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: '我的电脑', breadcrumb: '设备', module: 'pc' },
        },
        {
          path: 'family',
          name: 'family',
          component: () => import('@/views/ModulePlaceholderView.vue'),
          meta: { title: '家庭中心', breadcrumb: '家庭', module: 'family' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { title: '设置', breadcrumb: '系统' },
        },
        { path: ':pathMatch(.*)*', redirect: '/dashboard' },
      ],
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string | undefined) ?? 'Home Hub'
  document.title = `${title} · Home Hub`
})

export { router }
