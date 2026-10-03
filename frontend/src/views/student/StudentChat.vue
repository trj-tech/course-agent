<script setup>
import ChatView from '../../components/ChatView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <ChatView :token="token" show-history />
</template>
