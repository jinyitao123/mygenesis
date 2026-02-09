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

    <!-- 可视化编辑器模态框 -->
    <div v-if="showVisualEditor" class="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      <div class="bg-gray-800 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
        <div>
          <h2 class="text-xl font-bold">可视化本体编辑器</h2>
          <div class="text-sm text-gray-400">领域: {{ visualEditorDomain?.name || '未命名领域' }}</div>
        </div>
        <div class="flex space-x-3">
          <button @click="loadGraphData" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            刷新数据
          </button>
          <button @click="closeVisualEditor" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            返回主界面
          </button>
        </div>
      </div>
      <div class="flex-1 flex">
        <div class="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
          <h3 class="font-semibold mb-4">对象类型 ({{ visualEditorSidebarData?.object_types?.length || 0 }})</h3>
          <div id="objectTypes" class="space-y-2 mb-6 max-h-60 overflow-y-auto">
            <div v-if="visualEditorSidebarData?.object_types?.length > 0">
              <div 
                v-for="type in visualEditorSidebarData.object_types" 
                :key="type.name"
                class="p-3 bg-gray-700 rounded cursor-move hover:bg-gray-600" 
                draggable="true" 
                data-type="node" 
                :data-object-type="type.name || '未命名'"
              >
                <div class="font-medium flex items-center justify-between">
                  <span>{{ type.name || '未命名类型' }}</span>
                  <span class="text-xs px-2 py-1 rounded bg-blue-900 text-blue-300">
                    {{ type.properties ? Object.keys(type.properties).length : 0 }} 属性
                  </span>
                </div>
                <div class="text-xs text-gray-400 mt-1">{{ type.description || '无描述' }}</div>
                <div v-if="type.properties" class="text-xs text-gray-500 mt-2">
                  属性: {{ Object.keys(type.properties).slice(0, 3).join(', ') }}{{ Object.keys(type.properties).length > 3 ? '...' : '' }}
                </div>
              </div>
            </div>
            <div v-else class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">
              无对象类型数据
            </div>
          </div>
          
          <h3 class="font-semibold mb-4">动作规则 ({{ visualEditorSidebarData?.action_rules?.length || 0 }})</h3>
          <div id="actionRules" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            <div v-if="visualEditorSidebarData?.action_rules?.length > 0">
              <div 
                v-for="rule in visualEditorSidebarData.action_rules" 
                :key="rule.name"
                class="p-3 bg-gray-700 rounded hover:bg-gray-600"
              >
                <div class="font-medium">{{ rule.name || '未命名规则' }}</div>
                <div class="text-xs text-gray-400 mt-1">{{ rule.description || '无描述' }}</div>
                <div class="text-xs text-gray-500 mt-2">
                  {{ rule.source || '?' }} → {{ rule.target || '?' }}
                  {{ rule.conditions ? ' | 有条件' : '' }}
                </div>
              </div>
            </div>
            <div v-else class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">
              无动作规则数据
            </div>
          </div>
          
          <h3 class="font-semibold mb-4">种子数据 ({{ visualEditorSidebarData?.seed_data?.length || 0 }})</h3>
          <div id="seedData" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            <div v-if="visualEditorSidebarData?.seed_data?.length > 0">
              <div 
                v-for="(seed, index) in visualEditorSidebarData.seed_data" 
                :key="index"
                class="p-2 bg-gray-700 rounded text-sm"
              >
                <div class="font-medium">{{ seed.name || `种子 ${index + 1}` }}</div>
                <div class="text-xs text-gray-400">{{ seed.type || '未知类型' }}</div>
              </div>
            </div>
            <div v-else class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">
              无种子数据
            </div>
          </div>
          
          <div class="mt-6">
            <h3 class="font-semibold mb-2">属性面板</h3>
            <div id="propertyPanel" class="text-sm text-gray-400 p-3 bg-gray-900 rounded">
              选择元素以编辑属性
            </div>
          </div>
        </div>
        
        <div class="flex-1 p-4">
          <div class="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
            <div class="p-4 border-b border-gray-700 flex justify-between items-center">
              <h3 class="font-semibold">图谱视图</h3>
              <div class="flex space-x-2">
                <button @click="addSampleNode" class="px-3 py-1 bg-blue-600 rounded text-sm hover:bg-blue-700">
                  添加示例节点
                </button>
                <button @click="clearGraph" class="px-3 py-1 bg-red-600 rounded text-sm hover:bg-red-700">
                  清空
                </button>
              </div>
            </div>
            <div class="flex-1 p-4 overflow-auto">
              <CytoscapeGraph 
                v-if="visualEditorGraphData"
                :elements="visualEditorGraphData.elements || []"
                :domain-config="visualEditorDomainConfig"
                @node-click="handleNodeClick"
                @edge-click="handleEdgeClick"
                @node-add="handleNodeAdd"
                @edge-add="handleEdgeAdd"
                @node-delete="handleNodeDelete"
                @edge-delete="handleEdgeDelete"
                @node-update="handleNodeUpdate"
                @edge-update="handleEdgeUpdate"
              />
              <div v-else class="h-full flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl mb-4">🔗</div>
                  <p class="text-lg mb-2">{{ visualEditorDomain?.name || '领域' }} 的可视化编辑器</p>
                  <p class="text-gray-400 mb-4">当前领域没有图谱数据</p>
                  <p class="text-sm text-gray-500 mb-6">您可以通过以下方式添加数据：</p>
                  <div class="space-y-3">
                    <button @click="loadRealData" class="w-full px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                      从后端加载数据
                    </button>
                    <button @click="addSampleNode" class="w-full px-4 py-2 bg-green-600 rounded hover:bg-green-700">
                      添加示例节点
                    </button>
                    <button @click="importCSVToEditor" class="w-full px-4 py-2 bg-purple-600 rounded hover:bg-purple-700">
                      导入CSV数据
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-800 px-6 py-3 border-t border-gray-700">
        <div class="flex justify-between items-center text-sm">
          <div>
            <span id="graphStats">
              {{ visualEditorGraphData ? `节点: ${visualEditorGraphData.stats?.nodes || 0}, 边: ${visualEditorGraphData.stats?.edges || 0}` : '就绪 | 拖拽模式' }}
            </span>
          </div>
          <div class="flex space-x-3">
            <button @click="validateGraph" class="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700">
              验证
            </button>
            <button @click="saveVisualEditor(visualEditorDomain?.id)" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
              保存到图数据库
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, render } from 'vue'
import api from './utils/api'
import Notification from './components/Notification.vue'
import CytoscapeGraph from './components/CytoscapeGraph.vue'
import notify, { notifySuccess, notifyError, notifyWarning, notifyInfo, confirm, prompt } from './utils/notify'

