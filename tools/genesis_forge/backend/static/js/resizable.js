// 可调整大小和可拖动的面板分隔条
console.log('Resizable panels script loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded: Initializing resizable panels...');
    
    // 等待Alpine初始化
    document.addEventListener('alpine:init', () => {
        console.log('Alpine initialized, setting up resizable panels');
        
        // 初始化所有分隔条
        initAllResizers();
        
        // 监听侧边栏折叠状态
        Alpine.store('app').$watch('sidebarCollapsed', (value) => {
            console.log('Sidebar collapsed changed:', value);
            setTimeout(() => {
                if (value) {
                    removeSidebarResizer();
                } else {
                    initSidebarResizer();
                }
            }, 100);
        });
        
        // 监听标签页切换以重新初始化分隔条
        Alpine.store('app').$watch('activeTab', (value) => {
            console.log('Active tab changed:', value);
            // 延迟执行以确保DOM已更新
            setTimeout(() => {
                if (value === 'split') {
                    initSplitViewResizer();
                } else {
                    removeSplitViewResizer();
                }
            }, 100);
        });
        
        // 监听底部面板状态变化
        Alpine.store('app').$watch('bottomPanelOpen', (value) => {
            console.log('Bottom panel open changed:', value);
            setTimeout(() => {
                if (value) {
                    initBottomPanelResizer();
                } else {
                    removeBottomPanelResizer();
                }
            }, 100);
        });
    });
    
    // 也尝试直接初始化，以防Alpine未加载
    setTimeout(() => {
        if (typeof Alpine === 'undefined') {
            console.log('Alpine not loaded, trying direct initialization');
            initAllResizers();
        }
    }, 1000);
});

function initAllResizers() {
    initSidebarResizer();
    initSplitViewResizer();
    initBottomPanelResizer();
}

