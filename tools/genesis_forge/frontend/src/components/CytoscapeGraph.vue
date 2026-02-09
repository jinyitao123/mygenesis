<template>
  <div class="h-full w-full flex flex-col">
    <!-- 工具栏 -->
    <div class="bg-gray-800 p-3 border-b border-gray-700 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="text-sm font-medium">图谱编辑器</div>
        <div class="flex items-center space-x-2">
          <button 
            @click="zoomIn" 
            class="p-1.5 bg-gray-700 rounded hover:bg-gray-600"
            title="放大"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          <button 
            @click="zoomOut" 
            class="p-1.5 bg-gray-700 rounded hover:bg-gray-600"
            title="缩小"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <button 
            @click="fitView" 
            class="p-1.5 bg-gray-700 rounded hover:bg-gray-600"
            title="适应视图"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
            </svg>
          </button>
          <button 
            @click="resetView" 
            class="p-1.5 bg-gray-700 rounded hover:bg-gray-600"
            title="重置视图"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="flex items-center space-x-3">
        <div class="text-xs text-gray-400">
          节点: {{ nodeCount }} | 边: {{ edgeCount }}
        </div>
        <div class="flex space-x-2">
          <button 
            @click="addNode" 
            class="px-3 py-1.5 bg-blue-600 rounded text-sm hover:bg-blue-700 flex items-center"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            添加节点
          </button>
          <button 
            @click="addEdge" 
            class="px-3 py-1.5 bg-green-600 rounded text-sm hover:bg-green-700 flex items-center"
            :disabled="!selectedNodes.source || !selectedNodes.target"
            :class="{ 'opacity-50 cursor-not-allowed': !selectedNodes.source || !selectedNodes.target }"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
            添加关系
          </button>
          <button 
            @click="deleteSelected" 
            class="px-3 py-1.5 bg-red-600 rounded text-sm hover:bg-red-700 flex items-center"
            :disabled="!selectedElement"
            :class="{ 'opacity-50 cursor-not-allowed': !selectedElement }"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </button>
        </div>
      </div>
    </div>
    
    <!-- 图容器 -->
    <div ref="cyContainer" class="flex-1 bg-gray-900"></div>
    
    <!-- 属性面板 -->
    <div v-if="selectedElement" class="bg-gray-800 border-t border-gray-700 p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold">属性编辑</h3>
        <button 
          @click="closePropertyPanel" 
          class="text-gray-400 hover:text-white"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div v-if="selectedElement">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">ID</label>
          <input 
            v-model="selectedElement.data.id" 
            type="text" 
            class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            :readonly="true"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">标签</label>
          <input 
            v-model="selectedElement.data.label" 
            type="text" 
            class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            @change="updateElement"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">类型</label>
          <input 
            v-model="selectedElement.data.type" 
            type="text" 
            class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            @change="updateElement"
          />
        </div>
        
        <div v-if="selectedElement.data.source" class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">源节点</label>
          <input 
            v-model="selectedElement.data.source" 
            type="text" 
            class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            @change="updateElement"
          />
        </div>
        
        <div v-if="selectedElement.data.target" class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">目标节点</label>
          <input 
            v-model="selectedElement.data.target" 
            type="text" 
            class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            @change="updateElement"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-300 mb-1">属性</label>
          <div class="bg-gray-900 rounded p-3 max-h-40 overflow-y-auto">
            <div v-if="!selectedElement.data.properties || Object.keys(selectedElement.data.properties).length === 0" class="text-gray-400 text-sm">
              无属性
            </div>
            <div v-else class="space-y-2">
              <div v-for="(value, key) in selectedElement.data.properties" :key="key" class="flex items-center justify-between">
                <span class="text-sm text-gray-300">{{ key }}:</span>
                <span class="text-sm text-gray-400">{{ typeof value === 'object' ? JSON.stringify(value) : value }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex justify-end space-x-3">
          <button 
            @click="saveElement" 
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
    </div>
    
    <!-- 添加节点模态框 -->
    <div v-if="showAddNodeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-xl font-bold mb-4">添加新节点</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">节点ID</label>
            <input 
              v-model="newNode.id" 
              type="text" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              placeholder="例如: node_001"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">节点标签</label>
            <input 
              v-model="newNode.label" 
              type="text" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              placeholder="例如: 运输卡车A"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">节点类型</label>
            <select 
              v-model="newNode.type" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="">选择类型</option>
              <option v-for="type in availableNodeTypes" :key="type" :value="type">{{ type }}</option>
              <option value="custom">自定义类型</option>
            </select>
            
            <div v-if="newNode.type === 'custom'" class="mt-2">
              <input 
                v-model="newNode.customType" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="输入自定义类型"
              />
            </div>
          </div>
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button 
            @click="cancelAddNode" 
            class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
          >
            取消
          </button>
          <button 
            @click="confirmAddNode" 
            class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
            :disabled="!newNode.id || !newNode.label"
            :class="{ 'opacity-50 cursor-not-allowed': !newNode.id || !newNode.label }"
          >
            添加
          </button>
        </div>
      </div>
    </div>
    
    <!-- 添加关系模态框 -->
    <div v-if="showAddEdgeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-xl font-bold mb-4">添加新关系</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">源节点</label>
            <select 
              v-model="newEdge.source" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="">选择源节点</option>
              <option v-for="node in nodes" :key="node.data.id" :value="node.data.id">
                {{ node.data.label }} ({{ node.data.type }})
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">目标节点</label>
            <select 
              v-model="newEdge.target" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="">选择目标节点</option>
              <option v-for="node in nodes" :key="node.data.id" :value="node.data.id">
                {{ node.data.label }} ({{ node.data.type }})
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">关系类型</label>
            <select 
              v-model="newEdge.type" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="">选择关系类型</option>
              <option v-for="type in availableEdgeTypes" :key="type" :value="type">{{ type }}</option>
              <option value="custom">自定义类型</option>
            </select>
            
            <div v-if="newEdge.type === 'custom'" class="mt-2">
              <input 
                v-model="newEdge.customType" 
                type="text" 
                class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="输入自定义关系类型"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">关系标签</label>
            <input 
              v-model="newEdge.label" 
              type="text" 
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              :placeholder="newEdge.type === 'custom' ? '输入关系标签' : newEdge.type"
            />
          </div>
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button 
            @click="cancelAddEdge" 
            class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
          >
            取消
          </button>
          <button 
            @click="confirmAddEdge" 
            class="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
            :disabled="!newEdge.source || !newEdge.target || !newEdge.type"
            :class="{ 'opacity-50 cursor-not-allowed': !newEdge.source || !newEdge.target || !newEdge.type }"
          >
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'

// 定义元素类型
interface GraphElement {
  data: {
    id: string
    label: string
    type: string
    source?: string
    target?: string
    properties?: Record<string, any>
    position?: { x: number; y: number }
  }
  position?: { x: number; y: number }
}

// 属性
const props = defineProps<{
  elements: GraphElement[]
  domainConfig: any
}>()

const emit = defineEmits<{
  'node-click': [node: any]
  'edge-click': [edge: any]
  'node-add': [node: any]
  'edge-add': [edge: any]
  'node-delete': [nodeId: string]
  'edge-delete': [edgeId: string]
  'node-update': [node: any]
  'edge-update': [edge: any]
  'graph-updated': [elements: any[]]
}>()

// 引用
const cyContainer = ref<HTMLElement>()
let cy: Core | null = null

// 响应式数据
const nodeCount = ref(0)
const edgeCount = ref(0)
const selectedElement = ref<GraphElement | null>(null)
const selectedNodes = ref({
  source: '',
  target: ''
})
const showAddNodeModal = ref(false)
const showAddEdgeModal = ref(false)

// 新元素数据
const newNode = ref({
  id: '',
  label: '',
  type: '',
  customType: ''
})

const newEdge = ref({
  source: '',
  target: '',
  type: '',
  label: '',
  customType: ''
})

// 计算属性
const nodes = computed(() => {
  return props.elements.filter(el => !el.data.source && !el.data.target)
})

const edges = computed(() => {
  return props.elements.filter(el => el.data.source && el.data.target)
})

const availableNodeTypes = computed(() => {
  const types = new Set<string>()
  nodes.value.forEach(node => {
    if (node.data.type) {
      types.add(node.data.type)
    }
  })
  return Array.from(types)
})

const availableEdgeTypes = computed(() => {
  const types = new Set<string>()
  edges.value.forEach(edge => {
    if (edge.data.type) {
      types.add(edge.data.type)
    }
  })
  return Array.from(types)
})

// 初始化Cytoscape
const initCytoscape = () => {
  if (!cyContainer.value) return
  
  // 销毁现有的实例
  if (cy) {
    cy.destroy()
  }
  
  // 创建Cytoscape实例
  cy = cytoscape({
    container: cyContainer.value,
    elements: formatElementsForCytoscape(props.elements),
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#3B82F6',
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'color': '#FFFFFF',
          'font-size': '12px',
          'font-weight': 'bold',
          'width': '60px',
          'height': '60px',
          'border-width': '2px',
          'border-color': '#1E40AF'
        }
      },
      {
        selector: 'node[type="object_type"]',
        style: {
          'background-color': '#10B981',
          'border-color': '#047857'
        }
      },
      {
        selector: 'node[type="relation_type"]',
        style: {
          'background-color': '#8B5CF6',
          'border-color': '#7C3AED'
        }
      },
      {
        selector: 'node[type="action_type"]',
        style: {
          'background-color': '#F59E0B',
          'border-color': '#D97706'
        }
      },
      {
        selector: 'node[type="TRUCK"]',
        style: {
          'background-color': '#EF4444',
          'border-color': '#DC2626'
        }
      },
      {
        selector: 'node[type="WAREHOUSE"]',
        style: {
          'background-color': '#8B5CF6',
          'border-color': '#7C3AED'
        }
      },
      {
        selector: 'node[type="PACKAGE"]',
        style: {
          'background-color': '#10B981',
          'border-color': '#047857'
        }
      },
      {
        selector: 'node[type="ORDER"]',
        style: {
          'background-color': '#F59E0B',
          'border-color': '#D97706'
        }
      },
      {
        selector: 'node[type="SUPPLIER"]',
        style: {
          'background-color': '#EC4899',
          'border-color': '#DB2777'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#9CA3AF',
          'target-arrow-color': '#9CA3AF',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'text-rotation': 'autorotate',
          'color': '#D1D5DB',
          'font-size': '10px',
          'font-weight': 'bold'
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': '#3B82F6',
          'target-arrow-color': '#3B82F6',
          'width': 3
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': '4px',
          'border-color': '#3B82F6'
        }
      }
    ],
    layout: {
      name: 'cose',
      animate: false,  // 禁用动画，避免节点持续移动
      fit: true,
      padding: 50,
      randomize: true,  // 启用随机化以获得更好的初始布局
      componentSpacing: 50,
      nodeRepulsion: 8000,  // 减少排斥力
      nodeOverlap: 20,
      idealEdgeLength: 50,  // 减少理想边长
      edgeElasticity: 50,
      nestingFactor: 5,
      gravity: 1,  // 大幅减少重力
      numIter: 250,  // 减少迭代次数
      initialTemp: 100,
      coolingFactor: 0.99,
      minTemp: 0.5
    }
  })
  
  // 更新计数
  updateCounts()
  
  // 添加事件监听
  setupEventListeners()
}

