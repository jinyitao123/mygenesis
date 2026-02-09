<template>
  <div class="h-toolbar bg-ide-toolbar border-b border-ide-border flex items-center px-4">
    <!-- 左侧：Logo和面包屑 -->
    <div class="flex items-center space-x-4">
      <div class="flex items-center space-x-2">
        <div class="w-6 h-6 bg-ide-accent rounded flex items-center justify-center">
          <span class="text-white font-bold text-sm">G</span>
        </div>
        <span class="font-semibold text-white">Genesis Forge</span>
      </div>
      
      <div class="flex items-center text-sm">
        <span class="text-gray-400">当前领域:</span>
        <span class="ml-2 px-2 py-1 rounded bg-ide-sidebar">{{ currentDomain }}</span>
      </div>
    </div>

    <!-- 中间：全局搜索 -->
    <div class="flex-1 mx-8">
      <el-input
        v-model="searchQuery"
        placeholder="搜索对象、动作或输入命令 (如 '> reload')"
        size="small"
        class="max-w-xl"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 右侧：状态指示器和操作按钮 -->
    <div class="flex items-center space-x-4">
      <!-- 状态指示器 -->
      <div class="flex items-center space-x-2">
        <div :class="['status-indicator', connectionStatus]"></div>
        <span class="text-xs">{{ statusText }}</span>
      </div>

      <!-- Git状态 -->
      <div v-if="gitBranch" class="flex items-center space-x-2">
        <el-icon><Branch /></el-icon>
        <span class="text-xs">{{ gitBranch }}</span>
        <span v-if="gitChanges" class="text-xs text-ide-warning">({{ gitChanges }})</span>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center space-x-2">
        <el-button size="small" type="primary" @click="handleDeploy">
          <el-icon class="mr-1"><Upload /></el-icon>
          部署
        </el-button>
        
        <el-button size="small" @click="handleHotReload">
          <el-icon class="mr-1"><Refresh /></el-icon>
          热重载
        </el-button>
        
        <el-button size="small" @click="toggleAiPanel">
          <el-icon class="mr-1"><MagicStick /></el-icon>
          AI Copilot
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Branch, Upload, Refresh, MagicStick } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { useUiStore } from '@/stores/ui'

const projectStore = useProjectStore()
const uiStore = useUiStore()

const searchQuery = ref('')

const currentDomain = computed(() => projectStore.currentDomain?.name || '未选择')
const connectionStatus = computed(() => projectStore.connectionStatus)
const statusText = computed(() => {
  switch (projectStore.connectionStatus) {
    case 'online': return '已连接'
    case 'offline': return '离线'
    case 'connecting': return '连接中'
    default: return '未知'
  }
})

const gitBranch = computed(() => projectStore.gitStatus?.branch)
const gitChanges = computed(() => {
  const changes = projectStore.gitStatus?.changes
  return changes ? `${changes.added}+ ${changes.modified}~ ${changes.deleted}-` : ''
})

const handleDeploy = () => {
  console.log('部署操作')
  // TODO: 实现部署逻辑
}

const handleHotReload = () => {
  console.log('热重载操作')
  // TODO: 实现热重载逻辑
}

const toggleAiPanel = () => {
  uiStore.toggleBottomPanel('ai')
}
</script>