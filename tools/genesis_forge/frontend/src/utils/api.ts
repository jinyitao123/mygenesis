// API服务 - 封装所有后端API调用

const API_BASE = '/api' // 通过Vite代理

// 通用请求函数
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  }
  
  try {
    const response = await fetch(url, defaultOptions)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    // 尝试解析JSON
    const text = await response.text()
    if (!text) {
      return {} as T
    }
    
    return JSON.parse(text) as T
  } catch (error) {
    console.error(`API请求失败 ${endpoint}:`, error)
    throw error
  }
}

// 领域管理API
export const domainApi = {
  // 获取所有领域
  getDomains: () => request<any>('/api/v1/domains'),
  
  // 切换领域
  switchDomain: (domainId: string) => 
    request<any>(`/api/v1/domains/${domainId}/switch`, {
      method: 'POST'
    }),
  
  // 获取领域配置
  getDomainConfig: (domainName: string) =>
    request<any>(`/api/domains/${domainName}/config`),
  
  // 保存领域配置
  saveDomain: (domainName: string, config: any) =>
    request<any>(`/api/domains/${domainName}/save`, {
      method: 'POST',
      body: JSON.stringify(config)
    })
}

// AI Copilot API
export const aiApi = {
  // 生成AI响应
  generate: (prompt: string, context?: any) =>
    request<any>('/api/v1/copilot/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, context })
    }),
  
  // 文本转Cypher
  textToCypher: (description: string, schema?: any) =>
    request<any>('/api/v1/copilot/text-to-cypher', {
      method: 'POST',
      body: JSON.stringify({ description, schema })
    }),
  
  // 建议动作
  suggestActions: (context: any) =>
    request<any>('/api/v1/copilot/suggest-actions', {
      method: 'POST',
      body: JSON.stringify({ context })
    }),
  
  // AI聊天（HTMX版本）
  chat: (message: string, history?: any[]) =>
    request<any>('/api/copilot/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history })
    })
}

// 本体管理API
export const ontologyApi = {
  // 验证本体
  validate: (schema: any) =>
    request<any>('/api/v1/ontology/validate', {
      method: 'POST',
      body: JSON.stringify({ schema })
    }),
  
  // 检查完整性
  checkIntegrity: () =>
    request<any>('/api/v1/ontology/integrity'),
  
  // 保存本体
  saveOntology: (ontology: any) =>
    request<any>('/api/save_ontology', {
      method: 'POST',
      body: JSON.stringify(ontology)
    })
}

// 世界仿真API
export const worldApi = {
  // 预览世界
  preview: () =>
    request<any>('/api/v1/world/preview'),
  
  // 验证连接性
  validateConnectivity: () =>
    request<any>('/api/v1/world/validate-connectivity'),
  
  // 重置世界
  reset: () =>
    request<any>('/api/v1/world/reset', {
      method: 'POST'
    }),
  
  // 启动仿真
  launchSimulation: (config: any) =>
    request<any>('/api/launch_simulation', {
      method: 'POST',
      body: JSON.stringify(config)
    })
}

// 规则引擎API
export const ruleApi = {
  // 仿真规则
  simulate: (ruleId: string, initialState: any, steps?: number) =>
    request<any>('/api/v1/rules/simulate', {
      method: 'POST',
      body: JSON.stringify({ ruleId, initialState, steps })
    }),
  
  // 验证规则
  validate: (rule: any) =>
    request<any>('/api/v1/rules/validate', {
      method: 'POST',
      body: JSON.stringify({ rule })
    })
}

// Git操作API
export const gitApi = {
  // 获取状态
  getStatus: () =>
    request<any>('/api/v1/git/status'),
  
  // 提交更改
  commit: (message: string, files?: string[]) =>
    request<any>('/api/v1/git/commit', {
      method: 'POST',
      body: JSON.stringify({ message, files })
    }),
  
  // 热重载
  hotReload: () =>
    request<any>('/api/v1/git/hot-reload', {
      method: 'POST'
    }),
  
  // 回滚
  rollback: (commitId?: string) =>
    request<any>('/api/v1/git/rollback', {
      method: 'POST',
      body: JSON.stringify({ commitId })
    })
}

// 编辑器API（HTMX）
export const editorApi = {
  // 获取对象编辑器
  getObjectEditor: (typeKey: string) =>
    request<any>(`/studio/editor/object/${typeKey}`),
  
  // 获取动作编辑器
  getActionEditor: (actionId: string) =>
    request<any>(`/studio/editor/action/${actionId}`),
  
  // 获取种子数据编辑器
  getSeedEditor: (seedName: string) =>
    request<any>(`/studio/editor/seed/${seedName}`),
  
  // 保存内容
  save: (content: any) =>
    request<any>('/api/save', {
      method: 'POST',
      body: JSON.stringify(content)
    }),
  
  // 验证内容
  validate: (content: any) =>
    request<any>('/api/validate', {
      method: 'POST',
      body: JSON.stringify(content)
    }),
  
  // 获取图谱数据
  getGraphData: () =>
    request<any>('/api/graph/data'),
  
  // 添加图谱节点
  addGraphNode: (node: any) =>
    request<any>('/api/graph/node', {
      method: 'POST',
      body: JSON.stringify(node)
    }),
  
  // 获取侧边栏数据
  getSidebarData: (domain?: string) =>
    request<any>(domain ? `/studio/sidebar/data?domain=${domain}` : '/studio/sidebar/data'),
  
  // 部署
  deploy: (config: any) =>
    request<any>('/api/deploy', {
      method: 'POST',
      body: JSON.stringify(config)
    }),
  
  // 格式化代码
  format: (code: string, language: string) =>
    request<any>('/api/tools/format', {
      method: 'POST',
      body: JSON.stringify({ code, language })
    })
}

// 文件上传API
export const uploadApi = {
  // 上传CSV文件并转换为本体 - 真正的后端上传
  uploadCSV: async (file: File, domainName: string): Promise<any> => {
    // 创建FormData
    const formData = new FormData()
    formData.append('file', file)
    formData.append('domain', domainName)
    formData.append('action', 'csv_to_ontology')
    
    try {
      // 使用fetch直接上传，避免JSON序列化问题
      const response = await fetch('/api/upload/csv', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`上传失败: HTTP ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('CSV上传失败:', error)
      
      // 备用方案：使用AI分析
      const text = await file.text()
      const aiResponse = await aiApi.generate(
        `请将以下CSV数据转换为本体结构：
文件: ${file.name}
内容:
${text}

要求：
1. 识别实体类型和属性
2. 建议关系类型
3. 生成JSON格式的本体定义
4. 适合领域: ${domainName}`,
        {
          data_type: 'csv_to_ontology',
          file_name: file.name,
          domain: domainName
        }
      )
      
      return aiResponse
    }
  },
  
  // 保存本体到领域
  saveOntologyToDomain: (domainName: string, ontology: any) =>
    request<any>(`/api/domains/${domainName}/save`, {
      method: 'POST',
      body: JSON.stringify({
        schema: JSON.stringify(ontology, null, 2),
        seed: JSON.stringify({ entities: [] }, null, 2)
      })
    }),
  
  // 直接保存本体
  saveOntology: (ontology: any) =>
    request<any>('/api/save_ontology', {
      method: 'POST',
      body: JSON.stringify(ontology)
    })
}

// 导出所有API
export default {
  domain: domainApi,
  ai: aiApi,
  ontology: ontologyApi,
  world: worldApi,
  rule: ruleApi,
  git: gitApi,
  editor: editorApi,
  upload: uploadApi
}