// 响应式状态
const notificationRef = ref()
const connectionStatus = ref('disconnected')
const domains = ref([])
const selectedDomainId = ref('')
const currentDomain = ref('')
const backendStatus = ref('未知')
const statusMessage = ref('就绪')
const statusColor = ref('bg-green-500')
const showVisualEditor = ref(false)
const visualEditorDomain = ref(null)
const visualEditorSidebarData = ref(null)
const visualEditorGraphData = ref(null)
const visualEditorDomainConfig = ref(null)

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

// 关闭可视化编辑器
const closeVisualEditor = () => {
  showVisualEditor.value = false
  statusMessage.value = '返回主界面'
  statusColor.value = 'bg-green-500'
}

// 加载图谱数据
const loadGraphData = async () => {
  try {
    const [graphResponse, sidebarResponse, configResponse] = await Promise.all([
      api.editor.getGraphData(),
      api.editor.getSidebarData(visualEditorDomain.value?.id),
      api.domain.getDomainConfig(visualEditorDomain.value?.id)
    ])
    
    // 更新数据
    visualEditorGraphData.value = graphResponse
    visualEditorSidebarData.value = sidebarResponse
    visualEditorDomainConfig.value = configResponse
    
    // 更新统计
    notifySuccess('数据刷新成功', '图谱数据已更新')
    
  } catch (error) {
    console.error('加载图谱数据失败:', error)
    notifyError('数据刷新失败', `错误: ${error}`)
  }
}

// 加载真实数据
const loadRealData = async () => {
  try {
    const response = await api.editor.getGraphData()
    visualEditorGraphData.value = response
    notifySuccess('数据加载成功', `已加载 ${response.elements?.length || 0} 个元素`)
  } catch (error) {
    console.error('加载真实数据失败:', error)
    notifyError('数据加载失败', `错误: ${error}`)
  }
}

// 添加示例节点
const addSampleNode = () => {
  if (!visualEditorGraphData.value) {
    visualEditorGraphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
  }
  
  const newNode = {
    id: `node_${Date.now()}`,
    type: 'node',
    data: {
      label: '示例节点',
      type: 'sample',
      description: '通过可视化编辑器添加的示例节点'
    },
    position: { x: 100, y: 100 }
  }
  
  visualEditorGraphData.value.elements.push(newNode)
  visualEditorGraphData.value.stats.nodes = (visualEditorGraphData.value.stats.nodes || 0) + 1
  
  notifySuccess('节点添加成功', '已添加示例节点到图谱')
}

// 清空图谱
const clearGraph = async () => {
  const confirmed = await confirm({
    title: '确认清空',
    message: '确定要清空所有图元素吗？此操作不可撤销。',
    confirmText: '清空',
    cancelText: '取消',
    type: 'warning'
  })
  
  if (confirmed) {
    visualEditorGraphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
    notifySuccess('已清空', '所有图元素已清空')
  }
}

// 验证图谱
const validateGraph = async () => {
  try {
    const response = await api.ontology.checkIntegrity()
    if (response.status === 'success') {
      notifySuccess('验证完成', response.message || '本体完整性检查通过')
    } else if (response.status === 'warning') {
      notifyWarning('验证警告', `${response.message || '发现一些问题'}\n\n错误: ${JSON.stringify(response.errors, null, 2)}`)
    } else {
      notifyError('验证失败', response.message || '未知错误')
    }
  } catch (error) {
    notifyError('验证失败', `错误: ${error}`)
  }
}

