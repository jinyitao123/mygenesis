
// 安全的Alpine.js辅助函数
window.AlpineHelpers = {
    // 安全的字符串操作
    safeUpperCase: function(value) {
        return value && typeof value === 'string' ? value.toUpperCase() : '';
    },
    
    safeLowerCase: function(value) {
        return value && typeof value === 'string' ? value.toLowerCase() : '';
    },
    
    safeTrim: function(value) {
        return value && typeof value === 'string' ? value.trim() : '';
    },
    
    // 安全的属性访问
    safeGet: function(obj, path, defaultValue = '') {
        if (!obj) return defaultValue;
        
        const keys = path.split('.');
        let result = obj;
        
        for (const key of keys) {
            if (result && typeof result === 'object' && key in result) {
                result = result[key];
            } else {
                return defaultValue;
            }
        }
        
        return result !== undefined ? result : defaultValue;
    },
    
    // 安全的数组操作
    safeArrayLength: function(arr) {
        return Array.isArray(arr) ? arr.length : 0;
    },
    
    safeArrayItem: function(arr, index, defaultValue = null) {
        return Array.isArray(arr) && arr[index] !== undefined ? arr[index] : defaultValue;
    },
    
    // 组件初始化辅助
    initComponent: function(componentName, defaults = {}) {
        return {
            ...defaults,
            // 确保所有必需属性都有默认值
            init() {
                // 组件初始化逻辑
                console.log(`${componentName} 组件初始化`);
                
                // 确保数据完整性
                this.ensureDataIntegrity();
            },
            
            ensureDataIntegrity() {
                // 确保所有属性都有值
                for (const key in defaults) {
                    if (this[key] === undefined) {
                        this[key] = defaults[key];
                    }
                }
            },
            
            // 错误处理
            handleError(error, context = '') {
                console.error(`[${componentName}] ${context}:`, error);
                // 可以在这里添加错误上报或用户提示
            }
        };
    }
};

// 注册为Alpine魔法属性
document.addEventListener('alpine:init', () => {
    // 安全字符串魔法属性
    Alpine.magic('safeUpper', () => {
        return (value) => AlpineHelpers.safeUpperCase(value);
    });
    
    Alpine.magic('safeLower', () => {
        return (value) => AlpineHelpers.safeLowerCase(value);
    });
    
    Alpine.magic('safeGet', () => {
        return (obj, path, defaultValue) => AlpineHelpers.safeGet(obj, path, defaultValue);
    });
});

// 使用示例:
// <div x-text="$safeUpper(message.language)"></div>
// <div x-text="$safeGet(message, 'language', 'unknown')"></div>
