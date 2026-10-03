<script setup>
import AssignmentsView from '../../components/AssignmentsView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <AssignmentsView :token="token" />
</template>
