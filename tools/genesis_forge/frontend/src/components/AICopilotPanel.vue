<template>
  <div class="h-full flex flex-col bg-gray-900 border-l border-gray-700">
    <!-- 标题栏 -->
    <div class="px-4 py-3 border-b border-gray-700 bg-gray-800">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <i class="fas fa-robot text-white"></i>
          </div>
          <div>
            <h3 class="font-bold text-lg">AI Copilot</h3>
            <div class="flex items-center space-x-2 mt-1">
              <div class="flex items-center space-x-1">
                <div :class="['w-2 h-2 rounded-full', isConnected ? 'bg-green-500' : 'bg-red-500']"></div>
                <span class="text-xs text-gray-400">
                  {{ isConnected ? '已连接' : '连接中...' }}
                </span>
              </div>
              <span class="text-xs text-gray-400">•</span>
              <span class="text-xs text-gray-400">
                {{ messages.length }} 条消息
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <button @click="clearHistory" 
                  class="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded flex items-center space-x-1"
                  title="清空历史">
            <i class="fas fa-trash"></i>
            <span>清空</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 消息区域 -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-6">
      <!-- CSV导入区域 -->
      <div v-if="messages.length === 0" class="p-6">
        <div class="bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 mb-8">
          <div class="flex items-center space-x-3 mb-4">
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <i class="fas fa-file-csv text-white text-xl"></i>
            </div>
            <div>
              <h4 class="text-lg font-semibold">CSV数据导入</h4>
              <p class="text-gray-400 text-sm">上传CSV文件，AI自动分析并转换为本体结构</p>
            </div>
          </div>
          
          <!-- 文件上传区域 -->
          <div class="mb-4">
            <div @click="triggerFileInput" 
                 class="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors">
              <i class="fas fa-cloud-upload-alt text-3xl text-gray-500 mb-3"></i>
              <p class="text-gray-400 mb-2">点击或拖拽CSV文件到这里</p>
              <p class="text-gray-500 text-sm">支持 .csv 格式，最大 10MB</p>
            </div>
            <input ref="fileInput" type="file" accept=".csv" @change="handleFileSelect" class="hidden" />
            
            <!-- 文件信息 -->
            <div v-if="csvFile" class="mt-4 p-4 bg-gray-800 rounded-lg">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <i class="fas fa-file-csv text-blue-400 text-xl"></i>
                  <div>
                    <p class="font-medium">{{ csvFile.name }}</p>
                    <p class="text-gray-400 text-sm">{{ (csvFile.size / 1024).toFixed(1) }} KB</p>
                  </div>
                </div>
                <button @click="removeFile" class="text-gray-400 hover:text-red-400">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>
          
          <!-- 领域选择 -->
          <div class="mb-6">
            <label class="block text-sm font-medium mb-2">目标领域</label>
            <div class="flex space-x-2">
              <input v-model="csvDomainName" 
                     type="text" 
                     placeholder="输入新领域名称（如：供应链ERP）"
                     class="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button @click="suggestDomainName" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">
                <i class="fas fa-lightbulb"></i>
              </button>
            </div>
            <p class="text-gray-500 text-sm mt-2">AI将根据CSV内容创建新的领域配置</p>
          </div>
          
          <!-- 操作按钮 -->
          <div class="flex space-x-3">
            <button @click="analyzeCSV" 
                    :disabled="!csvFile || !csvDomainName.trim()"
                    :class="['flex-1 py-3 rounded-lg font-medium flex items-center justify-center space-x-2',
                            !csvFile || !csvDomainName.trim() ? 'bg-gray-700 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:opacity-90']">
              <i class="fas fa-brain"></i>
              <span>AI分析CSV</span>
            </button>
            <button @click="showCSVPreview" 
                    :disabled="!csvFile"
                    :class="['px-4 py-3 rounded-lg', !csvFile ? 'bg-gray-700 cursor-not-allowed' : 'bg-gray-700 hover:bg-gray-600']">
              <i class="fas fa-eye"></i>
            </button>
          </div>
        </div>
        
        <!-- AI功能卡片 -->
        <div class="text-center mb-8">
          <h4 class="text-lg font-semibold mb-4">或者使用其他AI功能</h4>
          <div class="grid grid-cols-2 gap-3">
            <div @click="askQuestion('帮我创建一个采购订单对象类型定义')"
                 class="bg-gray-800 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-700 transition-colors">
              <i class="fas fa-cube text-blue-400 text-xl mb-2"></i>
              <p class="text-sm">生成对象类型</p>
            </div>
            <div @click="askQuestion('生成一个查询所有采购订单的Cypher语句')"
                 class="bg-gray-800 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-700 transition-colors">
              <i class="fas fa-code text-green-400 text-xl mb-2"></i>
              <p class="text-sm">Cypher查询</p>
            </div>
            <div @click="askQuestion('优化这段XML代码的性能和可读性')"
                 class="bg-gray-800 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-700 transition-colors">
              <i class="fas fa-magic text-purple-400 text-xl mb-2"></i>
              <p class="text-sm">优化代码</p>
            </div>
            <div @click="askQuestion('解释供应链ERP领域的主要概念和关系')"
                 class="bg-gray-800 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-700 transition-colors">
              <i class="fas fa-book text-yellow-400 text-xl mb-2"></i>
              <p class="text-sm">领域解释</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="message in messages" :key="message.id" 
           :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']">
        <div :class="['max-w-[85%] rounded-xl p-4', 
                     message.role === 'user' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 
                     message.isCode ? 'bg-gray-800 border border-gray-700' : 'bg-gray-800']">
          
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <div class="w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center">
                  <i class="fas fa-user text-xs"></i>
                </div>
                <span class="font-medium">您</span>
              </div>
              <span class="text-xs opacity-70">{{ message.timestamp }}</span>
            </div>
            <div class="whitespace-pre-wrap">{{ message.content }}</div>
          </div>

          <!-- AI消息 -->
          <div v-else>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <i class="fas fa-robot text-xs"></i>
                </div>
                <div>
                  <span class="font-medium">AI Copilot</span>
                  <div v-if="!message.isComplete" class="flex items-center space-x-1 mt-1">
                    <div class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
                    <div class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                    <div class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
                  </div>
                </div>
              </div>
              <span class="text-xs opacity-70">{{ message.timestamp }}</span>
            </div>

            <!-- 普通文本消息 -->
            <div v-if="!message.isCode" class="whitespace-pre-wrap">{{ message.content }}</div>

            <!-- 代码建议 -->
            <div v-else class="mt-2">
              <div class="flex items-center justify-between mb-2 px-1">
                <div class="flex items-center space-x-2">
                  <span class="text-xs font-mono px-2 py-1 bg-gray-900 rounded">
                    {{ message.language?.toUpperCase() || 'CODE' }}
                  </span>
                  <span class="text-xs text-gray-400">代码建议</span>
                </div>
                <button @click="applyCodeSuggestion(message.content, message.language)"
                        class="text-sm text-blue-400 hover:text-blue-300 flex items-center space-x-1">
                  <i class="fas fa-code"></i>
                  <span>应用到编辑器</span>
                </button>
              </div>
              <pre class="bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto font-mono border border-gray-700">{{ message.content }}</pre>
              
              <!-- 代码操作按钮 -->
              <div v-if="message.action" class="mt-3 flex space-x-2">
                <button @click="executeCodeAction(message.action, message.content)"
                        class="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 rounded">
                  <i class="fas fa-play mr-1"></i>执行
                </button>
                <button @click="copyToClipboard(message.content)"
                        class="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded">
                  <i class="fas fa-copy mr-1"></i>复制
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="isLoading && (!messages.length || messages[messages.length - 1].role !== 'assistant' || messages[messages.length - 1].isComplete)"
           class="flex justify-start">
        <div class="max-w-[85%] rounded-xl p-4 bg-gray-800">
          <div class="flex items-center space-x-3">
            <div class="w-6 h-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <i class="fas fa-robot text-xs"></i>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
              <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="border-t border-gray-700 p-4 bg-gray-800">
      <!-- 快捷指令 -->
      <div class="mb-3 flex flex-wrap gap-2">
        <button v-for="suggestion in quickSuggestions" :key="suggestion.text"
                @click="inputText = suggestion.text"
                class="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center space-x-2">
          <i :class="suggestion.icon"></i>
          <span>{{ suggestion.label }}</span>
        </button>
      </div>

      <div class="flex space-x-3">
        <div class="flex-1 relative">
          <textarea v-model="inputText"
                    @keydown.enter.exact.prevent="sendMessage"
                    placeholder="输入您的问题或指令... (Shift+Enter换行)"
                    :disabled="isLoading"
                    rows="3"
                    class="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-50"></textarea>
          
          <div class="absolute bottom-2 right-2 flex items-center space-x-3">
            <div class="text-xs text-gray-400">
              <span v-if="!isConnected" class="text-yellow-400">
                <i class="fas fa-unlink mr-1"></i>连接中...
              </span>
              <span v-else class="text-green-400">
                <i class="fas fa-link mr-1"></i>已连接
              </span>
            </div>
            <div class="text-xs text-gray-400">
              {{ inputText.length }}/1000
            </div>
          </div>
        </div>
        
        <div class="flex flex-col space-y-2">
          <button @click="sendMessage"
                  :disabled="!inputText.trim() || isLoading"
                  :class="['px-4 py-3 rounded-lg font-medium flex items-center justify-center space-x-2',
                          !inputText.trim() || isLoading ? 'bg-gray-700 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:opacity-90']"
                  title="发送消息 (Enter)">
            <i class="fas fa-paper-plane"></i>
            <span>发送</span>
          </button>
          

        </div>
      </div>

      <!-- 提示信息 -->
      <div class="mt-3 text-xs text-gray-400 flex items-center justify-between">
        <div>
          <span class="mr-3"><i class="fas fa-keyboard mr-1"></i>Enter发送</span>
          <span><i class="fas fa-shift mr-1"></i>Shift+Enter换行</span>
        </div>
        <div>
          <span><i class="fas fa-bolt mr-1"></i>Ctrl+Shift+C打开</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import api from '../utils/api'
