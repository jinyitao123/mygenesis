<template>
  <div class="mb-4">
    <div
      class="px-2 py-1 text-xs font-semibold text-gray-400 flex items-center cursor-pointer hover:bg-gray-800 rounded"
      @click="toggleExpanded"
    >
      <el-icon class="mr-1 transform transition-transform" :class="{ 'rotate-90': isExpanded }">
        <ArrowRight />
      </el-icon>
      <slot name="icon">
        <el-icon v-if="icon" class="mr-1">
          <component :is="icon" />
        </el-icon>
      </slot>
      {{ title }}
      <span class="ml-2 text-xs text-gray-500">({{ items.length }})</span>
    </div>

    <div v-show="isExpanded" class="mt-1 ml-4 space-y-1">
      <div
        v-for="item in items"
        :key="item.id"
        class="px-3 py-2 rounded hover:bg-gray-800 cursor-pointer flex items-center justify-between group"
        @click="$emit('item-click', item)"
        draggable="true"
        @dragstart="$emit('item-drag', $event, item)"
      >
        <div class="flex items-center">
          <el-icon v-if="item.icon" class="mr-2 text-sm">
            <component :is="item.icon" />
          </el-icon>
          <span class="text-sm">{{ item.name }}</span>
          <span v-if="item.description" class="ml-2 text-xs text-gray-400">
            {{ item.description }}
          </span>
        </div>
        
        <div class="opacity-0 group-hover:opacity-100 flex items-center space-x-1">
          <el-button
            type="text"
            size="small"
            @click.stop="$emit('item-edit', item)"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button
            type="text"
            size="small"
            @click.stop="$emit('item-delete', item)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ArrowRight, Edit, Delete } from '@element-plus/icons-vue'

defineProps<{
  title: string
  icon?: string
  items: any[]
}>()

defineEmits<{
  'item-click': [item: any]
  'item-drag': [event: DragEvent, item: any]
  'item-edit': [item: any]
  'item-delete': [item: any]
}>()

const isExpanded = ref(true)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}
</script>