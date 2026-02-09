<template>
  <div class="flex flex-col h-full">
    <TopBar />
    <div class="flex flex-1 overflow-hidden">
      <SideBar />
      <MainContent />
    </div>
    <BottomPanel />
  </div>
</template>

<script setup lang="ts">
import TopBar from './TopBar.vue'
import SideBar from './SideBar.vue'
import MainContent from './MainContent.vue'
import BottomPanel from './BottomPanel.vue'
</script>