// 保存可视化编辑器
const saveVisualEditor = async (domainId: string) => {
  try {
    // 获取当前领域配置
    const domainConfig = await api.domain.getDomainConfig(domainId)
    
    // 创建简单的本体配置
    const ontology = {
      name: `可视化编辑_${new Date().toISOString().split('T')[0]}`,
      description: '通过可视化编辑器创建的本体',
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      objectTypes: [
        {
          name: 'VisualNode',
          description: '可视化节点',
          properties: {
            label: { type: 'string', description: '节点标签' },
            type: { type: 'string', description: '节点类型' }
          }
        }
      ],
      relationships: [],
      rules: []
    }
    
    // 保存到领域
    await api.upload.saveOntologyToDomain(domainId, ontology)
    
    notifySuccess('本体保存成功', `已保存到领域: ${domainId}\n\n现在可以在以下位置使用：\n1. E:\\Documents\\MyGame\\genesis\n2. E:\\Documents\\MyGame\\applications\n3. 其他业务系统`)
    
    closeVisualEditor()
    statusMessage.value = '已保存到图数据库'
    statusColor.value = 'bg-green-500'
    
  } catch (error) {
    notifyError('保存失败', `错误: ${error}\n\n尝试使用备用保存方法...`)
    
    // 尝试HTMX保存
    try {
      const response = await api.editor.save({
        type: 'ontology',
        content: '可视化编辑器生成的本体',
        domain: domainId
      })
      
      if (response.success) {
        notifySuccess('保存成功', '本体已成功保存')
        closeVisualEditor()
        statusMessage.value = '保存成功'
        statusColor.value = 'bg-green-500'
      } else {
        throw new Error('HTMX保存也失败')
      }
    } catch (htmxError) {
      notifyError('所有保存方法都失败', '请检查后端服务是否正常运行')
    }
  }
}

// CytoscapeGraph 事件处理函数
const handleNodeClick = (node: any) => {
  console.log('节点点击:', node)
  const propertyPanel = document.getElementById('propertyPanel')
  if (propertyPanel) {
    propertyPanel.innerHTML = `
      <div class="font-medium mb-2">节点属性</div>
      <div class="text-xs space-y-1">
        <div><span class="text-gray-500">ID:</span> ${node.id}</div>
        <div><span class="text-gray-500">标签:</span> ${node.data?.label || '无'}</div>
        <div><span class="text-gray-500">类型:</span> ${node.data?.type || '无'}</div>
        ${node.data?.description ? `<div><span class="text-gray-500">描述:</span> ${node.data.description}</div>` : ''}
      </div>
    `
  }
}

const handleEdgeClick = (edge: any) => {
  console.log('边点击:', edge)
  const propertyPanel = document.getElementById('propertyPanel')
  if (propertyPanel) {
    propertyPanel.innerHTML = `
      <div class="font-medium mb-2">边属性</div>
      <div class="text-xs space-y-1">
        <div><span class="text-gray-500">ID:</span> ${edge.id}</div>
        <div><span class="text-gray-500">源:</span> ${edge.data?.source || '无'}</div>
        <div><span class="text-gray-500">目标:</span> ${edge.data?.target || '无'}</div>
        <div><span class="text-gray-500">关系:</span> ${edge.data?.relationship || '无'}</div>
        ${edge.data?.description ? `<div><span class="text-gray-500">描述:</span> ${edge.data.description}</div>` : ''}
      </div>
    `
  }
}

const handleNodeAdd = (node: any) => {
  console.log('添加节点:', node)
  if (!visualEditorGraphData.value) {
    visualEditorGraphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
  }
  
  visualEditorGraphData.value.elements.push(node)
  visualEditorGraphData.value.stats.nodes = (visualEditorGraphData.value.stats.nodes || 0) + 1
  
  notifySuccess('节点添加成功', `已添加节点: ${node.data?.label || node.id}`)
}

const handleEdgeAdd = (edge: any) => {
  console.log('添加边:', edge)
  if (!visualEditorGraphData.value) {
    visualEditorGraphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
  }
  
  visualEditorGraphData.value.elements.push(edge)
  visualEditorGraphData.value.stats.edges = (visualEditorGraphData.value.stats.edges || 0) + 1
  
  notifySuccess('边添加成功', `已添加边: ${edge.data?.source} → ${edge.data?.target}`)
}

const handleNodeDelete = (nodeId: string) => {
  console.log('删除节点:', nodeId)
  if (visualEditorGraphData.value?.elements) {
    visualEditorGraphData.value.elements = visualEditorGraphData.value.elements.filter(
      (el: any) => !(el.id === nodeId && el.type === 'node')
    )
    visualEditorGraphData.value.stats.nodes = Math.max(0, (visualEditorGraphData.value.stats.nodes || 0) - 1)
    
    notifySuccess('节点删除成功', `已删除节点: ${nodeId}`)
  }
}

const handleEdgeDelete = (edgeId: string) => {
  console.log('删除边:', edgeId)
  if (visualEditorGraphData.value?.elements) {
    visualEditorGraphData.value.elements = visualEditorGraphData.value.elements.filter(
      (el: any) => !(el.id === edgeId && el.type === 'edge')
    )
    visualEditorGraphData.value.stats.edges = Math.max(0, (visualEditorGraphData.value.stats.edges || 0) - 1)
    
    notifySuccess('边删除成功', `已删除边: ${edgeId}`)
  }
}

