<script setup>
import DocumentsView from '../../components/DocumentsView.vue'

const token = localStorage.getItem('token') || ''
</script>

<template>
  <DocumentsView :token="token" />
</template>