// 格式化元素为Cytoscape格式
const formatElementsForCytoscape = (elements: GraphElement[]) => {
  return elements.map(el => {
    const cytoscapeElement: any = {
      data: {
        id: el.data.id || `element_${Date.now()}_${Math.random()}`,
        label: el.data.label || el.data.id || '未命名',
        type: el.data.type || 'unknown',
        ...el.data
      }
    }
    
    // 添加位置信息
    if (el.position) {
      cytoscapeElement.position = el.position
    } else if (el.data.position) {
      cytoscapeElement.position = el.data.position
    }
    
    // 如果是边，添加源和目标
    if (el.data.source && el.data.target) {
      cytoscapeElement.data.source = el.data.source
      cytoscapeElement.data.target = el.data.target
    }
    
    return cytoscapeElement
  })
}

// 设置事件监听器
const setupEventListeners = () => {
  if (!cy) return
  
  // 选择事件
  cy.on('select', 'node, edge', (event) => {
    const element = event.target
    const elementData = element.data()
    
    // 构建GraphElement对象
    const graphElement: GraphElement = {
      data: {
        id: elementData.id,
        label: elementData.label || elementData.id,
        type: elementData.type || 'unknown',
        ...elementData
      }
    }
    
    // 如果是节点，更新selectedNodes
    if (element.isNode()) {
      if (!selectedNodes.value.source) {
        selectedNodes.value.source = elementData.id
      } else if (!selectedNodes.value.target && elementData.id !== selectedNodes.value.source) {
        selectedNodes.value.target = elementData.id
      }
      
      // 发出节点点击事件
      emit('node-click', graphElement)
    } else if (element.isEdge()) {
      // 发出边点击事件
      emit('edge-click', graphElement)
    }
    
    selectedElement.value = graphElement
  })
  
  // 取消选择事件
  cy.on('unselect', 'node, edge', () => {
    const selected = cy?.$(':selected')
    if (selected.length === 0) {
      selectedElement.value = null
      emit('element-selected', null)
    }
  })
  
  // 双击节点添加关系
  cy.on('dbltap', 'node', (event) => {
    const node = event.target
    const nodeId = node.data('id')
    
    if (!selectedNodes.value.source) {
      selectedNodes.value.source = nodeId
    } else if (!selectedNodes.value.target && nodeId !== selectedNodes.value.source) {
      selectedNodes.value.target = nodeId
      showAddEdgeModal.value = true
    }
  })
  
  // 右键菜单
  cy.on('cxttap', 'node, edge', (event) => {
    event.preventDefault()
    const element = event.target
    
    // 显示上下文菜单
    showContextMenu(element)
  })
}