// 侧边栏分隔条
function initSidebarResizer() {
    console.log('Initializing sidebar resizer...');
    
    // 检查侧边栏是否折叠
    if (window.Alpine && Alpine.store('app') && Alpine.store('app').sidebarCollapsed) {
        console.log('Sidebar is collapsed, skipping resizer');
        return; // 折叠时不添加分隔条
    }
    
    const sidebar = document.querySelector('aside');
    const mainContent = document.querySelector('main');
    console.log('Sidebar:', sidebar, 'Main content:', mainContent);
    
    if (!sidebar || !mainContent) {
        console.log('Missing sidebar or main content');
        return;
    }
    
    // 检查是否已存在分隔条
    if (document.querySelector('.sidebar-resizer')) {
        console.log('Sidebar resizer already exists');
        return;
    }
    
    const resizer = document.createElement('div');
    resizer.className = 'sidebar-resizer w-1 bg-studio-border hover:bg-studio-accent transition-colors duration-200';
    resizer.title = '拖动调整侧边栏宽度';
    resizer.style.cursor = 'col-resize';
    
    // 插入分隔条到侧边栏和主内容之间
    sidebar.parentNode.insertBefore(resizer, sidebar.nextSibling);
    console.log('Sidebar resizer added');
    
    let isResizing = false;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        document.body.classList.add('resizing');
        
        const startX = e.clientX;
        const startWidth = sidebar.offsetWidth;
        console.log('Start sidebar resize, width:', startWidth);
        
        function onMouseMove(e) {
            if (!isResizing) return;
            
            const dx = e.clientX - startX;
            const newWidth = Math.max(200, Math.min(600, startWidth + dx));
            
            sidebar.style.width = newWidth + 'px';
            sidebar.style.flex = '0 0 auto';
            mainContent.style.flex = '1 1 auto';
            
            // 如果宽度调整到很小，自动折叠侧边栏？
            if (newWidth < 100 && Alpine.store('app')) {
                Alpine.store('app').sidebarCollapsed = true;
            }
        }
        
        function onMouseUp() {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.body.classList.remove('resizing');
            console.log('Sidebar resize completed');
            
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    // 双击重置宽度
    resizer.addEventListener('dblclick', () => {
        sidebar.style.width = '';
        sidebar.style.flex = '';
        console.log('Sidebar width reset');
    });
}

// 分割视图分隔条
function initSplitViewResizer() {
    console.log('Initializing split view resizer...');
    // 使用属性包含选择器，避免转义问题
    const splitView = document.querySelector('[x-show*="split"]');
    console.log('Found split view:', splitView);
    if (!splitView) {
        console.log('No split view found');
        return;
    }
    
    const leftPanel = splitView.querySelector('div:first-child');
    const rightPanel = splitView.querySelector('div:last-child');
    console.log('Left panel:', leftPanel, 'Right panel:', rightPanel);
    
    if (!leftPanel || !rightPanel) {
        console.log('Missing left or right panel');
        return;
    }
    
    // 检查是否已存在分隔条
    if (splitView.querySelector('.split-resizer')) {
        console.log('Split resizer already exists');
        return;
    }
    
    const resizer = document.createElement('div');
    resizer.className = 'split-resizer w-1 bg-studio-border hover:bg-studio-accent transition-colors duration-200';
    resizer.title = '拖动调整左右面板宽度';
    resizer.style.cursor = 'col-resize';
    
    // 插入分隔条到左右面板之间
    leftPanel.parentNode.insertBefore(resizer, leftPanel.nextSibling);
    console.log('Split resizer added');
    
    let isResizing = false;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        document.body.classList.add('resizing');
        
        const startX = e.clientX;
        const containerWidth = splitView.offsetWidth;
        const leftWidth = leftPanel.offsetWidth;
        
        function onMouseMove(e) {
            if (!isResizing) return;
            
            const dx = e.clientX - startX;
            const newLeftWidth = Math.max(300, Math.min(containerWidth - 300, leftWidth + dx));
            
            leftPanel.style.width = newLeftWidth + 'px';
            leftPanel.style.flex = '0 0 auto';
            rightPanel.style.flex = '1 1 auto';
        }
        
        function onMouseUp() {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.body.classList.remove('resizing');
            
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    // 双击重置宽度
    resizer.addEventListener('dblclick', () => {
        leftPanel.style.width = '';
        leftPanel.style.flex = '';
        rightPanel.style.flex = '';
        console.log('Split view reset');
    });
}

// 底部面板分隔条
function initBottomPanelResizer() {
    console.log('Initializing bottom panel resizer...');
    
    // 底部面板容器（包含标题栏和内容）
    const bottomPanelContainer = document.querySelector('.border-t.border-studio-border.bg-studio-sidebar');
    console.log('Bottom panel container:', bottomPanelContainer);
    
    if (!bottomPanelContainer) {
        console.log('Bottom panel container not found');
        return;
    }
    
    // 使用属性包含选择器查找内容区域
    const bottomPanelContent = bottomPanelContainer.querySelector('[x-show*="bottomPanelOpen"]');
    console.log('Bottom panel content:', bottomPanelContent);
    
    if (!bottomPanelContent) {
        console.log('Bottom panel content not found');
        return;
    }
    
    // 检查是否已存在分隔条
    if (bottomPanelContainer.querySelector('.bottom-resizer')) {
        console.log('Bottom resizer already exists');
        return;
    }
    
    const resizer = document.createElement('div');
    resizer.className = 'bottom-resizer h-1 bg-studio-border hover:bg-studio-accent transition-colors duration-200';
    resizer.title = '拖动调整底部面板高度';
    resizer.style.cursor = 'row-resize';
    
    // 插入分隔条到内容区域上方，但在容器内部
    bottomPanelContainer.insertBefore(resizer, bottomPanelContent);
    console.log('Bottom resizer added');
    
    let isResizing = false;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
        document.body.classList.add('resizing');
        
        const startY = e.clientY;
        const startHeight = bottomPanelContent.offsetHeight;
        console.log('Start bottom panel resize, height:', startHeight);
        
        function onMouseMove(e) {
            if (!isResizing) return;
            
            const dy = startY - e.clientY; // 向上拖动增加高度
            const newHeight = Math.max(100, Math.min(500, startHeight + dy));
            
            bottomPanelContent.style.height = newHeight + 'px';
            bottomPanelContainer.classList.remove('h-64'); // 移除固定高度类
        }
        
        function onMouseUp() {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.body.classList.remove('resizing');
            console.log('Bottom panel resize completed');
            
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    // 双击重置高度
    resizer.addEventListener('dblclick', () => {
        bottomPanelContent.style.height = '';
        bottomPanelContainer.classList.add('h-64');
        console.log('Bottom panel height reset');
    });
}

// 移除分隔条的函数
function removeSidebarResizer() {
    const resizer = document.querySelector('.sidebar-resizer');
    if (resizer) resizer.remove();
}

function removeSplitViewResizer() {
    const resizer = document.querySelector('.split-resizer');
    if (resizer) resizer.remove();
}

function removeBottomPanelResizer() {
    const resizer = document.querySelector('.bottom-resizer');
    if (resizer) resizer.remove();
}