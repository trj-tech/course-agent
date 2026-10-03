<script setup>
import ScoresView from '../../components/ScoresView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <ScoresView :token="token" />
</template>