// 显示上下文菜单
const showContextMenu = (element: any) => {
  // 这里可以添加右键菜单功能
  console.log('右键点击:', element.data())
}

// 更新计数
const updateCounts = () => {
  if (!cy) return
  
  nodeCount.value = cy.nodes().length
  edgeCount.value = cy.edges().length
}

// 视图控制
const zoomIn = () => {
  if (cy) {
    cy.zoom(cy.zoom() * 1.2)
  }
}

const zoomOut = () => {
  if (cy) {
    cy.zoom(cy.zoom() / 1.2)
  }
}

const fitView = () => {
  if (cy) {
    cy.fit()
  }
}

const resetView = () => {
  if (cy) {
    cy.reset()
    cy.fit()
  }
}

// 元素操作
const addNode = () => {
  // 生成默认ID
  newNode.value.id = `node_${Date.now()}`
  newNode.value.label = `新节点_${Date.now().toString().slice(-4)}`
  newNode.value.type = ''
  newNode.value.customType = ''
  
  showAddNodeModal.value = true
}

const confirmAddNode = () => {
  if (!cy) return
  
  const nodeType = newNode.value.type === 'custom' ? newNode.value.customType : newNode.value.type
  
  const newNodeData: GraphElement = {
    data: {
      id: newNode.value.id,
      label: newNode.value.label,
      type: nodeType || 'custom',
      properties: {
        created: new Date().toISOString(),
        source: 'visual_editor'
      }
    },
    position: {
      x: Math.random() * 500 + 100,
      y: Math.random() * 300 + 100
    }
  }
  
  // 添加到Cytoscape
  cy.add({
    group: 'nodes',
    data: newNodeData.data,
    position: newNodeData.position
  })
  
  // 触发事件
  emit('node-add', newNodeData)
  emit('graph-updated', getCurrentElements())
  
  // 更新计数
  updateCounts()
  
  // 重置并关闭模态框
  cancelAddNode()
}

