<template>
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- 标签页导航 -->
    <div class="h-10 bg-ide-sidebar border-b border-ide-border flex items-center px-2">
      <div class="flex-1 flex overflow-x-auto">
        <div
          v-for="tab in tabs"
          :key="tab.id"
          class="px-4 py-2 text-sm flex items-center cursor-pointer border-r border-ide-border min-w-32"
          :class="{
            'bg-ide-bg': activeTabId === tab.id,
            'text-white': activeTabId === tab.id,
            'text-gray-400 hover:text-white': activeTabId !== tab.id
          }"
          @click="setActiveTab(tab.id)"
        >
          <el-icon v-if="tab.icon" class="mr-2">
            <component :is="tab.icon" />
          </el-icon>
          <span class="truncate">{{ tab.title }}</span>
          <span v-if="tab.isDirty" class="ml-2 text-ide-warning">●</span>
          <el-button
            v-if="tabs.length > 1"
            type="text"
            size="small"
            class="ml-2 opacity-0 hover:opacity-100"
            @click.stop="closeTab(tab.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 标签页操作 -->
      <div class="flex items-center space-x-2 px-2">
        <el-dropdown @command="handleTabCommand">
          <el-button type="text" size="small">
            <el-icon><More /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="split-horizontal">水平分屏</el-dropdown-item>
              <el-dropdown-item command="split-vertical">垂直分屏</el-dropdown-item>
              <el-dropdown-item command="close-all" divided>关闭所有</el-dropdown-item>
              <el-dropdown-item command="close-others">关闭其他</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主工作区 -->
    <div class="flex-1 overflow-hidden">
      <div v-if="activeTab" class="h-full">
        <component
          :is="getEditorComponent(activeTab.type)"
          :key="activeTab.id"
          :tab="activeTab"
          @save="handleSave"
          @validate="handleValidate"
        />
      </div>
      <div v-else class="h-full flex items-center justify-center text-gray-500">
        <div class="text-center">
          <el-icon class="text-4xl mb-4"><DocumentAdd /></el-icon>
          <p>从左侧资源树选择项目开始编辑</p>
          <p class="text-sm mt-2">或拖拽资产到工作区</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Close, More, DocumentAdd } from '@element-plus/icons-vue'
import GraphEditor from '@/components/studio/GraphEditor.vue'
import CodeEditor from '@/components/studio/CodeEditor.vue'
import SplitView from '@/components/studio/SplitView.vue'
import { useEditorStore } from '@/stores/editor'

const editorStore = useEditorStore()

const tabs = computed(() => editorStore.tabs)
const activeTabId = computed(() => editorStore.activeTabId)
const activeTab = computed(() => editorStore.activeTab)

const getEditorComponent = (type: string) => {
  switch (type) {
    case 'graph': return GraphEditor
    case 'code': return CodeEditor
    case 'split': return SplitView
    default: return CodeEditor
  }
}

const setActiveTab = (tabId: string) => {
  editorStore.setActiveTab(tabId)
}

const closeTab = (tabId: string) => {
  editorStore.closeTab(tabId)
}

const handleSave = (tabId: string, content: any) => {
  console.log('保存标签页:', tabId, content)
  // TODO: 实现保存逻辑
}

const handleValidate = (tabId: string) => {
  console.log('验证标签页:', tabId)
  // TODO: 实现验证逻辑
}

const handleTabCommand = (command: string) => {
  switch (command) {
    case 'split-horizontal':
      editorStore.splitTab('horizontal')
      break
    case 'split-vertical':
      editorStore.splitTab('vertical')
      break
    case 'close-all':
      editorStore.closeAllTabs()
      break
    case 'close-others':
      editorStore.closeOtherTabs()
      break
  }
}
</script>