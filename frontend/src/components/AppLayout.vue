<script setup>
import { ElAvatar } from 'element-plus'

const props = defineProps({
  title: { type: String, required: true }, // 顶栏标题，如「学生端」「管理后台」
  menus: { type: Array, required: true }, // [{ index, label, icon }] icon 为组件
  activeIndex: { type: String, default: '' },
  user: { type: Object, default: null },
  onSelect: { type: Function, default: null }, // (index) => void
})

defineOptions({ inheritAttrs: false })
</script>

<template>
  <el-container class="layout">
    <!-- 左侧深色侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-icon">
          <svg viewBox="0 0 1024 1024" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path
              d="M512 96 64 320l448 224 448-224L512 96zm-96 512v128c0 35 128 64 192 64s192-29 192-64V608l-96 48v112c-16 8-40 16-96 16s-80-8-96-16V656l-96-48zm-16-128 112 56 112-56-112-56-112 56z"
            />
          </svg>
        </span>
        <span class="logo-text">校园课程智能助手</span>
      </div>
      <el-menu :default-active="activeIndex" class="menu" @select="(i) => onSelect && onSelect(i)">
        <el-menu-item v-for="m in menus" :key="m.index" :index="m.index">
          <el-icon class="menu-icon"><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="body">
      <!-- 白色顶栏 -->
      <el-header class="header" height="60px">
        <span class="title">{{ title }}</span>
        <div class="right">
          <slot name="headerExtra" />
          <el-dropdown v-if="user" trigger="click">
            <span class="user">
              <el-avatar :size="28" class="avatar">{{ (user.name || user.username || '?').slice(0, 1) }}</el-avatar>
              <span class="who">{{ user.name }}（{{ user.role === 'admin' ? '管理员' : '学生' }}）</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="onSelect && onSelect('logout')">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
  overflow: hidden;
}

/* ---------- 侧边栏（白底，参考 Ant Design 浅色菜单） ---------- */
.aside {
  background: #fff;
  color: #1f2329;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #1f2329;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.logo-icon {
  display: flex;
  color: #1890ff;
}

.menu {
  flex: 1;
  border-right: none;
  background: transparent;
  padding-top: 8px;
}

.menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  color: rgba(0, 0, 0, 0.65);
  margin: 2px 0;
}

.menu :deep(.el-menu-item .menu-icon) {
  font-size: 16px;
  margin-right: 8px;
}

.menu :deep(.el-menu-item:hover) {
  background: #f5f5f5;
  color: #1890ff;
}

.menu :deep(.el-menu-item.is-active) {
  background: #e6f7ff;
  color: #1890ff;
  border-right: 3px solid #1890ff;
}

.menu :deep(.el-menu-item.is-active:hover) {
  background: #e6f7ff;
  color: #1890ff;
}

/* ---------- 右侧主体 ---------- */
.body {
  min-width: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eef0f3;
  padding: 0 20px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2329;
}

.right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.avatar {
  background: #1890ff;
  color: #fff;
  font-size: 13px;
}

.who {
  color: #374151;
  font-size: 14px;
}

.main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