const cancelAddNode = () => {
  showAddNodeModal.value = false
  newNode.value = {
    id: '',
    label: '',
    type: '',
    customType: ''
  }
}

const addEdge = () => {
  if (!selectedNodes.value.source || !selectedNodes.value.target) {
    return
  }
  
  newEdge.value.source = selectedNodes.value.source
  newEdge.value.target = selectedNodes.value.target
  newEdge.value.type = ''
  newEdge.value.label = ''
  newEdge.value.customType = ''
  
  showAddEdgeModal.value = true
}

const confirmAddEdge = () => {
  if (!cy) return
  
  const edgeType = newEdge.value.type === 'custom' ? newEdge.value.customType : newEdge.value.type
  const edgeLabel = newEdge.value.label || edgeType
  
  const newEdgeData: GraphElement = {
    data: {
      id: `edge_${newEdge.value.source}_${newEdge.value.target}_${Date.now()}`,
      label: edgeLabel,
      type: edgeType || 'RELATES_TO',
      source: newEdge.value.source,
      target: newEdge.value.target,
      properties: {
        created: new Date().toISOString(),
        source: 'visual_editor'
      }
    }
  }
  
  // 检查是否已存在相同的关系
  const existingEdge = cy.edges().filter(edge => 
    edge.data('source') === newEdge.value.source && 
    edge.data('target') === newEdge.value.target &&
    edge.data('type') === edgeType
  )
  
  if (existingEdge.length > 0) {
    alert('相同节点间已存在此类型的关系')
    return
  }
  
  // 添加到Cytoscape
  cy.add({
    group: 'edges',
    data: newEdgeData.data
  })
  
  // 触发事件
  emit('edge-add', newEdgeData)
  emit('graph-updated', getCurrentElements())
  
  // 更新计数
  updateCounts()
  
  // 重置并关闭模态框
  cancelAddEdge()
}

