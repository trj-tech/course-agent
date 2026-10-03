<script setup>
import PlansView from '../../components/PlansView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <PlansView :token="token" />
</template>
