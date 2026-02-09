<template>
  <div class="h-screen bg-gray-900 text-white flex flex-col">
    <!-- 通知系统 -->
    <Notification ref="notificationRef" />
    
    <!-- 顶部导航 -->
    <header class="bg-gray-800 px-6 py-4 border-b border-gray-700">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
              <span class="font-bold">G</span>
            </div>
            <h1 class="text-xl font-bold">Genesis Forge Studio</h1>
          </div>
          <nav class="flex space-x-4">
            <button @click="showProjects" class="px-3 py-2 rounded hover:bg-gray-700">项目</button>
            <button @click="showEditor" class="px-3 py-2 rounded hover:bg-gray-700">编辑</button>
            <button @click="showView" class="px-3 py-2 rounded hover:bg-gray-700">视图</button>
            <button @click="showTools" class="px-3 py-2 rounded hover:bg-gray-700">工具</button>
            <button @click="showHelp" class="px-3 py-2 rounded hover:bg-gray-700">帮助</button>
          </nav>
        </div>
        <div class="flex items-center space-x-4">
          <div class="text-sm">
            <span class="text-gray-400">状态:</span>
            <span :class="['ml-2', connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400']">
              ● {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
            </span>
          </div>
          <button @click="checkBackend" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
            检查后端
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="flex-1 flex overflow-hidden">
      <!-- 左侧边栏 -->
      <aside class="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
        <h2 class="text-lg font-semibold mb-4">项目资源</h2>
        <div class="space-y-2">
          <div 
            v-for="domain in domains" 
            :key="domain.id"
            @click="selectDomain(domain)"
            :class="['p-3 rounded cursor-pointer', selectedDomainId === domain.id ? 'bg-blue-600' : 'hover:bg-gray-700']"
          >
            <div class="font-medium">{{ domain.name }}</div>
            <div class="text-sm text-gray-400">{{ domain.description }}</div>
          </div>
          <div v-if="domains.length === 0" class="p-3 rounded bg-gray-700 text-center">
            <div class="text-sm text-gray-400">加载中...</div>
          </div>
        </div>

        <div class="mt-8">
          <h3 class="text-md font-semibold mb-3">快速操作</h3>
          <div class="space-y-2">
            <button @click="importCSV" class="w-full p-3 bg-blue-600 rounded hover:bg-blue-700 flex items-center justify-center">
              <span>导入CSV</span>
            </button>
            <button @click="analyzeWithAI" class="w-full p-3 bg-green-600 rounded hover:bg-green-700 flex items-center justify-center">
              <span>AI分析</span>
            </button>
            <button @click="openVisualEditor" class="w-full p-3 bg-purple-600 rounded hover:bg-purple-700 flex items-center justify-center">
              <span>可视化编辑</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- 主工作区 -->
      <div class="flex-1 flex flex-col">
        <!-- 标签页 -->
        <div class="bg-gray-800 border-b border-gray-700 px-4">
          <div class="flex space-x-1">
            <button class="px-4 py-2 bg-gray-900 rounded-t-lg border border-gray-700 border-b-0">
              欢迎页面
            </button>
            <button class="px-4 py-2 rounded-t-lg hover:bg-gray-700">
              代码编辑器
            </button>
            <button class="px-4 py-2 rounded-t-lg hover:bg-gray-700">
              图谱视图
            </button>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="flex-1 p-8 overflow-y-auto">
          <div class="max-w-4xl mx-auto">
            <div class="text-center mb-12">
              <h2 class="text-3xl font-bold mb-4">欢迎使用 Genesis Forge Studio</h2>
              <p class="text-gray-300 text-lg">
                基于AI辅助的CSV到本体转换和可视化编辑平台
              </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              <!-- 功能卡片1 -->
              <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center mb-4">
                  <span class="text-2xl">📊</span>
                </div>
                <h3 class="text-xl font-semibold mb-3">CSV导入</h3>
                <p class="text-gray-400 mb-4">
                  上传CSV文件，AI自动分析数据结构，智能转换为本体定义
                </p>
                <button @click="importCSV" class="w-full py-2 bg-blue-600 rounded hover:bg-blue-700">
                  开始导入
                </button>
              </div>

              <!-- 功能卡片2 -->
              <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mb-4">
                  <span class="text-2xl">🤖</span>
                </div>
                <h3 class="text-xl font-semibold mb-3">AI Copilot</h3>
                <p class="text-gray-400 mb-4">
                  智能助手帮助优化本体结构、调整属性和规则，提供专业建议
                </p>
                <button @click="analyzeWithAI" class="w-full py-2 bg-green-600 rounded hover:bg-green-700">
                  启动AI助手
                </button>
              </div>

              <!-- 功能卡片3 -->
              <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <span class="text-2xl">🔗</span>
                </div>
                <h3 class="text-xl font-semibold mb-3">可视化编辑</h3>
                <p class="text-gray-400 mb-4">
                  拖拽式编辑本体关系，实时预览图数据库结构，直观管理数据模型
                </p>
                <button @click="openVisualEditor" class="w-full py-2 bg-purple-600 rounded hover:bg-purple-700">
                  打开编辑器
                </button>
              </div>
            </div>

            <!-- 工作流程 -->
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 class="text-2xl font-semibold mb-6 text-center">核心工作流程</h3>
              <div class="relative">
                <!-- 连接线 -->
                <div class="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-700 transform -translate-y-1/2 hidden md:block"></div>
                
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
                  <!-- 步骤1 -->
                  <div class="text-center">
                    <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
                      <span class="text-2xl">1</span>
                    </div>
                    <h4 class="font-semibold mb-2">上传CSV</h4>
                    <p class="text-sm text-gray-400">导入业务数据文件</p>
                  </div>

                  <!-- 步骤2 -->
                  <div class="text-center">
                    <div class="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
                      <span class="text-2xl">2</span>
                    </div>
                    <h4 class="font-semibold mb-2">AI分析</h4>
                    <p class="text-sm text-gray-400">智能识别数据结构</p>
                  </div>

                  <!-- 步骤3 -->
                  <div class="text-center">
                    <div class="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
                      <span class="text-2xl">3</span>
                    </div>
                    <h4 class="font-semibold mb-2">生成本体</h4>
                    <p class="text-sm text-gray-400">创建XML本体定义</p>
                  </div>

                  <!-- 步骤4 -->
                  <div class="text-center">
                    <div class="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
                      <span class="text-2xl">4</span>
                    </div>
                    <h4 class="font-semibold mb-2">图数据库</h4>
                    <p class="text-sm text-gray-400">存储和可视化查询</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 快速开始 -->
            <div class="mt-12">
              <h3 class="text-2xl font-semibold mb-6">快速开始</h3>
              <div class="bg-gray-800 rounded-lg p-6">
                <ol class="space-y-4">
                  <li class="flex items-start">
                    <span class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-4 flex-shrink-0">1</span>
                    <div>
                      <h4 class="font-semibold mb-1">准备CSV数据</h4>
                      <p class="text-gray-400">确保CSV文件包含表头，数据格式规范</p>
                    </div>
                  </li>
                  <li class="flex items-start">
                    <span class="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mr-4 flex-shrink-0">2</span>
                    <div>
                      <h4 class="font-semibold mb-1">选择目标领域</h4>
                      <p class="text-gray-400">从左侧选择或创建新的领域配置</p>
                    </div>
                  </li>
                  <li class="flex items-start">
                    <span class="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center mr-4 flex-shrink-0">3</span>
                    <div>
                      <h4 class="font-semibold mb-1">使用AI辅助</h4>
                      <p class="text-gray-400">让AI帮助优化本体结构和规则定义</p>
                    </div>
                  </li>
                  <li class="flex items-start">
                    <span class="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center mr-4 flex-shrink-0">4</span>
                    <div>
                      <h4 class="font-semibold mb-1">保存和部署</h4>
                      <p class="text-gray-400">将生成的本体保存到图数据库供其他系统使用</p>
                    </div>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 底部状态栏 -->
    <footer class="bg-gray-800 px-6 py-3 border-t border-gray-700">
      <div class="flex items-center justify-between text-sm">
        <div class="flex items-center space-x-6">
          <span>Genesis Forge Studio v2.0</span>
          <span class="text-gray-400">|</span>
          <span>当前领域: {{ currentDomain || '未选择' }}</span>
          <span class="text-gray-400">|</span>
          <span>后端: {{ backendStatus }}</span>
        </div>
        <div class="flex items-center space-x-4">
          <span>{{ statusMessage }}</span>
          <div :class="['w-2 h-2 rounded-full', statusColor]"></div>
        </div>
      </div>
    </footer>

    <!-- 可视化编辑器组件 -->
    <VisualEditor 
      v-if="showVisualEditor" 
      :domain="selectedDomain"
      @close="closeVisualEditor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from './utils/api'
import Notification from './components/Notification.vue'
import VisualEditor from './components/VisualEditor.vue'
import notify, { notifySuccess, notifyError, notifyWarning, notifyInfo } from './utils/notify'

// 响应式状态
const notificationRef = ref()
const connectionStatus = ref('disconnected')
const domains = ref([])
const selectedDomainId = ref('')
const selectedDomain = ref<any>(null)
const currentDomain = ref('')
const backendStatus = ref('未知')
const statusMessage = ref('就绪')
const statusColor = ref('bg-green-500')
const showVisualEditor = ref(false)

// 领域模组配置（与后端保持一致）
const DOMAIN_PACKS: Record<string, any> = {
  "supply_chain": {
    "name": "供应链物流系统",
    "description": "卡车、仓库、货物运输仿真",
    "color": "#f59e0b",
    "icon": "truck"
  },
  "finance_risk": {
    "name": "金融风控图谱",
    "description": "账户、交易、担保关系网络",
    "color": "#8b5cf6",
    "icon": "chart-line"
  },
  "it_ops": {
    "name": "IT运维监控",
    "description": "服务器、网络、应用监控",
    "color": "#10b981",
    "icon": "server"
  },
  "empty": {
    "name": "空白项目",
    "description": "从零开始定义新的本体",
    "color": "#6b7280",
    "icon": "file-plus"
  }
}

// 基础功能函数
const checkBackend = async () => {
  try {
    // 尝试调用一个已知的API端点来检查后端连接
    const response = await api.editor.getGraphData()
    connectionStatus.value = 'connected'
    backendStatus.value = '运行中'
    statusMessage.value = '后端连接正常'
    statusColor.value = 'bg-green-500'
    notifySuccess('后端连接成功', '后端服务运行正常')
  } catch (error) {
    connectionStatus.value = 'disconnected'
    backendStatus.value = '离线'
    statusMessage.value = '后端连接失败'
    statusColor.value = 'bg-red-500'
    notifyWarning('后端连接失败', '请检查后端服务是否启动')
  }
}

const importCSV = () => {
  notifyInfo('CSV导入', 'CSV导入功能需要上传CSV文件')
  // 这里可以添加实际的CSV导入逻辑
}

const analyzeWithAI = () => {
  notifyInfo('AI分析', 'AI Copilot分析功能')
  // 这里可以添加实际的AI分析逻辑
}

const showProjects = () => {
  notifyInfo('项目管理', '项目管理功能')
}

const showEditor = () => {
  notifyInfo('代码编辑器', '代码编辑器功能')
}

const showView = () => {
  notifyInfo('视图', '视图功能')
}

const showTools = () => {
  notifyInfo('工具', '工具功能')
}

const showHelp = () => {
  notifyInfo('帮助', '帮助文档')
}

// 加载领域数据
const loadDomains = async () => {
  try {
    // 尝试从后端API获取领域数据
    const domainsData = await api.domain.getDomains()
    if (domainsData && Array.isArray(domainsData)) {
      domains.value = domainsData
    } else {
      // 如果API失败或返回无效数据，使用模拟数据
      domains.value = Object.entries(DOMAIN_PACKS).map(([id, config]) => ({
        id,
        name: config.name,
        description: config.description,
        color: config.color,
        icon: config.icon
      }))
    }
  } catch (error) {
    console.error('加载领域数据失败，使用模拟数据:', error)
    // 使用模拟数据
    domains.value = Object.entries(DOMAIN_PACKS).map(([id, config]) => ({
      id,
      name: config.name,
      description: config.description,
      color: config.color,
      icon: config.icon
    }))
  }
}

// 打开可视化编辑器
const openVisualEditor = async () => {
  if (!selectedDomainId.value) {
    notifyWarning('请先选择领域', '请从左侧选择一个领域后再打开可视化编辑器')
    return
  }
  
  statusMessage.value = '加载领域数据中...'
  statusColor.value = 'bg-yellow-500'
  
  try {
    const currentDomain = domains.value.find(d => d.id === selectedDomainId.value)
    if (!currentDomain) {
      throw new Error('未找到当前领域')
    }
    
    selectedDomain.value = currentDomain
    showVisualEditor.value = true
    
    statusMessage.value = '可视化编辑器已打开'
    statusColor.value = 'bg-green-500'
    
  } catch (error) {
    console.error('打开可视化编辑器失败:', error)
    notifyWarning('打开编辑器失败', `错误: ${error}\n\n使用模拟数据打开...`)
    
    const currentDomain = domains.value.find(d => d.id === selectedDomainId.value)
    selectedDomain.value = currentDomain || { id: 'unknown', name: '未知领域' }
    showVisualEditor.value = true
    
    statusMessage.value = '编辑器（模拟模式）'
    statusColor.value = 'bg-blue-500'
  }
}

// 关闭可视化编辑器
const closeVisualEditor = () => {
  showVisualEditor.value = false
  selectedDomain.value = null
  statusMessage.value = '返回主界面'
  statusColor.value = 'bg-green-500'
}

// 选择领域
const selectDomain = async (domain: any) => {
  selectedDomainId.value = domain.id
  selectedDomain.value = domain
  currentDomain.value = domain.name
  
  statusMessage.value = `切换到领域: ${domain.name}`
  statusColor.value = 'bg-yellow-500'
  
  try {
    // 首先尝试v1 API切换领域
    try {
      const data = await api.domain.switchDomain(domain.id)
      statusMessage.value = `已切换到: ${domain.name}`
      statusColor.value = 'bg-green-500'
      notifySuccess('领域切换成功', `已切换到: ${domain.name}\n\n${domain.description}`)
      return
    } catch (v1Error) {
      console.log('v1 API切换失败，尝试兼容API:', v1Error)
    }
    
    // 尝试兼容API
    const response = await fetch(`/api/domains/${domain.id}`, {
      method: 'POST'
    })
    
    if (response.ok) {
      statusMessage.value = `已切换到: ${domain.name}`
      statusColor.value = 'bg-green-500'
      notifySuccess('领域切换成功', `已切换到: ${domain.name}`)
    } else {
      throw new Error(`HTTP ${response.status}: 切换失败`)
    }
    
  } catch (error) {
    console.error('领域切换失败:', error)
    
    // 如果所有API都不可用，只在前端切换
    statusMessage.value = `前端切换到: ${domain.name}`
    statusColor.value = 'bg-blue-500'
    notifyWarning('前端切换', `已切换到领域: ${domain.name}\n\n注意：后端切换API不可用，仅前端切换`)
  }
}

// 页面加载时自动检查后端
onMounted(() => {
  // 初始化通知系统
  if (notificationRef.value) {
    notify.setNotificationInstance(notificationRef.value)
  }
  
  // 加载领域数据
  loadDomains()
  
  // 检查后端连接
  checkBackend()
})
</script>

<style scoped>
/* 基础样式 */
</style>