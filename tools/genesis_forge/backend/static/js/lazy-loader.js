/**
 * 前端资源懒加载工具
 * 优化页面加载性能，按需加载重型资源
 */

class LazyLoader {
    constructor() {
        this.loadedScripts = new Set();
        this.loadedStyles = new Set();
        this.pendingPromises = new Map();
    }

    /**
     * 懒加载JavaScript脚本
     * @param {string} url - 脚本URL
     * @param {Object} options - 选项
     * @returns {Promise} 加载完成的Promise
     */
    loadScript(url, options = {}) {
        if (this.loadedScripts.has(url)) {
            return Promise.resolve();
        }

        if (this.pendingPromises.has(url)) {
            return this.pendingPromises.get(url);
        }

        const promise = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.async = options.async !== false;
            script.defer = options.defer !== false;
            
            if (options.integrity) {
                script.integrity = options.integrity;
            }
            
            if (options.crossOrigin) {
                script.crossOrigin = options.crossOrigin;
            }

            script.onload = () => {
                this.loadedScripts.add(url);
                this.pendingPromises.delete(url);
                console.log(`✅ 脚本加载完成: ${url}`);
                resolve();
            };

            script.onerror = (error) => {
                this.pendingPromises.delete(url);
                console.error(`❌ 脚本加载失败: ${url}`, error);
                reject(new Error(`Failed to load script: ${url}`));
            };

            document.head.appendChild(script);
        });

        this.pendingPromises.set(url, promise);
        return promise;
    }

    /**
     * 懒加载CSS样式表
     * @param {string} url - 样式表URL
     * @returns {Promise} 加载完成的Promise
     */
    loadStyle(url) {
        if (this.loadedStyles.has(url)) {
            return Promise.resolve();
        }

        if (this.pendingPromises.has(url)) {
            return this.pendingPromises.get(url);
        }

        const promise = new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            
            link.onload = () => {
                this.loadedStyles.add(url);
                this.pendingPromises.delete(url);
                console.log(`✅ 样式表加载完成: ${url}`);
                resolve();
            };

            link.onerror = (error) => {
                this.pendingPromises.delete(url);
                console.error(`❌ 样式表加载失败: ${url}`, error);
                reject(new Error(`Failed to load stylesheet: ${url}`));
            };

            document.head.appendChild(link);
        });

        this.pendingPromises.set(url, promise);
        return promise;
    }

    /**
     * 批量加载资源
     * @param {Array} resources - 资源数组 [{type: 'script', url: '...'}, ...]
     * @returns {Promise} 所有资源加载完成的Promise
     */
    loadResources(resources) {
        const promises = resources.map(resource => {
            if (resource.type === 'script') {
                return this.loadScript(resource.url, resource.options || {});
            } else if (resource.type === 'style') {
                return this.loadStyle(resource.url);
            }
            return Promise.resolve();
        });
        
        return Promise.all(promises);
    }

    /**
     * 预加载资源（不阻塞页面）
     * @param {string} url - 资源URL
     * @param {string} as - 资源类型 ('script', 'style', 'image', 'font')
     */
    preloadResource(url, as = 'script') {
        if (this.loadedScripts.has(url) || this.loadedStyles.has(url)) {
            return;
        }

        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = url;
        link.as = as;
        
        if (as === 'script') {
            link.crossOrigin = 'anonymous';
        }

        document.head.appendChild(link);
        console.log(`📦 预加载资源: ${url} (${as})`);
    }

    /**
     * 检查资源是否已加载
     * @param {string} url - 资源URL
     * @param {string} type - 资源类型 ('script' 或 'style')
     * @returns {boolean} 是否已加载
     */
    isLoaded(url, type = 'script') {
        if (type === 'script') {
            return this.loadedScripts.has(url);
        } else if (type === 'style') {
            return this.loadedStyles.has(url);
        }
        return false;
    }
}

// 创建全局懒加载器实例
window.lazyLoader = new LazyLoader();

// 预加载关键资源（不阻塞页面）
document.addEventListener('DOMContentLoaded', () => {
    // 预加载Cytoscape.js（当用户可能访问图谱时）
    window.lazyLoader.preloadResource(
        'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js',
        'script'
    );
    
    // 预加载Monaco Editor核心
    window.lazyLoader.preloadResource(
        'https://unpkg.com/monaco-editor@0.45.0/min/vs/loader.js',
        'script'
    );
    
    // 预加载NProgress（用于显示加载进度）
    window.lazyLoader.preloadResource(
        'https://cdn.jsdelivr.net/npm/nprogress@0.2.0/nprogress.min.js',
        'script'
    );
    
    // 延迟加载Font Awesome（如果页面中有图标）
    setTimeout(() => {
        const hasIcons = document.querySelector('i.fas, i.far, i.fab, i.fal, i.fad');
        if (hasIcons && !window.lazyLoader.isLoaded('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css', 'style')) {
            window.lazyLoader.loadStyle('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        }
    }, 1000);
});

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyLoader;
}