import { useToast } from '../utils/notify'

const props = defineProps<{
  domain?: string
  currentFile?: string
  editorContent?: string
}>()

const emit = defineEmits<{
  applyCode: [code: string, language: string]
  executeAction: [action: string, data: any]
}>()

// 响应式状态
const messages = ref<Array<{
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  isComplete: boolean
  isCode?: boolean
  language?: string
  action?: string
}>>([])
const inputText = ref('')
const isLoading = ref(false)
const isConnected = ref(false)
const messagesContainer = ref<HTMLElement>()
const eventSource = ref<EventSource | null>(null)

// CSV导入相关状态
const csvFile = ref<File | null>(null)
const csvDomainName = ref('')
const fileInput = ref<HTMLInputElement>()
const isAnalyzingCSV = ref(false)

// 快捷建议
const quickSuggestions = ref([
  { label: '创建对象类型', text: '帮我创建一个采购订单对象类型定义', icon: 'fas fa-cube' },
  { label: 'Cypher查询', text: '生成一个查询所有采购订单的Cypher语句', icon: 'fas fa-code' },
  { label: '优化代码', text: '优化这段XML代码的性能和可读性', icon: 'fas fa-magic' },
  { label: '领域解释', text: '解释供应链ERP领域的主要概念和关系', icon: 'fas fa-book' },
  { label: '验证规则', text: '帮我创建一个订单金额验证规则', icon: 'fas fa-check-circle' }
])

