<template>
  <div class="fixed inset-0 bg-gray-900 z-50 flex flex-col">
    <!-- 顶部标题栏 -->
    <div class="bg-gray-800 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
      <div>
        <h2 class="text-xl font-bold">可视化本体编辑器</h2>
        <div class="text-sm text-gray-400">领域: {{ domain?.name || '未命名领域' }}</div>
      </div>
      <div class="flex space-x-3">
        <button @click="loadGraphData" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
          刷新数据
        </button>
        <button @click="closeEditor" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
          返回主界面
        </button>
      </div>
    </div>

    <!-- 主编辑器区域 -->
    <div class="flex-1 flex">
      <!-- 左侧边栏（可调整宽度） -->
      <ResizablePanel 
        :default-width="256" 
        :min-width="180" 
        :max-width="600"
        storage-key="visual_editor_sidebar_width"
        position="left"
        class="bg-gray-800 border-r border-gray-700 overflow-y-auto"
      >
        <div class="p-4 h-full overflow-y-auto">
          <h3 class="font-semibold mb-4">对象类型 ({{ sidebarData?.object_types?.length || 0 }})</h3>
          <div id="objectTypes" class="space-y-2 mb-6 max-h-60 overflow-y-auto">
            <div v-if="sidebarData?.object_types?.length > 0">
              <div 
                v-for="type in sidebarData.object_types" 
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
          
          <h3 class="font-semibold mb-4">动作规则 ({{ sidebarData?.action_rules?.length || 0 }})</h3>
          <div id="actionRules" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            <div v-if="sidebarData?.action_rules?.length > 0">
              <div 
                v-for="rule in sidebarData.action_rules" 
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
          
          <h3 class="font-semibold mb-4">种子数据 ({{ sidebarData?.seed_data?.length || 0 }})</h3>
          <div id="seedData" class="space-y-2 mb-6 max-h-40 overflow-y-auto">
            <div v-if="sidebarData?.seed_data?.length > 0">
              <div 
                v-for="(seed, index) in sidebarData.seed_data" 
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
      </ResizablePanel>
      
      <!-- 中间图谱视图 -->
      <div class="flex-1 p-4">
        <div class="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
          <div class="p-4 border-b border-gray-700">
            <h3 class="font-semibold">图谱视图</h3>
          </div>
          <div class="flex-1 p-4 overflow-auto">
            <CytoscapeGraph 
              v-if="graphData"
              :elements="graphData.elements || []"
              :domain-config="domainConfig"
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
                <p class="text-lg mb-2">{{ domain?.name || '领域' }} 的可视化编辑器</p>
                <p class="text-gray-400 mb-4">当前领域没有图谱数据</p>
                <p class="text-sm text-gray-500 mb-6">您可以通过以下方式添加数据：</p>
                <div class="space-y-3">
                  <button @click="loadRealData" class="w-full px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                    从后端加载数据
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

      <!-- 右侧属性编辑面板（可调整宽度） -->
      <ResizablePanel 
        v-show="showPropertyPanel"
        :default-width="320" 
        :min-width="200" 
        :max-width="800"
        storage-key="visual_editor_property_panel_width"
        position="right"
        class="bg-gray-800 border-l border-gray-700 overflow-y-auto"
      >
        <div class="p-4 h-full overflow-y-auto">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-semibold">属性编辑</h3>
            <button @click="closePropertyPanel" class="text-gray-400 hover:text-white">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          <div v-if="selectedElement">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">ID</label>
              <input 
                v-model="selectedElement.id" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" 
                readonly
              >
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">标签</label>
              <input 
                v-model="selectedElement.label" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">类型</label>
              <input 
                v-model="selectedElement.type" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
            </div>
            <div v-if="selectedElement.elementType === 'edge'" class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">源节点</label>
              <input 
                v-model="selectedElement.source" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
            </div>
            <div v-if="selectedElement.elementType === 'edge'" class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">目标节点</label>
              <input 
                v-model="selectedElement.target" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-1">属性</label>
              <div class="bg-gray-900 rounded p-3 max-h-40 overflow-y-auto">
                <div v-if="Object.keys(selectedElement.properties || {}).length === 0" class="text-gray-400 text-sm">
                  无属性
                </div>
                <div v-else>
                  <div 
                    v-for="(value, key) in selectedElement.properties" 
                    :key="key"
                    class="mb-2"
                  >
                    <label class="text-xs text-gray-400">{{ key }}</label>
                    <input 
                      v-model="selectedElement.properties[key]" 
                      type="text" 
                      class="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
                    >
                  </div>
                </div>
              </div>
            </div>
            <div class="flex justify-end space-x-3">
              <button 
                @click="saveElementProperties" 
                class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
              >
                保存
              </button>
              <button 
                @click="closePropertyPanel" 
                class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
          <div v-else class="text-gray-400 text-sm">
            选择元素以编辑属性
          </div>
        </div>
      </ResizablePanel>
    </div>

    <!-- 底部状态栏 -->
    <div class="bg-gray-800 px-6 py-3 border-t border-gray-700">
      <div class="flex justify-between items-center text-sm">
        <div>
          <span id="graphStats">
            {{ graphData ? `节点: ${graphData.stats?.nodes || 0}, 边: ${graphData.stats?.edges || 0}` : '就绪 | 拖拽模式' }}
          </span>
        </div>
        <div class="flex space-x-3">
          <button @click="validateGraph" class="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700">
            验证
          </button>
          <button @click="saveVisualEditor" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
            保存到图数据库
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CytoscapeGraph from './CytoscapeGraph.vue'
import ResizablePanel from './layout/ResizablePanel.vue'
import api from '../utils/api'
import notify, { notifySuccess, notifyError, notifyWarning, notifyInfo, confirm } from '../utils/notify'

