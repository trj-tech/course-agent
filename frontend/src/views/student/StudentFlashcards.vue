<script setup>
import FlashcardsView from '../../components/FlashcardsView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <FlashcardsView :token="token" />
</template>
