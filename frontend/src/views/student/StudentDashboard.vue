<script setup>
import DashboardView from '../../components/DashboardView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <DashboardView :token="token" />
</template>
