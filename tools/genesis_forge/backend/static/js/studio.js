// Genesis Studio JavaScript 客户端
console.log('Genesis Studio v2.0 loaded');

// HTMX 扩展
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing Genesis Studio...');
    
    // 初始化工具提示
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-2 py-1 text-sm bg-gray-800 text-white rounded shadow-lg';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.left = e.pageX + 'px';
            tooltip.style.top = (e.pageY - 30) + 'px';
            tooltip.id = 'tooltip-' + Date.now();
            document.body.appendChild(tooltip);
            this.dataset.currentTooltip = tooltip.id;
        });
        
        el.addEventListener('mouseleave', function() {
            const tooltipId = this.dataset.currentTooltip;
            if (tooltipId) {
                const tooltip = document.getElementById(tooltipId);
                if (tooltip) tooltip.remove();
                delete this.dataset.currentTooltip;
            }
        });
    });
    
    // 处理HTMX请求
    document.body.addEventListener('htmx:beforeRequest', function(e) {
        const target = e.target;
        target.classList.add('loading');
    });
    
    document.body.addEventListener('htmx:afterRequest', function(e) {
        const target = e.target;
        target.classList.remove('loading');
    });
    
    // 编辑器初始化
    if (typeof initEditor === 'function') {
        initEditor();
    }
});

// 编辑器功能
function initEditor() {
    console.log('Initializing editor...');
    
    // 图谱编辑器占位
    const graphEditor = document.getElementById('graph-editor');
    if (graphEditor) {
        graphEditor.innerHTML = '<div class="text-center py-8 text-gray-500">图谱编辑器初始化中...</div>';
    }
    
    // 代码编辑器占位
    const codeEditor = document.getElementById('code-editor');
    if (codeEditor) {
        codeEditor.innerHTML = '<div class="text-center py-8 text-gray-500">代码编辑器初始化中...</div>';
    }
}

// API 调用函数
window.GenesisAPI = {
    // 获取领域数据
    getDomains: async function() {
        try {
            const response = await fetch('/api/v1/domains');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch domains:', error);
            return { domains: [], status: 'error' };
        }
    },
    
    // 保存对象类型
    saveObjectType: async function(domain, objectType) {
        try {
            const response = await fetch(`/api/v1/${domain}/objects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(objectType)
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to save object type:', error);
            return { status: 'error', message: error.message };
        }
    },
    
    // 获取图谱数据
    getGraphData: async function(domain) {
        try {
            const response = await fetch(`/api/v1/${domain}/graph`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch graph data:', error);
            return { nodes: [], edges: [] };
        }
    },
    
    // AI Copilot 调用
    callCopilot: async function(type, prompt) {
        try {
            const response = await fetch('/api/v1/copilot/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, prompt })
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to call AI copilot:', error);
            return { status: 'error', message: error.message };
        }
    }
};

// 工具函数
window.GenesisUtils = {
    // 显示通知
    showToast: function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },
    
    // 格式化JSON显示
    formatJSON: function(obj) {
        return JSON.stringify(obj, null, 2);
    },
    
    // 生成UUID
    generateUUID: function() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
};