const handleNodeUpdate = (node: any) => {
  console.log('更新节点:', node)
  if (visualEditorGraphData.value?.elements) {
    const index = visualEditorGraphData.value.elements.findIndex(
      (el: any) => el.id === node.id && el.type === 'node'
    )
    if (index !== -1) {
      visualEditorGraphData.value.elements[index] = node
      notifySuccess('节点更新成功', `已更新节点: ${node.data?.label || node.id}`)
    }
  }
}

const handleEdgeUpdate = (edge: any) => {
  console.log('更新边:', edge)
  if (visualEditorGraphData.value?.elements) {
    const index = visualEditorGraphData.value.elements.findIndex(
      (el: any) => el.id === edge.id && el.type === 'edge'
    )
    if (index !== -1) {
      visualEditorGraphData.value.elements[index] = edge
      notifySuccess('边更新成功', `已更新边: ${edge.data?.source} → ${edge.data?.target}`)
    }
  }
}

// 导入CSV到编辑器
const importCSVToEditor = () => {
  notifyInfo('CSV导入', 'CSV导入功能需要先上传CSV文件到主界面')
  closeVisualEditor()
}

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
    
    // 1. 获取侧边栏数据（对象类型、动作规则、种子数据）
    let sidebarData = null
    try {
      sidebarData = await api.editor.getSidebarData(currentDomain.id)
      console.log('侧边栏数据:', sidebarData)
    } catch (error) {
      console.error('获取侧边栏数据失败:', error)
      // 使用空数据
      sidebarData = {
        object_types: [],
        action_rules: [],
        seed_data: []
      }
    }
    
    // 2. 获取图谱数据
    let graphData = null
    try {
      graphData = await api.editor.getGraphData()
      console.log('图谱数据:', graphData)
    } catch (error) {
      console.log('无法获取图谱数据，使用空数据:', error)
      graphData = {
        elements: [],
        stats: { nodes: 0, edges: 0 }
      }
    }
    
    // 3. 获取领域配置
    let domainConfig = null
    try {
      domainConfig = await api.domain.getDomainConfig(currentDomain.id)
      console.log('领域配置:', domainConfig)
    } catch (error) {
      console.log('无法获取领域配置:', error)
    }
    
    // 设置可视化编辑器数据并显示
    visualEditorDomain.value = currentDomain
    visualEditorSidebarData.value = sidebarData
    visualEditorGraphData.value = graphData
    visualEditorDomainConfig.value = domainConfig
    showVisualEditor.value = true
    
    statusMessage.value = '可视化编辑器已打开'
    statusColor.value = 'bg-green-500'
    
  } catch (error) {
    console.error('打开可视化编辑器失败:', error)
    notifyWarning('打开编辑器失败', `错误: ${error}\n\n使用模拟数据打开...`)
    
    const currentDomain = domains.value.find(d => d.id === selectedDomainId.value)
    visualEditorDomain.value = currentDomain || { id: 'unknown', name: '未知领域' }
    visualEditorSidebarData.value = { object_types: [], action_rules: [], seed_data: [] }
    visualEditorGraphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
    visualEditorDomainConfig.value = null
    showVisualEditor.value = true
    
    statusMessage.value = '编辑器（模拟模式）'
    statusColor.value = 'bg-blue-500'
  }
}