// CSV导入相关函数
const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    csvFile.value = input.files[0]
    // 使用文件名作为默认领域名
    if (!csvDomainName.value.trim()) {
      csvDomainName.value = csvFile.value.name
        .replace('.csv', '')
        .replace(/[_-]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
    }
  }
}

const removeFile = () => {
  csvFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const suggestDomainName = () => {
  if (csvFile.value) {
    const name = csvFile.value.name
      .replace('.csv', '')
      .replace(/[_-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
    csvDomainName.value = name
  } else {
    csvDomainName.value = '新业务领域'
  }
}

const analyzeCSV = async () => {
  if (!csvFile.value || !csvDomainName.value.trim() || isAnalyzingCSV.value) return
  
  isAnalyzingCSV.value = true
  
  try {
    // 添加用户消息
    addMessage({
      role: 'user',
      content: `请分析CSV文件: ${csvFile.value.name}\n领域名称: ${csvDomainName.value}`,
      isComplete: true
    })
    
    // 读取CSV内容
    const text = await csvFile.value.text()
    const lines = text.split('\n').slice(0, 10) // 只取前10行作为示例
    
    // 发送到AI分析
    const userMessage = `请分析以下CSV数据并转换为本体结构：
文件: ${csvFile.value.name}
领域: ${csvDomainName.value}

CSV内容（前10行）:
${lines.join('\n')}

请：
1. 识别实体类型和属性
2. 建议关系类型
3. 生成XML格式的本体定义
4. 提供导入到图数据库的建议`
    
    inputText.value = userMessage
    await sendMessage()
    
    // 清空文件
    removeFile()
    csvDomainName.value = ''
    
  } catch (error) {
    console.error('CSV分析失败:', error)
    useToast().error('CSV分析失败')
  } finally {
    isAnalyzingCSV.value = false
  }
}

const showCSVPreview = () => {
  if (!csvFile.value) return
  
  // 这里可以添加CSV预览功能
  useToast().info('CSV预览功能开发中')
}

const askQuestion = (question: string) => {
  inputText.value = question
  sendMessage()
}

// 初始化
onMounted(() => {
  loadHistory()
  connectSSE()
  setupKeyboardShortcuts()
  
  // 如果没有历史消息，添加欢迎消息
  if (messages.value.length === 0) {
    addWelcomeMessage()
  }
})

// 清理
onUnmounted(() => {
  if (eventSource.value) {
    eventSource.value.close()
  }
})

// 连接SSE
const connectSSE = (message?: string) => {
  if (eventSource.value) {
    eventSource.value.close()
  }

  // 构建URL，可选包含消息参数
  let url = '/api/copilot/stream'
  if (message) {
    const sessionId = Date.now().toString() // 简单的会话ID
    url += `?message=${encodeURIComponent(message)}&session_id=${sessionId}`
    console.log('通过SSE发送消息:', message)
  }

  eventSource.value = new EventSource(url)

  eventSource.value.onopen = () => {
    isConnected.value = true
    console.log('SSE连接已建立', message ? '(带消息)' : '(心跳模式)')
  }

  eventSource.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleSSEMessage(data)
    } catch (error) {
      console.error('解析SSE消息失败:', error)
    }
  }

  eventSource.value.onerror = (error) => {
    console.error('SSE连接错误:', error)
    isConnected.value = false
    
    // 尝试重新连接
    setTimeout(() => {
      if (!isConnected.value) {
        connectSSE()
      }
    }, 3000)
  }
}

// 处理SSE消息
const handleSSEMessage = (data: any) => {
  console.log('收到SSE消息:', data.type, data)
  
  if (data.type === 'connected') {
    // 连接确认
    console.log('SSE连接确认:', data.message)
    // 不显示给用户，只用于调试
  } else if (data.type === 'heartbeat') {
    // 心跳消息，保持连接活跃
    console.log('SSE心跳:', data.timestamp)
    // 不显示给用户
  } else if (data.type === 'test') {
    // 测试消息，不显示给用户
    console.log('SSE测试消息:', data.content)
  } else if (data.type === 'chunk') {
    // 流式文本块
    appendToLastMessage(data.content)
  } else if (data.type === 'complete') {
    // 消息完成
    isLoading.value = false
    markLastMessageComplete()
  } else if (data.type === 'error') {
    // 错误消息
    addMessage({
      role: 'assistant',
      content: `错误: ${data.message}`,
      isComplete: true
    })
    isLoading.value = false
  } else if (data.type === 'code_suggestion') {
    // 代码建议
    addMessage({
      role: 'assistant',
      content: data.content,
      isComplete: true,
      isCode: true,
      language: data.language || 'cypher',
      action: data.action
    })
    isLoading.value = false
  } else if (data.type === 'suggestion') {
    // 普通建议
    addMessage({
      role: 'assistant',
      content: data.content,
      isComplete: true
    })
    isLoading.value = false
  }
}

// 添加消息
const addMessage = (message: {
  role: 'user' | 'assistant'
  content: string
  isComplete: boolean
  isCode?: boolean
  language?: string
  action?: string
}) => {
  messages.value.push({
    ...message,
    id: Date.now(),
    timestamp: new Date().toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  })
  
  // 滚动到底部
  scrollToBottom()
  
  // 保存到本地存储
  saveHistory()
}

// 追加到最后一条消息
const appendToLastMessage = (content: string) => {
  if (messages.value.length === 0) {
    addMessage({
      role: 'assistant',
      content: content,
      isComplete: false
    })
    return
  }
  
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage.role === 'assistant' && !lastMessage.isComplete) {
    lastMessage.content += content
    
    // 触发UI更新
    messages.value = [...messages.value]
  } else {
    addMessage({
      role: 'assistant',
      content: content,
      isComplete: false
    })
  }
}

