<script setup>
// 骨架阶段占位页，后续替换为登录/聊天页面
</script>

<template>
  <main class="page">
    <h1>校园课程智能助手</h1>
    <p class="tagline">能查真实课表 · 能按文档作答 · 能帮你存计划</p>
    <div class="status">
      <span class="dot"></span>
      <span>项目骨架已就绪（M1）</span>
    </div>
    <div class="cards">
      <div class="card">课表查询</div>
      <div class="card">资料问答 RAG</div>
      <div class="card">学习计划</div>
    </div>
  </main>
</template>

<style scoped>
.page {
  max-width: 640px;
  margin: 80px auto;
  text-align: center;
  font-family: system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.tagline {
  color: #666;
  font-size: 15px;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 16px 0 32px;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f0fdf4;
  color: #16a34a;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.card {
  padding: 24px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  color: #374151;
  font-size: 14px;
}
</style>
