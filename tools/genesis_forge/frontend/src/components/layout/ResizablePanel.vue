<template>
  <div class="flex h-full min-w-0" ref="container">
    <!-- 左侧分隔条（用于右侧面板） -->
    <div 
      v-if="position === 'right'"
      class="w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize flex-shrink-0"
      @mousedown="startResize"
      @dblclick="handleDoubleClick"
      :class="{ 'bg-blue-500': isResizing }"
      title="拖拽调整宽度 | 双击重置"
    ></div>
    
    <!-- 面板内容 -->
    <div 
      class="h-full overflow-auto" 
      :style="{ width: panelWidth + 'px', minWidth: minWidth + 'px', maxWidth: maxWidth + 'px' }"
      ref="panel"
    >
      <slot></slot>
    </div>
    
    <!-- 右侧分隔条（用于左侧面板） -->
    <div 
      v-if="position === 'left'"
      class="w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize flex-shrink-0"
      @mousedown="startResize"
      @dblclick="handleDoubleClick"
      :class="{ 'bg-blue-500': isResizing }"
      title="拖拽调整宽度 | 双击重置"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  // 初始宽度
  defaultWidth?: number
  // 最小宽度
  minWidth?: number
  // 最大宽度
  maxWidth?: number
  // 存储键（用于持久化）
  storageKey?: string
  // 面板位置（left或right）
  position?: 'left' | 'right'
}

const props = withDefaults(defineProps<Props>(), {
  defaultWidth: 256,
  minWidth: 160,
  maxWidth: 600,
  storageKey: '',
  position: 'left'
})

const emit = defineEmits<{
  'width-change': [width: number]
}>()

// 响应式状态
const panelWidth = ref(props.defaultWidth)
const isResizing = ref(false)

// 监听宽度变化并发出事件
watch(panelWidth, (newWidth) => {
  emit('width-change', newWidth)
})

// 引用
const container = ref<HTMLElement>()
const panel = ref<HTMLElement>()

// 从localStorage加载保存的宽度
const loadSavedWidth = () => {
  if (props.storageKey) {
    try {
      const saved = localStorage.getItem(props.storageKey)
      if (saved) {
        const width = parseInt(saved, 10)
        if (!isNaN(width) && width >= props.minWidth && width <= props.maxWidth) {
          panelWidth.value = width
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
      localStorage.setItem(props.storageKey, panelWidth.value.toString())
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
  e.stopPropagation()
  
  console.log(`Start resize: position=${props.position}, clientX=${e.clientX}, startWidth=${panelWidth.value}`)
  
  isResizing.value = true
  startX = e.clientX
  startWidth = panelWidth.value
  
  // 添加全局事件监听
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  
  // 防止文本选择
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
  
  // 添加激活样式
  if (container.value) {
    const handle = container.value.querySelector('.w-1')
    if (handle) {
      handle.classList.add('bg-blue-500')
    }
  }
}

const handleMouseMove = (e: MouseEvent) => {
  if (!isResizing.value) return
  
  const deltaX = e.clientX - startX
  let newWidth = startWidth + deltaX
  
  // 对于右侧面板，调整方向相反
  if (props.position === 'right') {
    newWidth = startWidth - deltaX
  }
  
  // 限制宽度范围
  newWidth = Math.max(props.minWidth, Math.min(props.maxWidth, newWidth))
  
  // 调试日志
  console.log(`Resize: position=${props.position}, deltaX=${deltaX.toFixed(1)}, start=${startWidth}, new=${newWidth.toFixed(1)}, min=${props.minWidth}, max=${props.maxWidth}`)
  
  panelWidth.value = newWidth
}

const stopResize = () => {
  if (!isResizing.value) return
  
  console.log(`Stop resize: position=${props.position}, finalWidth=${panelWidth.value}`)
  
  isResizing.value = false
  
  // 移除事件监听
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
  
  // 恢复样式
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  
  // 移除激活样式
  if (container.value) {
    const handle = container.value.querySelector('.w-1')
    if (handle) {
      handle.classList.remove('bg-blue-500')
    }
  }
  
  // 保存宽度
  saveWidth()
}

// 双击分隔条重置宽度
const handleDoubleClick = () => {
  panelWidth.value = props.defaultWidth
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

/* 确保分隔条可以接收鼠标事件 */
.w-1 {
  position: relative;
  z-index: 10;
}

/* 调试：分隔条激活时的高亮效果 */
.w-1.bg-blue-500 {
  background-color: #3b82f6 !important;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}
</style>