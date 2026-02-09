// 通知工具 - 替换所有alert弹窗

// 通知类型
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

// 通知选项
export interface NotificationOptions {
  title: string
  message?: string
  type?: NotificationType
  duration?: number
  autoClose?: boolean
  actions?: Array<{
    label: string
    handler: () => void
    type?: 'primary' | 'secondary'
  }>
}

// 全局通知实例
let notificationInstance: any = null

// 设置通知实例
export const setNotificationInstance = (instance: any) => {
  notificationInstance = instance
}

// 显示通知
export const notify = (options: NotificationOptions | string) => {
  if (!notificationInstance) {
    console.warn('通知系统未初始化，使用console.log代替')
    if (typeof options === 'string') {
      console.log('通知:', options)
    } else {
      console.log('通知:', options.title, options.message)
    }
    return
  }
  
  const notificationOptions = typeof options === 'string' 
    ? { title: options, type: 'info' as NotificationType }
    : options
  
  return notificationInstance.addNotification({
    type: 'info',
    autoClose: true,
    duration: 5000,
    ...notificationOptions
  })
}

// 快捷方法
export const notifySuccess = (title: string, message?: string) => {
  return notify({ title, message, type: 'success' })
}

export const notifyError = (title: string, message?: string) => {
  return notify({ title, message, type: 'error' })
}

export const notifyWarning = (title: string, message?: string) => {
  return notify({ title, message, type: 'warning' })
}

export const notifyInfo = (title: string, message?: string) => {
  return notify({ title, message, type: 'info' })
}

// 确认对话框（替换confirm）
export const confirm = async (options: {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: NotificationType
}): Promise<boolean> => {
  return new Promise((resolve) => {
    const notificationId = notify({
      title: options.title,
      message: options.message,
      type: options.type || 'warning',
      autoClose: false,
      actions: [
        {
          label: options.cancelText || '取消',
          handler: () => {
            if (notificationInstance) {
              notificationInstance.removeNotification(notificationId)
            }
            resolve(false)
          },
          type: 'secondary'
        },
        {
          label: options.confirmText || '确认',
          handler: () => {
            if (notificationInstance) {
              notificationInstance.removeNotification(notificationId)
            }
            resolve(true)
          },
          type: 'primary'
        }
      ]
    })
  })
}

// 提示输入（替换prompt）
export const prompt = async (options: {
  title: string
  message: string
  defaultValue?: string
  placeholder?: string
  confirmText?: string
  cancelText?: string
}): Promise<string | null> => {
  return new Promise((resolve) => {
    // 创建自定义模态框
    const modal = document.createElement('div')
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'
    
    modal.innerHTML = `
      <div class="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold">${options.title}</h3>
          <button onclick="this.closest('.fixed').remove(); window.__promptResult = null" class="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>
        <div class="mb-4">
          <p class="text-gray-300 mb-3">${options.message}</p>
          <input 
            id="promptInput"
            type="text" 
            class="w-full bg-gray-900 border border-gray-700 rounded p-3 text-white"
            placeholder="${options.placeholder || '请输入'}"
            value="${options.defaultValue || ''}"
            autofocus
          />
        </div>
        <div class="flex justify-end space-x-3">
          <button onclick="this.closest('.fixed').remove(); window.__promptResult = null" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            ${options.cancelText || '取消'}
          </button>
          <button onclick="const input = document.getElementById('promptInput'); window.__promptResult = input ? input.value : null; this.closest('.fixed').remove()" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
            ${options.confirmText || '确认'}
          </button>
        </div>
      </div>
    `
    
    // 添加键盘支持
    const handleKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        modal.remove()
        window.removeEventListener('keydown', handleKeydown)
        resolve(null)
      } else if (e.key === 'Enter') {
        const input = modal.querySelector('#promptInput') as HTMLInputElement
        if (input) {
          modal.remove()
          window.removeEventListener('keydown', handleKeydown)
          resolve(input.value)
        }
      }
    }
    
    window.addEventListener('keydown', handleKeydown)
    
    // 监听关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove()
        window.removeEventListener('keydown', handleKeydown)
        resolve(null)
      }
    })
    
    document.body.appendChild(modal)
    
    // 等待结果
    const checkResult = () => {
      if (window.__promptResult !== undefined) {
        const result = window.__promptResult
        delete window.__promptResult
        resolve(result)
      } else {
        setTimeout(checkResult, 100)
      }
    }
    
    checkResult()
  })
}

// 导出所有方法
export default {
  setNotificationInstance,
  notify,
  notifySuccess,
  notifyError,
  notifyWarning,
  notifyInfo,
  confirm,
  prompt
}