<script setup>
import ChatView from '../../components/ChatView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <div class="panel">
    <h2 class="page-title">课程助手</h2>
    <p class="sub">可查询课表、按知识库文档作答、制定学习计划，右侧可查看历史会话。</p>
    <ChatView :token="token" show-history />
  </div>
</template>

<style scoped>
.page-title {
  margin: 0;
  font-size: 17px;
}

.sub {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 12px;
}
</style>
