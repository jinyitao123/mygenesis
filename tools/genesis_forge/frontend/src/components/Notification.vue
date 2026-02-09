<template>
  <div class="notification-container">
    <transition-group
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
      class="w-full max-w-sm space-y-4"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="max-w-sm w-full bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden"
        :class="{
          'border-l-4 border-green-500': notification.type === 'success',
          'border-l-4 border-red-500': notification.type === 'error',
          'border-l-4 border-yellow-500': notification.type === 'warning',
          'border-l-4 border-blue-500': notification.type === 'info'
        }"
      >
        <div class="p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <svg v-if="notification.type === 'success'" class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-if="notification.type === 'error'" class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-if="notification.type === 'warning'" class="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <svg v-if="notification.type === 'info'" class="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="ml-3 w-0 flex-1 pt-0.5">
              <p class="text-sm font-medium text-white">
                {{ notification.title }}
              </p>
              <p v-if="notification.message" class="mt-1 text-sm text-gray-300">
                {{ notification.message }}
              </p>
              <div v-if="notification.actions" class="mt-3 flex space-x-3">
                <button
                  v-for="action in notification.actions"
                  :key="action.label"
                  @click="action.handler"
                  class="inline-flex items-center text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2"
                  :class="{
                    'text-blue-400 hover:text-blue-300 focus:ring-blue-500': action.type === 'primary',
                    'text-gray-400 hover:text-gray-300 focus:ring-gray-500': action.type === 'secondary'
                  }"
                >
                  {{ action.label }}
                </button>
              </div>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
              <button
                @click="removeNotification(notification.id)"
                class="bg-gray-800 rounded-md inline-flex text-gray-400 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <span class="sr-only">关闭</span>
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div v-if="notification.autoClose" class="h-1 bg-gray-700">
          <div 
            class="h-full transition-all duration-300 ease-linear"
            :class="{
              'bg-green-500': notification.type === 'success',
              'bg-red-500': notification.type === 'error',
              'bg-yellow-500': notification.type === 'warning',
              'bg-blue-500': notification.type === 'info'
            }"
            :style="{ width: `${notification.progress}%` }"
          ></div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

export interface NotificationAction {
  label: string
  handler: () => void
  type?: 'primary' | 'secondary'
}

export interface NotificationItem {
  id: string
  title: string
  message?: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  autoClose?: boolean
  actions?: NotificationAction[]
  progress: number
}

const notifications = ref<NotificationItem[]>([])

let notificationId = 0
const progressIntervals = new Map<string, number>()

const addNotification = (notification: Omit<NotificationItem, 'id' | 'progress'>): string => {
  const id = `notification-${++notificationId}`
  const newNotification: NotificationItem = {
    ...notification,
    id,
    progress: 100,
    autoClose: notification.autoClose ?? true,
    duration: notification.duration ?? 5000
  }
  
  notifications.value.push(newNotification)
  
  if (newNotification.autoClose) {
    startProgressTimer(id, newNotification.duration!)
  }
  
  return id
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index !== -1) {
    notifications.value.splice(index, 1)
    clearProgressTimer(id)
  }
}

const startProgressTimer = (id: string, duration: number) => {
  const startTime = Date.now()
  const endTime = startTime + duration
  
  const interval = setInterval(() => {
    const now = Date.now()
    const remaining = endTime - now
    const progress = Math.max(0, (remaining / duration) * 100)
    
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.progress = progress
    }
    
    if (remaining <= 0) {
      removeNotification(id)
    }
  }, 100)
  
  progressIntervals.set(id, interval as unknown as number)
}

const clearProgressTimer = (id: string) => {
  const interval = progressIntervals.get(id)
  if (interval) {
    clearInterval(interval)
    progressIntervals.delete(id)
  }
}

onUnmounted(() => {
  progressIntervals.forEach((interval) => {
    clearInterval(interval)
  })
  progressIntervals.clear()
})

defineExpose({
  addNotification
})
</script>

<style scoped>
.notification-container {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 1rem;
  pointer-events: none;
  z-index: 50;
}

@media (min-width: 640px) {
  .notification-container {
    align-items: flex-start;
    justify-content: flex-end;
    padding: 1.5rem;
  }
}
</style>