// 标记最后一条消息完成
const markLastMessageComplete = () => {
  if (messages.value.length > 0) {
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage.role === 'assistant') {
      lastMessage.isComplete = true
      messages.value = [...messages.value]
      saveHistory()
    }
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value) return
  
  const userMessage = inputText.value.trim()
  
  // 添加用户消息
  addMessage({
    role: 'user',
    content: userMessage,
    isComplete: true
  })
  
  inputText.value = ''
  isLoading.value = true
  
  try {
    // 通过SSE发送消息（重新建立连接并传递消息参数）
    connectSSE(userMessage)
    
    // 等待SSE流式响应
    // 响应将通过handleSSEMessage处理
    
  } catch (error) {
    console.error('发送消息失败:', error)
    addMessage({
      role: 'assistant',
      content: '抱歉，发送消息时出现错误。请检查网络连接或稍后重试。',
      isComplete: true
    })
    isLoading.value = false
  }
}

// 获取上下文
const getContext = () => {
  const context: any = {
    domain: props.domain || 'supply_chain',
    currentFile: props.currentFile || '未选择文件',
    timestamp: new Date().toISOString(),
    platform: 'vue_frontend'
  }
  
  // 如果有编辑器内容
  if (props.editorContent) {
    context.editorContent = props.editorContent.substring(0, 5000) // 限制长度
  }
  
  return context
}