const cancelAddEdge = () => {
  showAddEdgeModal.value = false
  newEdge.value = {
    source: '',
    target: '',
    type: '',
    label: '',
    customType: ''
  }
}

const deleteSelected = () => {
  if (!cy || !selectedElement.value) return
  
  const elementId = selectedElement.value.data.id
  
  // 获取元素并判断类型
  const elementToDelete = cy.getElementById(elementId)
  if (elementToDelete) {
    // 根据元素类型触发相应事件
    if (elementToDelete.isNode()) {
      emit('node-delete', elementId)
    } else if (elementToDelete.isEdge()) {
      emit('edge-delete', elementId)
    }
    
    // 从Cytoscape中删除
    elementToDelete.remove()
  }
  
  emit('graph-updated', getCurrentElements())
  
  // 更新计数和选择状态
  updateCounts()
  selectedElement.value = null
  selectedNodes.value = { source: '', target: '' }
}

const updateElement = () => {
  if (!cy || !selectedElement.value) return
  
  const elementId = selectedElement.value.data.id
  const element = cy.getElementById(elementId)
  
  if (element) {
    // 更新元素数据
    element.data(selectedElement.value.data)
    
    // 触发事件 - 根据元素类型发出不同事件
    if (element.isNode()) {
      emit('node-update', selectedElement.value)
    } else if (element.isEdge()) {
      emit('edge-update', selectedElement.value)
    }
    emit('graph-updated', getCurrentElements())
  }
}

const saveElement = () => {
  updateElement()
  closePropertyPanel()
}

const closePropertyPanel = () => {
  selectedElement.value = null
  selectedNodes.value = { source: '', target: '' }
  
  // 清除Cytoscape中的选择
  if (cy) {
    cy.elements().unselect()
  }
  
  emit('element-selected', null)
}

// 获取当前所有元素
const getCurrentElements = (): GraphElement[] => {
  if (!cy) return []
  
  const elements: GraphElement[] = []
  
  cy.elements().forEach(element => {
    const elementData = element.data()
    const position = element.position()
    
    const graphElement: GraphElement = {
      data: {
        id: elementData.id,
        label: elementData.label || elementData.id,
        type: elementData.type || 'unknown',
        ...elementData
      },
      position: {
        x: position.x,
        y: position.y
      }
    }
    
    elements.push(graphElement)
  })
  
  return elements
}

// 监听元素变化
watch(() => props.elements, (newElements) => {
  if (cy) {
    // 清除现有元素
    cy.elements().remove()
    
    // 添加新元素
    const formattedElements = formatElementsForCytoscape(newElements)
    cy.add(formattedElements)
    
    // 只有在元素数量有显著变化时才重新布局
    const currentCount = cy.elements().length
    const newCount = newElements.length
    
    // 如果元素数量变化小于5个，不重新布局
    if (Math.abs(currentCount - newCount) > 5 || newCount < currentCount) {
      // 使用预设布局或简单布局
      cy.layout({
        name: 'grid',  // 使用网格布局更稳定
        animate: false,
        fit: true,
        padding: 30,
        rows: Math.ceil(Math.sqrt(newCount)) || 1
      }).run()
    } else {
      // 少量变化时只调整视图
      cy.fit()
    }
    
    // 更新计数
    updateCounts()
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  initCytoscape()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})

// 暴露方法给父组件
defineExpose({
  getCurrentElements,
  fitView,
  resetView
})
</script>

<style scoped>
/* 自定义样式 */
:deep(.cytoscape-container) {
  width: 100%;
  height: 100%;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #374151;
}

::-webkit-scrollbar-thumb {
  background: #6B7280;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9CA3AF;
}
</style>