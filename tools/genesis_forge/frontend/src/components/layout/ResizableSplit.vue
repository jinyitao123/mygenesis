<template>
  <div class="flex-1 flex overflow-hidden" ref="container">
    <!-- 左侧面板 -->
    <div 
      class="h-full overflow-auto" 
      :style="{ width: leftWidth + 'px', minWidth: minLeftWidth + 'px', maxWidth: maxLeftWidth + 'px' }"
      ref="leftPanel"
    >
      <slot></slot>
    </div>
    
    <!-- 分隔条 -->
    <div 
      class="w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize flex-shrink-0"
      @mousedown="startResize"
      @dblclick="handleDoubleClick"
      :class="{ 'bg-blue-500': isResizing }"
      title="拖拽调整宽度 | 双击重置"
    ></div>
    
    <!-- 右侧面板（占位符） -->
    <div class="flex-1 h-full overflow-auto" ref="rightPanel">
      <!-- 右侧内容由父组件提供 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  // 初始左侧宽度
  initialLeftWidth?: number
  // 最小左侧宽度
  minLeftWidth?: number
  // 最大左侧宽度
  maxLeftWidth?: number
  // 存储键（用于持久化）
  storageKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialLeftWidth: 256, // 默认256px，对应原来的w-64 (16*16=256)
  minLeftWidth: 160, // 最小160px
  maxLeftWidth: 600, // 最大600px
  storageKey: ''
})

// 响应式状态
const leftWidth = ref(props.initialLeftWidth)
const isResizing = ref(false)

// 引用
const container = ref<HTMLElement>()
const leftPanel = ref<HTMLElement>()

// 从localStorage加载保存的宽度
const loadSavedWidth = () => {
  if (props.storageKey) {
    try {
      const saved = localStorage.getItem(props.storageKey)
      if (saved) {
        const width = parseInt(saved, 10)
        if (!isNaN(width) && width >= props.minLeftWidth && width <= props.maxLeftWidth) {
          leftWidth.value = width
        }
      }
    } catch (e) {
      console.error('加载保存的宽度失败:', e)
    }
  }
}

// 保存宽度到localStorage
const saveWidth = () => {
  if (props.storageKey) {
    try {
      localStorage.setItem(props.storageKey, leftWidth.value.toString())
    } catch (e) {
      console.error('保存宽度失败:', e)
    }
  }
}

// 调整大小相关变量
let startX = 0
let startWidth = 0

const startResize = (e: MouseEvent) => {
  e.preventDefault()
  isResizing.value = true
  startX = e.clientX
  startWidth = leftWidth.value
  
  // 添加全局事件监听
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  
  // 防止文本选择
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isResizing.value) return
  
  const deltaX = e.clientX - startX
  let newWidth = startWidth + deltaX
  
  // 限制宽度范围
  newWidth = Math.max(props.minLeftWidth, Math.min(props.maxLeftWidth, newWidth))
  
  leftWidth.value = newWidth
}

const stopResize = () => {
  if (!isResizing.value) return
  
  isResizing.value = false
  
  // 移除事件监听
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
  
  // 恢复样式
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  
  // 保存宽度
  saveWidth()
}

// 双击分隔条重置宽度
const handleDoubleClick = () => {
  leftWidth.value = props.initialLeftWidth
  saveWidth()
}

// 初始化
onMounted(() => {
  loadSavedWidth()
})

// 清理
onUnmounted(() => {
  if (isResizing.value) {
    stopResize()
  }
})
</script>

<style scoped>
/* 分隔条悬停效果 */
.w-1:hover {
  background-color: #3b82f6;
  transition: background-color 0.2s;
}

/* 调整大小时的样式 */
.bg-blue-500 {
  background-color: #3b82f6;
}
</style>