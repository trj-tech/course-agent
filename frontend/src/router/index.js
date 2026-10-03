import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import StudentView from '../views/StudentView.vue'
import StudentChat from '../views/student/StudentChat.vue'
import StudentSchedule from '../views/student/StudentSchedule.vue'
import StudentDocuments from '../views/student/StudentDocuments.vue'
import StudentPlans from '../views/student/StudentPlans.vue'
import ManagerLayout from '../views/manager/ManagerLayout.vue'
import ManagerHome from '../views/manager/ManagerHome.vue'
import ManagerChat from '../views/manager/ManagerChat.vue'
import ManagerDocuments from '../views/manager/ManagerDocuments.vue'
import ManagerCourses from '../views/manager/ManagerCourses.vue'
import ManagerSchedules from '../views/manager/ManagerSchedules.vue'
import ManagerUsers from '../views/manager/ManagerUsers.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    {
      path: '/',
      component: StudentView,
      children: [
        { path: '', redirect: '/chat' },
        { path: 'chat', component: StudentChat },
        { path: 'schedule', component: StudentSchedule },
        { path: 'documents', component: StudentDocuments },
        { path: 'plans', component: StudentPlans },
      ],
    },
    {
      path: '/manager',
      component: ManagerLayout,
      children: [
        { path: '', redirect: '/manager/home' },
        { path: 'home', component: ManagerHome },
        { path: 'chat', component: ManagerChat },
        { path: 'documents', component: ManagerDocuments },
        { path: 'courses', component: ManagerCourses },
        { path: 'schedules', component: ManagerSchedules },
        { path: 'users', component: ManagerUsers },
      ],
    },
  ],
})

// 简单登录守卫：未登录一律去登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!token && to.path !== '/login') return '/login'
  return true
})

export default router
