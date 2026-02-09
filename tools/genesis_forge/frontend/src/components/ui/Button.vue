<template>
  <button
    :class="[
      'genesis-button',
      `genesis-button--${type}`,
      `genesis-button--${size}`,
      {
        'genesis-button--disabled': disabled,
        'genesis-button--loading': loading,
        'genesis-button--block': block,
        'genesis-button--icon-only': icon && !$slots.default
      }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="genesis-button__loading">
      <el-icon class="animate-spin"><Loading /></el-icon>
    </span>
    
    <span v-else-if="icon" class="genesis-button__icon">
      <el-icon><component :is="icon" /></el-icon>
    </span>
    
    <span v-if="$slots.default" class="genesis-button__content">
      <slot />
    </span>
    
    <span v-if="badge" class="genesis-button__badge">
      {{ badge }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  type?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  loading?: boolean
  block?: boolean
  icon?: string
  badge?: string | number
}>()

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const handleClick = (event: MouseEvent) => {
  emit('click', event)
}
</script>

<style scoped>
.genesis-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  border: 1px solid transparent;
  border-radius: 4px;
  transition: all 0.2s ease-in-out;
  outline: none;
}

.genesis-button--small {
  padding: 6px 12px;
  font-size: 12px;
}

.genesis-button--large {
  padding: 10px 20px;
  font-size: 16px;
}

.genesis-button--primary {
  background-color: #007acc;
  color: white;
  border-color: #007acc;
}

.genesis-button--primary:hover:not(:disabled) {
  background-color: #0066b3;
  border-color: #0066b3;
}

.genesis-button--primary:active:not(:disabled) {
  background-color: #005599;
  border-color: #005599;
}

.genesis-button--secondary {
  background-color: #3e3e42;
  color: #cccccc;
  border-color: #3e3e42;
}

.genesis-button--secondary:hover:not(:disabled) {
  background-color: #2d2d30;
  border-color: #2d2d30;
}

.genesis-button--success {
  background-color: #4ec9b0;
  color: white;
  border-color: #4ec9b0;
}

.genesis-button--warning {
  background-color: #ffcc00;
  color: #1e1e1e;
  border-color: #ffcc00;
}

.genesis-button--danger {
  background-color: #f44747;
  color: white;
  border-color: #f44747;
}

.genesis-button--info {
  background-color: #569cd6;
  color: white;
  border-color: #569cd6;
}

.genesis-button--text {
  background-color: transparent;
  color: #cccccc;
  border-color: transparent;
}

.genesis-button--text:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.1);
}

.genesis-button--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.genesis-button--loading {
  cursor: wait;
}

.genesis-button--block {
  display: flex;
  width: 100%;
}

.genesis-button--icon-only {
  padding: 8px;
  width: 36px;
  height: 36px;
}

.genesis-button--icon-only.genesis-button--small {
  padding: 6px;
  width: 32px;
  height: 32px;
}

.genesis-button--icon-only.genesis-button--large {
  padding: 10px;
  width: 40px;
  height: 40px;
}

.genesis-button__loading {
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
  animation: spin 1s linear infinite;
}

.genesis-button__icon {
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
}

.genesis-button--icon-only .genesis-button__icon {
  margin-right: 0;
}

.genesis-button__content {
  display: inline-flex;
  align-items: center;
}

.genesis-button__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: bold;
  line-height: 18px;
  text-align: center;
  color: white;
  background-color: #f44747;
  border-radius: 9px;
  border: 1px solid #1e1e1e;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>