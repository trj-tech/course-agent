<script setup>
import ScheduleView from '../../components/ScheduleView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <ScheduleView :token="token" />
</template>