// Props
const props = defineProps<{
  domain: any
}>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// 响应式状态
const sidebarData = ref<any>(null)
const graphData = ref<any>(null)
const domainConfig = ref<any>(null)
const showPropertyPanel = ref(false)
const selectedElement = ref<any>(null)

// 关闭编辑器
const closeEditor = () => {
  emit('close')
}

// 加载图谱数据
const loadGraphData = async () => {
  try {
    const [graphResponse, sidebarResponse, configResponse] = await Promise.all([
      api.editor.getGraphData(props.domain?.id),
      api.editor.getSidebarData(props.domain?.id),
      api.domain.getDomainConfig(props.domain?.id)
    ])
    
    // 更新数据
    graphData.value = graphResponse
    sidebarData.value = sidebarResponse
    domainConfig.value = configResponse
    
    notifySuccess('数据刷新成功', '图谱数据已更新')
    
  } catch (error) {
    console.error('加载图谱数据失败:', error)
    notifyError('数据刷新失败', `错误: ${error}`)
  }
}

// 加载真实数据
const loadRealData = async () => {
  try {
    const response = await api.editor.getGraphData(props.domain?.id)
    graphData.value = response
    notifySuccess('数据加载成功', `已加载 ${response.elements?.length || 0} 个元素`)
  } catch (error) {
    console.error('加载真实数据失败:', error)
    notifyError('数据加载失败', `错误: ${error}`)
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
const saveVisualEditor = async () => {
  try {
    console.log('保存按钮点击，领域ID:', props.domain?.id)
    
    // 检查是否有图数据
    if (!graphData.value?.elements || graphData.value.elements.length === 0) {
      notifyWarning('没有数据可保存', '请在保存前添加一些节点和关系')
      return
    }
    
    // 获取当前领域配置
    const domainConfig = await api.domain.getDomainConfig(props.domain?.id)
    console.log('领域配置获取成功')
    
    // 从图数据生成本体结构
    const elements = graphData.value.elements
    const nodes = elements.filter(el => !el.data?.source && !el.data?.target)
    const edges = elements.filter(el => el.data?.source && el.data?.target)
    
    console.log('生成本体:', { nodes: nodes.length, edges: edges.length })
    
    // 提取唯一的节点类型作为对象类型
    const nodeTypeMap = new Map()
    nodes.forEach(node => {
      const nodeType = node.data?.type || 'Unknown'
      if (!nodeTypeMap.has(nodeType)) {
        nodeTypeMap.set(nodeType, {
          name: nodeType,
          description: `通过可视化编辑器创建的 ${nodeType} 类型`,
          properties: {
            label: { type: 'string', description: '节点标签' },
            type: { type: 'string', description: '节点类型' },
            ...(node.data?.properties || {})
          }
        })
      }
    })
    
    // 提取唯一的关系类型
    const relationshipTypeMap = new Map()
    edges.forEach(edge => {
      const edgeType = edge.data?.type || 'RELATES_TO'
      if (!relationshipTypeMap.has(edgeType)) {
        relationshipTypeMap.set(edgeType, {
          name: edgeType,
          description: `通过可视化编辑器创建的 ${edgeType} 关系`,
          sourceType: 'Unknown',
          targetType: 'Unknown',
          properties: {
            ...(edge.data?.properties || {})
          }
        })
      }
    })
    
    // 创建本体配置
    const ontology = {
      name: `可视化编辑_${props.domain?.id}_${new Date().toISOString().split('T')[0]}`,
      description: `通过可视化编辑器创建的 ${props.domain?.id} 领域本体`,
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      objectTypes: Array.from(nodeTypeMap.values()),
      relationships: Array.from(relationshipTypeMap.values()),
      rules: [],
      // 包含种子数据（实际节点实例）
      seedData: {
        entities: nodes.map(node => ({
          id: node.id,
          type: node.data?.type || 'Unknown',
          properties: {
            label: node.data?.label || node.id,
            type: node.data?.type || 'Unknown',
            ...(node.data?.properties || {})
          }
        })),
        relations: edges.map(edge => ({
          id: edge.id,
          type: edge.data?.type || 'RELATES_TO',
          source: edge.data?.source,
          target: edge.data?.target,
          properties: {
            label: edge.data?.label || edge.id,
            ...(edge.data?.properties || {})
          }
        }))
      }
    }
    
    console.log('生成的本体:', ontology)
    
    // 保存到领域
    await api.upload.saveOntologyToDomain(props.domain?.id, ontology)
    
    notifySuccess('本体保存成功', `已保存到领域: ${props.domain?.id}\n\n现在可以在以下位置使用：\n1. E:\\Documents\\MyGame\\genesis\n2. E:\\Documents\\MyGame\\applications\n3. 其他业务系统`)
    
    closeEditor()
    
  } catch (error) {
    notifyError('保存失败', `错误: ${error}\n\n尝试使用备用保存方法...`)
    
    // 尝试HTMX保存
    try {
      const response = await api.editor.save({
        type: 'ontology',
        content: '可视化编辑器生成的本体'
      }, props.domain?.id)
      
      if (response.success) {
        notifySuccess('保存成功', '本体已成功保存')
        closeEditor()
      } else {
        throw new Error('HTMX保存也失败')
      }
    } catch (htmxError) {
      notifyError('所有保存方法都失败', '请检查后端服务是否正常运行')
    }
  }
}

// 关闭属性面板
const closePropertyPanel = () => {
  showPropertyPanel.value = false
  selectedElement.value = null
}

// 保存元素属性
const saveElementProperties = () => {
  if (!selectedElement.value) return
  
  const { elementType, id, label, type, properties } = selectedElement.value
  
  if (elementType === 'node') {
    handleNodeUpdate({
      id,
      type: 'node',
      data: {
        label,
        type,
        ...properties
      }
    })
  } else if (elementType === 'edge') {
    handleEdgeUpdate({
      id,
      type: 'edge',
      data: {
        label,
        type,
        source: selectedElement.value.source,
        target: selectedElement.value.target,
        ...properties
      }
    })
  }
  
  notifySuccess('属性保存成功', '元素属性已更新')
  closePropertyPanel()
}

// 导入CSV到编辑器
const importCSVToEditor = () => {
  notifyInfo('CSV导入', 'CSV导入功能需要先上传CSV文件到主界面')
  closeEditor()
}

// CytoscapeGraph 事件处理函数
const handleNodeClick = (node: any) => {
  console.log('节点点击:', node)
  // 更新旧的属性面板（向后兼容）
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
  
  // 设置选中的元素数据并显示属性面板
  selectedElement.value = {
    elementType: 'node',
    id: node.id,
    label: node.data?.label || '',
    type: node.data?.type || '',
    properties: { ...node.data }
  }
  showPropertyPanel.value = true
}

const handleEdgeClick = (edge: any) => {
  console.log('边点击:', edge)
  // 更新旧的属性面板（向后兼容）
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
  
  // 设置选中的元素数据并显示属性面板
  selectedElement.value = {
    elementType: 'edge',
    id: edge.id,
    label: edge.data?.label || edge.data?.relationship || '',
    type: edge.data?.type || '',
    source: edge.data?.source || '',
    target: edge.data?.target || '',
    properties: { ...edge.data }
  }
  showPropertyPanel.value = true
}

const handleNodeAdd = (node: any) => {
  console.log('添加节点:', node)
  if (!graphData.value) {
    graphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
  }
  
  graphData.value.elements.push(node)
  graphData.value.stats.nodes = (graphData.value.stats.nodes || 0) + 1
  
  notifySuccess('节点添加成功', `已添加节点: ${node.data?.label || node.id}`)
}

const handleEdgeAdd = (edge: any) => {
  console.log('添加边:', edge)
  if (!graphData.value) {
    graphData.value = { elements: [], stats: { nodes: 0, edges: 0 } }
  }
  
  graphData.value.elements.push(edge)
  graphData.value.stats.edges = (graphData.value.stats.edges || 0) + 1
  
  notifySuccess('边添加成功', `已添加边: ${edge.data?.source} → ${edge.data?.target}`)
}

const handleNodeDelete = (nodeId: string) => {
  console.log('删除节点:', nodeId)
  if (graphData.value?.elements) {
    graphData.value.elements = graphData.value.elements.filter(
      (el: any) => !(el.id === nodeId && el.type === 'node')
    )
    graphData.value.stats.nodes = Math.max(0, (graphData.value.stats.nodes || 0) - 1)
    
    notifySuccess('节点删除成功', `已删除节点: ${nodeId}`)
  }
}

const handleEdgeDelete = (edgeId: string) => {
  console.log('删除边:', edgeId)
  if (graphData.value?.elements) {
    graphData.value.elements = graphData.value.elements.filter(
      (el: any) => !(el.id === edgeId && el.type === 'edge')
    )
    graphData.value.stats.edges = Math.max(0, (graphData.value.stats.edges || 0) - 1)
    
    notifySuccess('边删除成功', `已删除边: ${edgeId}`)
  }
}

const handleNodeUpdate = (node: any) => {
  console.log('更新节点:', node)
  if (graphData.value?.elements) {
    const index = graphData.value.elements.findIndex(
      (el: any) => el.id === node.id && el.type === 'node'
    )
    if (index !== -1) {
      graphData.value.elements[index] = node
      notifySuccess('节点更新成功', `已更新节点: ${node.data?.label || node.id}`)
    }
  }
}

const handleEdgeUpdate = (edge: any) => {
  console.log('更新边:', edge)
  if (graphData.value?.elements) {
    const index = graphData.value.elements.findIndex(
      (el: any) => el.id === edge.id && el.type === 'edge'
    )
    if (index !== -1) {
      graphData.value.elements[index] = edge
      notifySuccess('边更新成功', `已更新边: ${edge.data?.source} → ${edge.data?.target}`)
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadGraphData()
})
</script>

<style scoped>
/* 样式 */
</style>