// 应用代码建议
const applyCodeSuggestion = (code: string, language?: string) => {
  emit('applyCode', code, language || 'text')
  useToast().success('代码已准备应用到编辑器')
}

// 执行代码操作
const executeCodeAction = (action: string, data: any) => {
  emit('executeAction', action, data)
}

// 复制到剪贴板
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    useToast().success('代码已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    useToast().error('复制失败')
  }
}



// 加载历史记录
const loadHistory = () => {
  try {
    const saved = localStorage.getItem('copilot_history_vue')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed)) {
        messages.value = parsed
      }
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

// 保存历史记录
const saveHistory = () => {
  try {
    // 只保存最近50条消息
    const recentMessages = messages.value.slice(-50)
    localStorage.setItem('copilot_history_vue', JSON.stringify(recentMessages))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

// 清空历史
const clearHistory = () => {
  if (confirm('确定要清空对话历史吗？此操作不可撤销。')) {
    messages.value = []
    localStorage.removeItem('copilot_history_vue')
    addWelcomeMessage()
    useToast().success('对话历史已清空')
  }
}

// 添加欢迎消息
const addWelcomeMessage = () => {
  // 现在CSV导入区域已经显示了欢迎信息，所以不需要额外的欢迎消息
  // 只有在有历史消息时才显示
  if (messages.value.length > 0) {
    addMessage({
      role: 'assistant',
      content: `👋 欢迎回来！我可以继续帮助您分析数据、生成代码或优化本体结构。`,
      isComplete: true
    })
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 设置键盘快捷键
const setupKeyboardShortcuts = () => {
  const handleKeyDown = (event: KeyboardEvent) => {
    // Ctrl+Shift+C 打开/关闭Copilot（由父组件处理）
    if (event.ctrlKey && event.shiftKey && event.key === 'C') {
      event.preventDefault()
      // 父组件会处理显示/隐藏
    }
    
    // Esc 关闭输入框
    if (event.key === 'Escape' && document.activeElement?.tagName === 'TEXTAREA') {
      ;(document.activeElement as HTMLTextAreaElement).blur()
    }
  }
  
  window.addEventListener('keydown', handleKeyDown)
  
  // 清理
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })
}

// 监听消息变化，自动滚动
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 暴露方法给父组件
defineExpose({
  askQuestion: (question: string) => {
    inputText.value = question
    sendMessage()
  },
  clearHistory,
  getMessages: () => messages.value
})
</script>

<style scoped>
/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #1f2937;
}

::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}

/* 消息动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.flex > div {
  animation: fadeIn 0.3s ease-out;
}

/* 代码块样式 */
pre {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  line-height: 1.5;
  tab-size: 2;
}

/* 加载动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>