/**
 * 前端性能监控工具
 * 跟踪页面加载时间、资源加载、用户交互延迟
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: null,
            resourceTiming: [],
            userInteractions: [],
            memoryUsage: null
        };
        
        this.startTime = performance.now();
        this.initialized = false;
    }
    
    init() {
        if (this.initialized) return;
        
        // 监听页面加载完成
        if (document.readyState === 'complete') {
            this.capturePageLoad();
        } else {
            window.addEventListener('load', () => this.capturePageLoad());
        }
        
        // 监听资源加载
        this.captureResourceTiming();
        
        // 监听用户交互
        this.captureUserInteractions();
        
        // 监听内存使用（如果支持）
        this.captureMemoryUsage();
        
        this.initialized = true;
        console.log('✅ 性能监控已初始化');
    }
    
    capturePageLoad() {
        const timing = performance.timing;
        
        if (timing.loadEventEnd > 0) {
            this.metrics.pageLoad = {
                dns: timing.domainLookupEnd - timing.domainLookupStart,
                tcp: timing.connectEnd - timing.connectStart,
                request: timing.responseStart - timing.requestStart,
                response: timing.responseEnd - timing.responseStart,
                domLoading: timing.domContentLoadedEventStart - timing.domLoading,
                domInteractive: timing.domInteractive - timing.domLoading,
                domComplete: timing.domComplete - timing.domLoading,
                loadEvent: timing.loadEventEnd - timing.loadEventStart,
                total: timing.loadEventEnd - timing.navigationStart
            };
            
            console.log('📊 页面加载性能:', {
                total: `${this.metrics.pageLoad.total}ms`,
                domInteractive: `${this.metrics.pageLoad.domInteractive}ms`,
                domComplete: `${this.metrics.pageLoad.domComplete}ms`
            });
            
            // 发送性能数据到服务器（可选）
            this.sendMetricsToServer();
        }
    }
    
    captureResourceTiming() {
        const resources = performance.getEntriesByType('resource');
        
        resources.forEach(resource => {
            this.metrics.resourceTiming.push({
                name: resource.name,
                duration: resource.duration,
                transferSize: resource.transferSize,
                initiatorType: resource.initiatorType,
                startTime: resource.startTime
            });
        });
        
        // 找出加载最慢的资源
        const slowResources = this.metrics.resourceTiming
            .filter(r => r.duration > 1000) // 超过1秒的资源
            .sort((a, b) => b.duration - a.duration)
            .slice(0, 5);
        
        if (slowResources.length > 0) {
            console.warn('⚠️ 检测到慢速资源:', slowResources.map(r => ({
                name: r.name.split('/').pop(),
                duration: `${Math.round(r.duration)}ms`
            })));
        }
    }
    
    captureUserInteractions() {
        // 监听首次用户交互
        let firstInteraction = false;
        
        const interactionHandler = (event) => {
            if (!firstInteraction) {
                firstInteraction = true;
                const interactionTime = performance.now() - this.startTime;
                
                this.metrics.userInteractions.push({
                    type: event.type,
                    target: event.target.tagName,
                    time: interactionTime,
                    timestamp: new Date().toISOString()
                });
                
                console.log('👆 首次用户交互:', {
                    type: event.type,
                    time: `${Math.round(interactionTime)}ms`,
                    element: event.target.tagName
                });
                
                // 移除监听器
                ['click', 'keydown', 'touchstart'].forEach(type => {
                    document.removeEventListener(type, interactionHandler);
                });
            }
        };
        
        // 监听多种交互类型
        ['click', 'keydown', 'touchstart'].forEach(type => {
            document.addEventListener(type, interactionHandler, { once: true });
        });
    }
    
    captureMemoryUsage() {
        // 检查是否支持内存API
        if (performance.memory) {
            this.metrics.memoryUsage = {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
            };
            
            const memoryUsage = (this.metrics.memoryUsage.usedJSHeapSize / this.metrics.memoryUsage.jsHeapSizeLimit) * 100;
            
            if (memoryUsage > 70) {
                console.warn(`⚠️ 内存使用率高: ${memoryUsage.toFixed(1)}%`);
            }
        }
    }
    
    sendMetricsToServer() {
        // 可选：将性能数据发送到服务器进行分析
        try {
            if (typeof navigator.sendBeacon === 'function') {
                const data = JSON.stringify({
                    url: window.location.href,
                    metrics: this.metrics,
                    userAgent: navigator.userAgent,
                    timestamp: new Date().toISOString()
                });
                
                navigator.sendBeacon('/api/performance/metrics', data);
            }
        } catch (error) {
            // 静默失败
        }
    }
    
    getReport() {
        return {
            summary: {
                pageLoadTime: this.metrics.pageLoad?.total || 0,
                slowResources: this.metrics.resourceTiming.filter(r => r.duration > 1000).length,
                firstInteraction: this.metrics.userInteractions[0]?.time || 0
            },
            details: this.metrics
        };
    }
    
    logReport() {
        const report = this.getReport();
        console.group('📈 性能报告');
        console.log('页面加载时间:', `${report.summary.pageLoadTime}ms`);
        console.log('慢速资源数量:', report.summary.slowResources);
        console.log('首次交互时间:', `${report.summary.firstInteraction}ms`);
        console.log('完整报告:', report.details);
        console.groupEnd();
    }
}

// 创建全局性能监控实例
window.performanceMonitor = new PerformanceMonitor();

// 自动初始化（延迟一点以避免影响初始加载）
setTimeout(() => {
    window.performanceMonitor.init();
}, 1000);

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
}