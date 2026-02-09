<template>
  <div class="w-sidebar bg-ide-sidebar border-r border-ide-border flex flex-col overflow-hidden">
    <!-- 资源树标题 -->
    <div class="px-4 py-3 border-b border-ide-border">
      <h3 class="text-sm font-semibold text-gray-300">资源管理器</h3>
    </div>

    <!-- 可折叠资源树 -->
    <div class="flex-1 overflow-y-auto p-2">
      <!-- 对象类型 -->
      <ResourceSection
        title="对象类型"
        icon="Cube"
        :items="objectTypes"
        @item-click="handleObjectTypeClick"
        @item-drag="handleObjectTypeDrag"
      />

      <!-- 动作规则 -->
      <ResourceSection
        title="动作规则"
        icon="Operation"
        :items="actionRules"
        @item-click="handleActionRuleClick"
      />

      <!-- 种子数据 -->
      <ResourceSection
        title="种子数据"
        icon="DataLine"
        :items="seedData"
        @item-click="handleSeedDataClick"
      />

      <!-- 资产库 -->
      <div class="mt-6">
        <div class="px-2 py-1 text-xs font-semibold text-gray-400 flex items-center">
          <el-icon class="mr-1"><Collection /></el-icon>
          资产库
        </div>
        <div class="mt-2 space-y-1">
          <div
            v-for="template in entityTemplates"
            :key="template.id"
            class="px-3 py-2 rounded hover:bg-gray-800 cursor-move flex items-center"
            draggable="true"
            @dragstart="handleTemplateDrag($event, template)"
          >
            <div
              class="w-3 h-3 rounded-full mr-2"
              :style="{ backgroundColor: template.color }"
            ></div>
            <span class="text-sm">{{ template.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 领域切换 -->
    <div class="p-3 border-t border-ide-border">
      <el-select
        v-model="selectedDomain"
        placeholder="选择领域"
        size="small"
        class="w-full"
        @change="handleDomainChange"
      >
        <el-option
          v-for="domain in availableDomains"
          :key="domain.id"
          :label="domain.name"
          :value="domain.id"
        >
          <div class="flex items-center">
            <div
              class="w-3 h-3 rounded-full mr-2"
              :style="{ backgroundColor: domain.color }"
            ></div>
            <span>{{ domain.name }}</span>
            <span class="ml-2 text-xs text-gray-400">{{ domain.description }}</span>
          </div>
        </el-option>
      </el-select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Cube, Operation, DataLine, Collection } from '@element-plus/icons-vue'
import ResourceSection from './ResourceSection.vue'
import { useProjectStore } from '@/stores/project'
import { useEditorStore } from '@/stores/editor'

const projectStore = useProjectStore()
const editorStore = useEditorStore()

const selectedDomain = ref('')

const objectTypes = computed(() => projectStore.currentDomain?.objectTypes || [])
const actionRules = computed(() => projectStore.currentDomain?.actionRules || [])
const seedData = computed(() => projectStore.currentDomain?.seedData || [])
const availableDomains = computed(() => projectStore.availableDomains)
const entityTemplates = computed(() => [
  { id: 'node', name: '节点', color: '#007acc' },
  { id: 'edge', name: '边', color: '#4ec9b0' },
  { id: 'group', name: '组', color: '#ffcc00' },
  { id: 'annotation', name: '注释', color: '#f44747' }
])

const handleObjectTypeClick = (item: any) => {
  editorStore.openEditor('object', item)
}

const handleActionRuleClick = (item: any) => {
  editorStore.openEditor('action', item)
}

const handleSeedDataClick = (item: any) => {
  editorStore.openEditor('seed', item)
}

const handleObjectTypeDrag = (event: DragEvent, item: any) => {
  event.dataTransfer?.setData('application/json', JSON.stringify({
    type: 'objectType',
    data: item
  }))
}

const handleTemplateDrag = (event: DragEvent, template: any) => {
  event.dataTransfer?.setData('application/json', JSON.stringify({
    type: 'template',
    data: template
  }))
}

const handleDomainChange = (domainId: string) => {
  projectStore.switchDomain(domainId)
}
</script>