const createVisualEditor = (domain: any, sidebarData: any, graphData: any, domainConfig: any) => {
  const domainName = domain?.name || '未命名领域'
  const domainId = domain?.id || 'unknown'
  
  const editorHTML = `
    <div class="fixed inset-0 bg-gray-900 z-50 flex flex-col">
      <div class="bg-gray-800 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
        <div>
          <h2 class="text-xl font-bold">可视化本体编辑器</h2>
          <div class="text-sm text-gray-400">领域: ${domainName}</div>
        </div>
        <div class="flex space-x-3">
          <button onclick="loadGraphData()" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            刷新数据
          </button>
          <button onclick="closeVisualEditor()" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            返回主界面
          </button>
        </div>
      </div>
      <div class="flex-1 flex">
        <div class="w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
          <h3 class="font-semibold mb-4">对象类型 (${sidebarData?.object_types?.length || 0})</h3>
          <div id="objectTypes" class="space-y-2 mb-6 max-h-60 overflow-y-auto">
            ${sidebarData?.object_types?.length > 0 ? 
              sidebarData.object_types.map((type: any) => `
                <div class="p-3 bg-gray-700 rounded cursor-move hover:bg-gray-600" 
                     draggable="true" 
                     data-type="node" 
                     data-object-type="${type.name || '未命名'}">
                  <div class="font-medium flex items-center justify-between">
                    <span>${type.name || '未命名类型'}</span>
                    <span class="text-xs px-2 py-1 rounded bg-blue-900 text-blue-300">
                      ${type.properties ? Object.keys(type.properties).length : 0} 属性
                    </span>
                  </div>
                  <div class="text-xs text-gray-400 mt-1">${type.description || '无描述'}</div>
                  ${type.properties ? `
                    <div class="text-xs text-gray-500 mt-2">
                      属性: ${Object.keys(type.properties).slice(0, 3).join(', ')}${Object.keys(type.properties).length > 3 ? '...' : ''}
                    </div>
                  ` : ''}
                </div>
              `).join('') : 
              '<div class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">无对象类型数据</div>'
            }
          </div>
          
          <h3 class="font-semibold mb-4">动作规则 (${sidebarData?.action_rules?.length || 0})</h3>
          <div id="actionRules" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            ${sidebarData?.action_rules?.length > 0 ? 
              sidebarData.action_rules.map((rule: any) => `
                <div class="p-3 bg-gray-700 rounded hover:bg-gray-600">
                  <div class="font-medium">${rule.name || '未命名规则'}</div>
                  <div class="text-xs text-gray-400 mt-1">${rule.description || '无描述'}</div>
                  <div class="text-xs text-gray-500 mt-2">
                    ${rule.source || '?'} → ${rule.target || '?'}
                    ${rule.conditions ? ' | 有条件' : ''}
                  </div>
                </div>
              `).join('') : 
              '<div class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">无动作规则数据</div>'
            }
          </div>
          
          <h3 class="font-semibold mb-4">种子数据 (${sidebarData?.seed_data?.length || 0})</h3>
          <div id="seedData" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            ${sidebarData?.seed_data?.length > 0 ? 
              sidebarData.seed_data.map((seed: any, index: number) => `
                <div class="p-2 bg-gray-700 rounded text-sm">
                  <div class="font-medium">${seed.name || `种子 ${index + 1}`}</div>
                  <div class="text-xs text-gray-400">${seed.type || '未知类型'}</div>
                </div>
              `).join('') : 
              '<div class="text-gray-400 text-sm p-3 bg-gray-900 rounded text-center">无种子数据</div>'
            }
          </div>
          
          <div class="mt-6">
            <h3 class="font-semibold mb-2">属性面板</h3>
            <div id="propertyPanel" class="text-sm text-gray-400 p-3 bg-gray-900 rounded">
              选择元素以编辑属性
            </div>
          </div>
        </div>
        
        <div class="flex-1 p-4">
          <div class="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
            <div class="p-4 border-b border-gray-700 flex justify-between items-center">
              <h3 class="font-semibold">图谱视图</h3>
              <div class="flex space-x-2">
                <button onclick="addSampleNode()" class="px-3 py-1 bg-blue-600 rounded text-sm hover:bg-blue-700">
                  添加示例节点
                </button>
                <button onclick="clearGraph()" class="px-3 py-1 bg-red-600 rounded text-sm hover:bg-red-700">
                  清空
                </button>
              </div>
            </div>
            <div id="graphCanvas" class="flex-1 p-4 overflow-auto">
              ${graphData?.elements?.length > 0 ? renderGraphElements(graphData.elements, domainConfig) : renderEmptyGraph(domain)}
            </div>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-800 px-6 py-3 border-t border-gray-700">
        <div class="flex justify-between items-center text-sm">
          <div>
            <span id="graphStats">${graphData ? `节点: ${graphData.stats?.nodes || 0}, 边: ${graphData.stats?.edges || 0}` : '就绪 | 拖拽模式'}</span>
          </div>
          <div class="flex space-x-3">
            <button onclick="validateGraph()" class="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700">
              验证
            </button>
            <button onclick="saveVisualEditor('${selectedDomainId.value}')" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
              保存到图数据库
            </button>
          </div>
        </div>
      </div>
    </div>
  `
  
  const editorDiv = document.createElement('div')
  editorDiv.innerHTML = editorHTML
  document.body.appendChild(editorDiv)
  
  // 添加图元素渲染
  function renderGraphElements(elements: any[], domainConfig: any) {
    if (!elements || elements.length === 0) {
      return renderEmptyGraph(domain)
    }
    
    // 创建CytoscapeGraph组件的容器
    return `
      <div id="cytoscape-container" class="h-full w-full"></div>
    `
  }
  
  function renderEmptyGraph(domain: any) {
    const domainInfo = domain ? `
      <div class="mb-6 p-4 bg-gray-900 rounded-lg border border-gray-700">
        <h4 class="font-semibold mb-2">领域信息</h4>
        <div class="text-sm text-gray-400">
          <div>名称: ${domain.name}</div>
          <div>ID: ${domain.id}</div>
          <div>描述: ${domain.description || '无描述'}</div>
        </div>
      </div>
    ` : ''
    
    return `
      <div class="h-full flex flex-col">
        ${domainInfo}
        <div class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <div class="text-4xl mb-4">🔗</div>
            <p class="text-lg mb-2">${domain?.name || '领域'} 的可视化编辑器</p>
            <p class="text-gray-400 mb-4">当前领域没有图谱数据</p>
            <p class="text-sm text-gray-500 mb-6">您可以通过以下方式添加数据：</p>
            <div class="space-y-3">
              <button onclick="loadRealData()" class="w-full px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                从后端加载数据
              </button>
              <button onclick="addSampleNode()" class="w-full px-4 py-2 bg-green-600 rounded hover:bg-green-700">
                添加示例节点
              </button>
              <button onclick="importCSVToEditor()" class="w-full px-4 py-2 bg-purple-600 rounded hover:bg-purple-700">
                导入CSV数据
              </button>
            </div>
          </div>
        </div>
      </div>
    `
  }
  
  // 添加功能函数
  ;(window as any).closeVisualEditor = () => {
    editorDiv.remove()
    statusMessage.value = '返回主界面'
    statusColor.value = 'bg-green-500'
  }
  
  ;(window as any).loadGraphData = async () => {
    try {
      const [graphResponse, sidebarResponse, configResponse] = await Promise.all([
        api.editor.getGraphData(),
        api.editor.getSidebarData(domainId),
        api.domain.getDomainConfig(domainId)
      ])
      
      const graphCanvas = editorDiv.querySelector('#graphCanvas')
      if (graphCanvas) {
        graphCanvas.innerHTML = renderGraphElements(graphResponse.elements, configResponse)
        
        // 重新初始化CytoscapeGraph组件
        setTimeout(() => {
          const cytoscapeContainer = editorDiv.querySelector('#cytoscape-container')
          if (cytoscapeContainer && graphResponse.elements?.length > 0) {
            // 先卸载现有的Vue组件
            render(null, cytoscapeContainer)
            
            // 创建CytoscapeGraph虚拟节点
            const vnode = h(CytoscapeGraph, {
              elements: graphResponse.elements,
              'domain-config': configResponse,
              'onNodeClick': (node: any) => {
                console.log('节点点击:', node)
                const propertyPanel = editorDiv.querySelector('#propertyPanel')
                if (propertyPanel) {
                  propertyPanel.innerHTML = `
                    <div class="font-medium mb-2">节点属性</div>
                    <div class="text-xs space-y-1">
                      <div><span class="text-gray-500">ID:</span> ${node.id}</div>
                      <div><span class="text-gray-500">标签:</span> ${node.data?.label || '无'}</div>
                      <div><span class="text-gray-500">类型:</span> ${node.data?.type || '无'}</div>
                      ${node.data?.description ? `<div><span class="text-gray-500">描述:</span> ${node.data.description}</div>` : ''}
                    </div>
                  `
                }
              },
              'onEdgeClick': (edge: any) => {
                console.log('边点击:', edge)
                const propertyPanel = editorDiv.querySelector('#propertyPanel')
                if (propertyPanel) {
                  propertyPanel.innerHTML = `
                    <div class="font-medium mb-2">边属性</div>
                    <div class="text-xs space-y-1">
                      <div><span class="text-gray-500">ID:</span> ${edge.id}</div>
                      <div><span class="text-gray-500">源:</span> ${edge.data?.source || '无'}</div>
                      <div><span class="text-gray-500">目标:</span> ${edge.data?.target || '无'}</div>
                      <div><span class="text-gray-500">关系:</span> ${edge.data?.relationship || '无'}</div>
                      ${edge.data?.description ? `<div><span class="text-gray-500">描述:</span> ${edge.data.description}</div>` : ''}
                    </div>
                  `
                }
              }
            })
            
            // 渲染组件到容器
            render(vnode, cytoscapeContainer)
          }
        }, 100)
      }
      
      // 更新侧边栏
      updateSidebar(sidebarResponse)
      
      // 更新统计
      const statsElement = editorDiv.querySelector('#graphStats')
      if (statsElement) {
        statsElement.textContent = `节点: ${graphResponse.stats?.nodes || 0}, 边: ${graphResponse.stats?.edges || 0}, 对象类型: ${sidebarResponse.object_types?.length || 0}`
      }
      
      notifySuccess('数据刷新成功', '图谱数据已更新')
    } catch (error) {
      notifyError('刷新数据失败', `错误: ${error}`)
    }
  }
  
  ;(window as any).loadRealData = async () => {
    await (window as any).loadGraphData()
  }
  
  function updateSidebar(sidebarData: any) {
    // 更新对象类型
    const objectTypesContainer = editorDiv.querySelector('#objectTypes')
    if (objectTypesContainer && sidebarData.object_types) {
      objectTypesContainer.innerHTML = sidebarData.object_types.map((type: any) => `
        <div class="p-3 bg-gray-700 rounded cursor-move hover:bg-gray-600" 
             draggable="true" 
             data-type="node" 
             data-object-type="${type.name || '未命名'}">
          <div class="font-medium flex items-center justify-between">
            <span>${type.name || '未命名类型'}</span>
            <span class="text-xs px-2 py-1 rounded bg-blue-900 text-blue-300">
              ${type.properties ? Object.keys(type.properties).length : 0} 属性
            </span>
          </div>
          <div class="text-xs text-gray-400 mt-1">${type.description || '无描述'}</div>
        </div>
      `).join('')
    }
    
    // 更新动作规则
    const actionRulesContainer = editorDiv.querySelector('#actionRules')
    if (actionRulesContainer && sidebarData.action_rules) {
      actionRulesContainer.innerHTML = sidebarData.action_rules.map((rule: any) => `
        <div class="p-3 bg-gray-700 rounded hover:bg-gray-600">
          <div class="font-medium">${rule.name || '未命名规则'}</div>
          <div class="text-xs text-gray-400 mt-1">${rule.description || '无描述'}</div>
          <div class="text-xs text-gray-500 mt-2">
            ${rule.source || '?'} → ${rule.target || '?'}
          </div>
        </div>
      `).join('')
    }
    
    // 更新种子数据
    const seedDataContainer = editorDiv.querySelector('#seedData')
    if (seedDataContainer && sidebarData.seed_data) {
      seedDataContainer.innerHTML = sidebarData.seed_data.map((seed: any, index: number) => `
        <div class="p-2 bg-gray-700 rounded text-sm">
          <div class="font-medium">${seed.name || `种子 ${index + 1}`}</div>
          <div class="text-xs text-gray-400">${seed.type || '未知类型'}</div>
        </div>
      `).join('')
    }
  }
  
  ;(window as any).importCSVToEditor = () => {
    notifyInfo('CSV导入', '这将打开文件选择器，您可以选择CSV文件导入到当前领域。')
    // 这里可以调用之前实现的importCSV函数
    const event = new Event('click')
    // 触发CSV导入
    setTimeout(() => {
      const importButton = document.querySelector('button[onclick*="importCSV"]')
      if (importButton) {
        (importButton as HTMLElement).click()
      }
    }, 100)
  }
  
  ;(window as any).addSampleNode = async () => {
    try {
      const node = {
        id: 'node_' + Date.now(),
        label: '示例节点',
        type: 'sample',
        properties: {
          created: new Date().toISOString(),
          source: 'visual_editor'
        }
      }
      
      // 尝试添加节点到图数据库
      const response = await api.editor.addGraphNode(node)
      
      if (response && response.status === 'success') {
        notifySuccess('示例节点已添加', '示例节点已成功添加到图数据库！')
        ;(window as any).loadGraphData()
      } else {
        throw new Error('API返回错误')
      }
      
    } catch (error) {
      console.log('添加节点API失败，使用前端模拟:', error)
      notifyWarning('API不可用', '图数据库API不可用，使用前端模拟模式')
      
      // 如果API失败，在前端添加模拟节点
      const graphCanvas = editorDiv.querySelector('#graphCanvas')
      if (graphCanvas) {
        const sampleHTML = `
          <div class="bg-gray-900 rounded-lg p-4 border border-gray-700 mb-4">
            <div class="font-medium">示例节点 (模拟)</div>
            <div class="text-sm text-gray-400">图数据库API不可用，前端模拟</div>
            <div class="text-xs text-gray-500 mt-2">ID: sample_${Date.now()}</div>
          </div>
        `
        
        if (graphCanvas.innerHTML.includes('text-center')) {
          graphCanvas.innerHTML = sampleHTML
        } else {
          graphCanvas.innerHTML = sampleHTML + graphCanvas.innerHTML
        }
        
        // 更新统计
        const statsElement = editorDiv.querySelector('#graphStats')
        if (statsElement) {
          const currentText = statsElement.textContent || ''
          const match = currentText.match(/节点: (\d+), 边: (\d+)/)
          if (match) {
            const nodes = parseInt(match[1]) + 1
            const edges = parseInt(match[2])
            statsElement.textContent = `节点: ${nodes}, 边: ${edges}`
          }
        }
      }
    }
  }
  
  ;(window as any).clearGraph = async () => {
    const confirmed = await confirm({
      title: '确认清空',
      message: '确定要清空所有图元素吗？此操作不可撤销。',
      confirmText: '清空',
      cancelText: '取消',
      type: 'warning'
    })
    
    if (confirmed) {
      const graphCanvas = editorDiv.querySelector('#graphCanvas')
      if (graphCanvas) {
        graphCanvas.innerHTML = renderEmptyGraph()
        notifySuccess('已清空', '所有图元素已清空')
      }
    }
  }
  
  ;(window as any).validateGraph = async () => {
    try {
      const response = await api.ontology.checkIntegrity()
      if (response.status === 'success') {
        notifySuccess('验证完成', response.message || '本体完整性检查通过')
      } else if (response.status === 'warning') {
        notifyWarning('验证警告', `${response.message || '发现一些问题'}\n\n错误: ${JSON.stringify(response.errors, null, 2)}`)
      } else {
        notifyError('验证失败', response.message || '未知错误')
      }
    } catch (error) {
      notifyError('验证失败', `错误: ${error}`)
    }
  }
  
  ;(window as any).saveVisualEditor = async (domainId: string) => {
    try {
      // 获取当前领域配置
      const domainConfig = await api.domain.getDomainConfig(domainId)
      
      // 创建简单的本体配置
      const ontology = {
        name: `可视化编辑_${new Date().toISOString().split('T')[0]}`,
        description: '通过可视化编辑器创建的本体',
        version: '1.0.0',
        createdAt: new Date().toISOString(),
        objectTypes: [
          {
            name: 'VisualNode',
            description: '可视化节点',
            properties: {
              label: { type: 'string', description: '节点标签' },
              type: { type: 'string', description: '节点类型' }
            }
          }
        ],
        relationships: [],
        rules: []
      }
      
      // 保存到领域
      await api.upload.saveOntologyToDomain(domainId, ontology)
      
      notifySuccess('本体保存成功', `已保存到领域: ${domainId}\n\n现在可以在以下位置使用：\n1. E:\\Documents\\MyGame\\genesis\n2. E:\\Documents\\MyGame\\applications\n3. 其他业务系统`)
      
      editorDiv.remove()
      statusMessage.value = '已保存到图数据库'
      statusColor.value = 'bg-green-500'
      
    } catch (error) {
      notifyError('保存失败', `错误: ${error}\n\n尝试使用备用保存方法...`)
      
      // 尝试HTMX保存
      try {
        const response = await api.editor.save({
          type: 'ontology',
          content: '可视化编辑器生成的本体',
          domain: domainId
        })
        
        if (response.success) {
          notifySuccess('保存成功', '本体已成功保存')
          editorDiv.remove()
          statusMessage.value = '保存成功'
          statusColor.value = 'bg-green-500'
        } else {
          throw new Error('HTMX保存也失败')
        }
      } catch (htmxError) {
        notifyError('所有保存方法都失败', '请检查后端服务是否正常运行')
      }
    }
  }
  
  // 添加拖拽功能
  setTimeout(() => {
    const draggables = editorDiv.querySelectorAll('[draggable="true"]')
    const dropZone = editorDiv.querySelector('#graphCanvas')
    
    draggables.forEach(item => {
      item.addEventListener('dragstart', (e) => {
        const target = e.target as HTMLElement
        const objectType = target.dataset.objectType || '未知类型'
        e.dataTransfer?.setData('text/plain', objectType)
      })
    })
    
    if (dropZone) {
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault()
        ;(dropZone as HTMLElement).style.backgroundColor = '#374151'
      })
      
      dropZone.addEventListener('dragleave', () => {
        ;(dropZone as HTMLElement).style.backgroundColor = ''
      })
      
      dropZone.addEventListener('drop', (e) => {
        e.preventDefault()
        ;(dropZone as HTMLElement).style.backgroundColor = ''
        
        const objectType = e.dataTransfer?.getData('text/plain')
        if (objectType) {
          // 不显示通知，因为后面会显示成功通知
          
        // 在前端添加节点显示
        const nodeHTML = `
          <div class="bg-gray-900 rounded-lg p-4 border border-gray-700 mb-4">
            <div class="font-medium">${objectType}</div>
            <div class="text-sm text-gray-400">拖拽创建的节点</div>
            <div class="text-xs text-gray-500 mt-2">ID: ${objectType.toLowerCase()}_${Date.now()}</div>
          </div>
        `
        
        if (dropZone.innerHTML.includes('text-center')) {
          dropZone.innerHTML = nodeHTML
        } else {
          dropZone.innerHTML = nodeHTML + dropZone.innerHTML
        }
        
        notifySuccess('节点创建成功', `已创建 ${objectType} 节点`)
        }
      })
    }
  }, 100)
  
    // 初始化CytoscapeGraph组件
    setTimeout(() => {
      const cytoscapeContainer = editorDiv.querySelector('#cytoscape-container')
      if (cytoscapeContainer && graphData?.elements?.length > 0) {
        // 创建CytoscapeGraph虚拟节点
        const vnode = h(CytoscapeGraph, {
          elements: graphData.elements,
          'domain-config': domainConfig,
          'onNodeClick': (node: any) => {
            console.log('节点点击:', node)
            const propertyPanel = editorDiv.querySelector('#propertyPanel')
            if (propertyPanel) {
              propertyPanel.innerHTML = `
                <div class="font-medium mb-2">节点属性</div>
                <div class="text-xs space-y-1">
                  <div><span class="text-gray-500">ID:</span> ${node.id}</div>
                  <div><span class="text-gray-500">标签:</span> ${node.data?.label || '无'}</div>
                  <div><span class="text-gray-500">类型:</span> ${node.data?.type || '无'}</div>
                  ${node.data?.description ? `<div><span class="text-gray-500">描述:</span> ${node.data.description}</div>` : ''}
                </div>
              `
            }
          },
          'onEdgeClick': (edge: any) => {
            console.log('边点击:', edge)
            const propertyPanel = editorDiv.querySelector('#propertyPanel')
            if (propertyPanel) {
              propertyPanel.innerHTML = `
                <div class="font-medium mb-2">边属性</div>
                <div class="text-xs space-y-1">
                  <div><span class="text-gray-500">ID:</span> ${edge.id}</div>
                  <div><span class="text-gray-500">源:</span> ${edge.data?.source || '无'}</div>
                  <div><span class="text-gray-500">目标:</span> ${edge.data?.target || '无'}</div>
                  <div><span class="text-gray-500">关系:</span> ${edge.data?.relationship || '无'}</div>
                  ${edge.data?.description ? `<div><span class="text-gray-500">描述:</span> ${edge.data.description}</div>` : ''}
                </div>
              `
            }
          },
          'onNodeAdd': (node: any) => {
            console.log('添加节点:', node)
            notifySuccess('节点添加成功', `已添加节点: ${node.data?.label || node.id}`)
          },
          'onEdgeAdd': (edge: any) => {
            console.log('添加边:', edge)
            notifySuccess('边添加成功', `已添加边: ${edge.data?.source} → ${edge.data?.target}`)
          },
          'onNodeDelete': (nodeId: string) => {
            console.log('删除节点:', nodeId)
            notifySuccess('节点删除成功', `已删除节点: ${nodeId}`)
          },
          'onEdgeDelete': (edgeId: string) => {
            console.log('删除边:', edgeId)
            notifySuccess('边删除成功', `已删除边: ${edgeId}`)
          }
        })
        
        // 渲染组件到容器
        render(vnode, cytoscapeContainer)
      }
    }, 200)
  
  statusMessage.value = '可视化编辑器已打开'
  statusColor.value = 'bg-green-500'
}

// 选择领域
const selectDomain = async (domain: any) => {
  selectedDomainId.value = domain.id
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