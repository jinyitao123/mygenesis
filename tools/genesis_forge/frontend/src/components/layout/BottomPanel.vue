<template>
  <div
    class="border-t border-ide-border transition-all duration-300"
    :class="{
      'h-bottom-panel': isExpanded,
      'h-8': !isExpanded
    }"
  >
    <!-- 面板标题栏 -->
    <div
      class="h-8 bg-ide-sidebar flex items-center justify-between px-4 cursor-pointer"
      @click="toggleExpanded"
    >
      <div class="flex items-center space-x-4">
        <div
          v-for="panel in panels"
          :key="panel.id"
          class="flex items-center space-x-1"
          :class="{
            'text-white': activePanel === panel.id,
            'text-gray-400 hover:text-white': activePanel !== panel.id
          }"
          @click.stop="setActivePanel(panel.id)"
        >
          <el-icon>
            <component :is="panel.icon" />
          </el-icon>
          <span class="text-sm">{{ panel.title }}</span>
          <span
            v-if="panel.badge"
            class="px-1 py-0.5 text-xs rounded bg-ide-error text-white"
          >
            {{ panel.badge }}
          </span>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <el-button
          v-if="activePanel === 'console'"
          type="text"
          size="small"
          @click.stop="clearConsole"
        >
          清空
        </el-button>
        <el-icon class="transform transition-transform" :class="{ 'rotate-180': isExpanded }">
          <ArrowDown />
        </el-icon>
      </div>
    </div>

    <!-- 面板内容 -->
    <div v-show="isExpanded" class="h-[calc(100%-2rem)] overflow-hidden">
      <!-- AI Copilot面板 -->
      <AiCopilot v-show="activePanel === 'ai'" />

      <!-- 控制台面板 -->
      <div v-show="activePanel === 'console'" class="h-full p-4 overflow-y-auto">
        <div v-for="(log, index) in consoleLogs" :key="index" class="mb-2">
          <div class="flex items-start">
            <span class="text-xs text-gray-500 w-16 shrink-0">{{ log.time }}</span>
            <span
              class="text-sm"
              :class="{
                'text-ide-success': log.level === 'info',
                'text-ide-warning': log.level === 'warning',
                'text-ide-error': log.level === 'error'
              }"
            >
              {{ log.message }}
            </span>
          </div>
          <div v-if="log.details" class="ml-16 mt-1">
            <pre class="text-xs text-gray-400 bg-black/20 p-2 rounded">{{ log.details }}</pre>
          </div>
        </div>
      </div>

      <!-- 验证结果面板 -->
      <div v-show="activePanel === 'validation'" class="h-full p-4 overflow-y-auto">
        <div v-if="validationErrors.length === 0" class="text-center text-gray-500 py-8">
          <el-icon class="text-4xl text-ide-success"><CircleCheck /></el-icon>
          <p class="mt-2">所有验证通过</p>
        </div>
        <div v-else>
          <div v-for="error in validationErrors" :key="error.id" class="mb-3 p-3 rounded bg-black/20">
            <div class="flex items-start">
              <el-icon class="text-ide-error mt-1 mr-2"><Warning /></el-icon>
              <div class="flex-1">
                <div class="font-medium">{{ error.title }}</div>
                <div class="text-sm text-gray-400 mt-1">{{ error.message }}</div>
                <div v-if="error.location" class="text-xs text-gray-500 mt-2">
                  位置: {{ error.location }}
                </div>
                <el-button
                  v-if="error.fixable"
                  type="text"
                  size="small"
                  class="mt-2"
                  @click="applyFix(error)"
                >
                  自动修复
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDown, CircleCheck, Warning } from '@element-plus/icons-vue'
import AiCopilot from '@/components/panels/AiCopilot.vue'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

const panels = [
  { id: 'ai', title: 'AI Copilot', icon: 'MagicStick', badge: null },
  { id: 'console', title: '控制台', icon: 'Promotion', badge: null },
  { id: 'validation', title: '验证结果', icon: 'CircleCheck', badge: '3' }
]

const isExpanded = computed(() => uiStore.isBottomPanelExpanded)
const activePanel = computed(() => uiStore.activeBottomPanel)

const consoleLogs = ref([
  { time: '10:30:15', level: 'info', message: '系统启动完成', details: null },
  { time: '10:30:20', level: 'info', message: '连接到后端服务器', details: 'http://localhost:5000' },
  { time: '10:30:25', level: 'warning', message: '检测到未保存的更改', details: 'object_types.json' },
  { time: '10:30:30', level: 'error', message: '语法验证失败', details: '第12行: 缺少闭合括号' }
])

const validationErrors = ref([
  { id: 1, title: '未定义的引用', message: '动作规则中引用了未定义的对象类型 "Warehouse"', location: 'actions.json:45', fixable: true },
  { id: 2, title: '循环依赖', message: '检测到对象类型之间的循环依赖关系', location: 'schema.json:23-45', fixable: false },
  { id: 3, title: '缺少必需字段', message: '种子数据缺少必需字段 "capacity"', location: 'seed.json:12', fixable: true }
])

const toggleExpanded = () => {
  uiStore.toggleBottomPanel()
}

const setActivePanel = (panelId: string) => {
  uiStore.setActiveBottomPanel(panelId)
}

const clearConsole = () => {
  consoleLogs.value = []
}

const applyFix = (error: any) => {
  console.log('应用修复:', error)
  // TODO: 实现自动修复逻辑
}
</script>