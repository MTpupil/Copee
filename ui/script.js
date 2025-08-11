/**
 * Copee - 前端脚本
 * 处理用户交互和API通信
 */

class ModernClipboardUI {
    constructor() {
        // 初始化属性
        this.clipboardItems = [];
        this.filteredItems = [];
        this.selectedIndex = -1;
        this.isSearchMode = false;
        this.isFavoriteMode = false; // 收藏模式标志
        this.filterType = null; // 类型筛选：'text', 'image', null
        this.searchType = 'normal'; // 搜索类型：'normal', 'regex'
        this.timeFilter = null; // 时间筛选：'today', 'yesterday', 'week', 'month', null
        
        // 设置相关属性
        this.settings = {
            autoDelete: {
                enabled: false,
                byTime: false,
                byCount: false,
                days: 7,
                maxItems: 100
            }
        };
        
        // 自动保存防抖定时器
        this.autoSaveTimer = null;
        
        // 绑定方法到实例，确保事件监听器能正确移除
        this.adjustModalSize = this.adjustModalSize.bind(this);
        
        // 绑定DOM元素
        this.bindElements();
        
        // 绑定事件
        this.bindEvents();
        
        // 初始化加载
        this.init();
    }
    
    /**
     * 绑定DOM元素
     */
    bindElements() {
        // 头部元素
        this.searchBtn = document.getElementById('searchBtn');
        this.favoriteBtn = document.getElementById('favoriteBtn');
        this.textFilterBtn = document.getElementById('textFilterBtn');
        this.imageFilterBtn = document.getElementById('imageFilterBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        
        // 搜索相关
        this.searchContainer = document.getElementById('searchContainer');
        this.searchInput = document.getElementById('searchInput');
        this.searchClose = document.getElementById('searchClose');
        
        // 高级搜索选项
        this.searchOptions = document.getElementById('searchOptions');
        this.normalSearchBtn = document.getElementById('normalSearchBtn');
        this.regexSearchBtn = document.getElementById('regexSearchBtn');
        this.allTimeBtn = document.getElementById('allTimeBtn');
        this.todayBtn = document.getElementById('todayBtn');
        this.yesterdayBtn = document.getElementById('yesterdayBtn');
        this.weekBtn = document.getElementById('weekBtn');
        this.monthBtn = document.getElementById('monthBtn');
        
        // 主要内容
        this.clipboardList = document.getElementById('clipboardList');
        this.emptyState = document.getElementById('emptyState');
        

        
        // 模态框
        this.modalOverlay = document.getElementById('modalOverlay');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalMessage = document.getElementById('modalMessage');
        this.modalCancel = document.getElementById('modalCancel');
        this.modalConfirm = document.getElementById('modalConfirm');
        
        // 通知
        this.notification = document.getElementById('notification');
        
        // 设置页面
        this.settingsModal = document.getElementById('settingsModal');
        this.settingsClose = document.getElementById('settingsClose');
        
        // 设置选项
        this.autoDeleteEnabled = document.getElementById('autoDeleteEnabled');
        this.autoDeleteOptions = document.getElementById('autoDeleteOptions');
        this.deleteByTime = document.getElementById('deleteByTime');
        this.deleteByCount = document.getElementById('deleteByCount');
        this.deleteDays = document.getElementById('deleteDays');
        this.maxItems = document.getElementById('maxItems');
        this.timeDeleteGroup = document.getElementById('timeDeleteGroup');
        this.countDeleteGroup = document.getElementById('countDeleteGroup');
    }
    
    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 头部按钮事件
        this.searchBtn.addEventListener('click', () => this.toggleSearch());
        this.favoriteBtn.addEventListener('click', () => this.toggleFavoriteMode());
        this.textFilterBtn.addEventListener('click', () => this.toggleTypeFilter('text'));
        this.imageFilterBtn.addEventListener('click', () => this.toggleTypeFilter('image'));
        this.clearBtn.addEventListener('click', () => this.showClearConfirm());
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        
        // 搜索事件
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        this.searchInput.addEventListener('keydown', (e) => this.handleSearchKeydown(e));
        this.searchClose.addEventListener('click', () => this.closeSearch());
        
        // 高级搜索选项事件
        this.normalSearchBtn.addEventListener('click', () => this.setSearchType('normal'));
        this.regexSearchBtn.addEventListener('click', () => this.setSearchType('regex'));
        this.allTimeBtn.addEventListener('click', () => this.setTimeFilter(null));
        this.todayBtn.addEventListener('click', () => this.setTimeFilter('today'));
        this.yesterdayBtn.addEventListener('click', () => this.setTimeFilter('yesterday'));
        this.weekBtn.addEventListener('click', () => this.setTimeFilter('week'));
        this.monthBtn.addEventListener('click', () => this.setTimeFilter('month'));
        
        // 设置页面事件
        this.settingsClose.addEventListener('click', () => this.closeSettingsWithSave());
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettingsWithSave();
            }
        });
        
        // 移除测试保存按钮事件（已改为关闭时自动保存）
        // const testSaveBtn = document.getElementById('testSaveBtn');
        // if (testSaveBtn) {
        //     testSaveBtn.addEventListener('click', () => this.testSaveSettings());
        // }
        
        // 自动删除选项事件 - 移除自动保存，改为关闭时保存
        this.autoDeleteEnabled.addEventListener('change', () => {
            this.toggleAutoDeleteOptions();
        });
        this.deleteByTime.addEventListener('change', () => {
            this.toggleTimeDeleteGroup();
        });
        this.deleteByCount.addEventListener('change', () => {
            this.toggleCountDeleteGroup();
        });
        
        // 移除自动保存的input事件监听器
        // this.deleteDays.addEventListener('input', () => this.autoSaveSettings());
        // this.maxItems.addEventListener('input', () => this.autoSaveSettings());
        
        // 模态框事件
        this.modalCancel.addEventListener('click', () => this.hideModal());
        this.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) {
                this.hideModal();
            }
        });
        

        
        // 键盘事件
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // 窗口失去焦点时隐藏（模拟点击外部）
        window.addEventListener('blur', () => {
            setTimeout(async () => {
                try {
                    await pywebview.api.hide_window();
                } catch (error) {
                    console.error('隐藏窗口失败:', error);
                }
            }, 100);
        });
        

    }
    
    /**
     * 初始化应用
     */
    async init() {
        // 显示加载状态
        this.showLoadingState();
        
        try {
            // 等待一小段时间确保API准备就绪
            await this.waitForAPI();
            await this.loadClipboardItems();
            // 移除状态栏更新调用
        } catch (error) {
            console.error('初始化失败:', error);
            // 不显示错误通知，静默处理，因为这通常是加载中的正常状态
            // 继续尝试加载，直到成功
            setTimeout(() => this.init(), 1000);
        }
    }
    
    /**
     * 等待API准备就绪
     */
    async waitForAPI() {
        let retries = 0;
        const maxRetries = 10;
        
        while (retries < maxRetries) {
            try {
                // 尝试调用一个简单的API来检查是否准备就绪
                if (typeof pywebview !== 'undefined' && pywebview.api) {
                    await pywebview.api.get_item_count();
                    return; // API准备就绪
                }
            } catch (error) {
                // API还未准备就绪，继续等待
            }
            
            retries++;
            await new Promise(resolve => setTimeout(resolve, 200)); // 等待200ms
        }
        
        throw new Error('API未能在预期时间内准备就绪');
    }
    
    /**
     * 显示加载状态
     */
    showLoadingState() {
        this.clipboardList.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <p>正在加载剪贴板内容...</p>
            </div>
        `;
    }
    
    /**
     * 加载剪贴板项目
     */
    async loadClipboardItems() {
        try {
            const response = await pywebview.api.get_clipboard_items();
            const result = JSON.parse(response);
            
            if (result.success) {
                this.clipboardItems = result.data;
                this.filteredItems = [...this.clipboardItems];
                this.renderClipboardList();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('加载剪贴板项目失败:', error);
            // 只在多次重试后仍然失败时才显示错误
            throw error;
        }
    }
    
    /**
     * 渲染剪贴板列表
     */
    renderClipboardList() {
        let items;
        
        if (this.isFavoriteMode) {
            // 收藏模式：只显示收藏的项目
            items = this.clipboardItems.filter(item => item.favorite);
        } else if (this.isSearchMode) {
            // 搜索模式：显示搜索结果
            items = this.filteredItems;
        } else {
            // 普通模式：显示所有项目
            items = this.clipboardItems;
        }
        
        // 应用类型筛选
        if (this.filterType) {
            items = items.filter(item => item.type === this.filterType);
        }
        
        if (items.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        const html = items.map((item, displayIndex) => {
            // 需要找到原始数组中的实际索引
            let actualIndex = displayIndex;
            if (this.isSearchMode || this.isFavoriteMode) {
                actualIndex = this.clipboardItems.findIndex(original => original.hash === item.hash);
            }
            
            // 索引映射处理
            if ((this.isSearchMode || this.isFavoriteMode || this.filterType) && actualIndex === -1) {
                // 如果找不到匹配项，跳过这个项目
                return '';
            }
            
            // 验证索引有效性
            if (actualIndex < 0 || actualIndex >= this.clipboardItems.length) {
                return '';
            }
            
            return this.createItemHTML(item, actualIndex);
        }).filter(html => html !== '').join('');
        
        this.clipboardList.innerHTML = html;
        
        // 绑定项目事件
        this.bindItemEvents();
        
        // 异步加载图片
        this.loadImages();
    }
    
    /**
     * 创建项目HTML
     */
    createItemHTML(item, index) {
        const timeAgo = this.getTimeAgo(new Date(item.timestamp));
        const isSelected = index === this.selectedIndex ? 'selected' : '';
        const isFavorite = item.favorite || false; // 检查是否收藏
        const favoriteClass = isFavorite ? 'favorite' : ''; // 收藏记录特殊样式
        
        // 根据内容类型设置不同的预览
        let preview;
        if (item.type === 'image') {
            // 使用API接口获取图片路径
            preview = `<img src="" alt="图片" class="item-image" data-filename="${item.content}" style="display:none;">
                      <div class="image-loading">加载中...</div>`;
        } else {
            preview = this.escapeHtml(item.preview);
        }
        
        // 根据内容类型生成操作按钮
        let actionButtons = `
            <div class="item-actions">
                <button class="action-btn" data-action="copy" title="复制">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="action-btn ${isFavorite ? 'favorited' : ''}" data-action="favorite" title="${isFavorite ? '取消收藏' : '收藏'}">
                    <i class="fas fa-star ${isFavorite ? 'favorited' : ''}"></i>
                </button>
                <button class="action-btn ${item.note ? 'has-note' : ''}" data-action="note" title="${item.note ? '编辑备注' : '添加备注'}">
                    <i class="fas fa-sticky-note"></i>
                </button>`
        
        // 只有文本类型才显示"仅复制文本"按钮
        if (item.type === 'text') {
            actionButtons += `
                <button class="action-btn" data-action="copyText" title="仅复制纯文本">
                    <i class="fas fa-font"></i>
                </button>`;
        }
        
        actionButtons += `
                <button class="action-btn delete-btn" data-action="delete" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </div>`;
        
        // 备注显示区域
        let noteDisplay = '';
        if (item.note && item.note.trim()) {
            noteDisplay = `<div class="item-note">
                <i class="fas fa-sticky-note note-icon"></i>
                <span class="note-text">${this.escapeHtml(item.note)}</span>
            </div>`;
        }
        
        return `
            <div class="clipboard-item ${isSelected} ${favoriteClass}" data-index="${index}">
                <div class="item-content">
                    <div class="item-text">
                        <div class="item-preview">${preview}</div>
                        ${noteDisplay}
                        <div class="item-meta">
                            <span class="item-time">${timeAgo}</span>
                        </div>
                    </div>
                </div>
                ${actionButtons}
            </div>
        `;
    }
    
    /**
     * 绑定项目事件
     */
    bindItemEvents() {
        const items = this.clipboardList.querySelectorAll('.clipboard-item');
        
        items.forEach(item => {
            const index = parseInt(item.dataset.index);
            
            // 检查索引是否有效
            if (isNaN(index) || index < 0 || index >= this.clipboardItems.length || !this.clipboardItems[index]) {
                return; // 跳过无效项目
            }
            
            // 点击事件
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.action-btn')) {
                    this.selectItem(index);
                    this.copyItem(index);
                }
            });
            
            // 双击事件
            item.addEventListener('dblclick', () => {
                this.copyItem(index);
            });
            
            // 动作按钮事件
            const actionBtns = item.querySelectorAll('.action-btn');
            actionBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const action = btn.dataset.action;
                    this.handleItemAction(action, index);
                });
            });
        });
    }
    
    /**
     * 异步加载图片
     */
    async loadImages() {
        const imageElements = this.clipboardList.querySelectorAll('.item-image[data-filename]');
        
        for (const img of imageElements) {
            const filename = img.dataset.filename;
            const loadingDiv = img.nextElementSibling;
            
            try {
                // 调用API获取图片Base64数据
                const response = await pywebview.api.get_image_data(filename);
                const result = JSON.parse(response);
                
                if (result.success && result.data_url) {
                    // 使用Base64数据URL显示图片
                    img.src = result.data_url;
                    img.style.display = 'block';
                    
                    // 添加图片加载事件监听
                    img.onload = function() {
                        // 图片加载成功
                    };
                    
                    img.onerror = function() {
                        // 图片加载失败
                        if (loadingDiv && loadingDiv.classList.contains('image-loading')) {
                            loadingDiv.textContent = '[图片数据无法显示]';
                            loadingDiv.classList.add('error-state');
                        }
                    };
                    
                    // 隐藏加载提示
                    if (loadingDiv && loadingDiv.classList.contains('image-loading')) {
                        loadingDiv.style.display = 'none';
                    }
                } else {
                    // 图片文件不存在，显示错误信息
                    if (loadingDiv && loadingDiv.classList.contains('image-loading')) {
                        loadingDiv.textContent = result.message || '[图片文件不存在]';
                        loadingDiv.classList.add('error-state');
                    }
                }
            } catch (error) {
                // 显示错误信息
                if (loadingDiv && loadingDiv.classList.contains('image-loading')) {
                    loadingDiv.textContent = '[图片加载失败]';
                    loadingDiv.classList.add('error-state');
                }
            }
        }
    }
    
    /**
     * 选择项目
     */
    selectItem(index) {
        this.selectedIndex = index;
        
        // 更新视觉选中状态
        const items = this.clipboardList.querySelectorAll('.clipboard-item');
        items.forEach((item, i) => {
            const itemIndex = parseInt(item.dataset.index);
            item.classList.toggle('selected', itemIndex === index);
        });
    }
    
    /**
     * 复制项目到剪贴板
     */
    async copyItem(index) {
        try {
            const response = await pywebview.api.copy_item(index);
            const result = JSON.parse(response);
            
            if (result.success) {
                // 不再显示通知提示，直接隐藏窗口
                console.log(result.message); // 仅在控制台输出信息
                
                // 复制成功后立即隐藏窗口
                setTimeout(async () => {
                    try {
                        await pywebview.api.hide_window();
                    } catch (error) {
                        console.error('隐藏窗口失败:', error);
                    }
                }, 100); // 减少延迟时间
                
                // 重新加载列表以更新顺序
                await this.loadClipboardItems();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('复制失败:', error);
            this.showNotification('复制失败', 'error');
        }
    }
    
    /**
     * 仅复制纯文本内容（去除格式）
     */
    async copyTextOnly(index) {
        try {
            const response = await pywebview.api.copy_text_only(index);
            const result = JSON.parse(response);
            
            if (result.success) {
                console.log(result.message);
                
                // 复制成功后立即隐藏窗口
                setTimeout(async () => {
                    try {
                        await pywebview.api.hide_window();
                    } catch (error) {
                        console.error('隐藏窗口失败:', error);
                    }
                }, 100);
                
                await this.loadClipboardItems();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('仅复制文本失败:', error);
            this.showNotification('仅复制文本失败', 'error');
        }
    }
    
    /**
     * 切换收藏状态
     */
    async toggleFavorite(index) {
        try {
            const response = await pywebview.api.toggle_favorite(index);
            const result = JSON.parse(response);
            
            if (result.success) {
                // 去掉收藏成功/取消收藏的通知弹窗
                await this.loadClipboardItems();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('切换收藏状态失败:', error);
            this.showNotification('操作失败', 'error');
        }
    }
    
    /**
     * 获取收藏的项目
     */
    getFavoriteItems() {
        return this.clipboardItems.filter(item => item.favorite);
    }
    
    /**
     * 删除项目
     */
    async deleteItem(index) {
        try {
            // 验证索引参数
            if (index === null || index === undefined || isNaN(index)) {
                this.showNotification(`无效的索引参数: ${index}`, 'error');
                return;
            }
            
            // 确保索引是整数
            index = parseInt(index);
            if (isNaN(index)) {
                this.showNotification(`索引无法转换为整数: ${index}`, 'error');
                return;
            }
            
            // 验证索引范围
            if (index < 0 || index >= this.clipboardItems.length) {
                this.showNotification(`索引超出范围: ${index}, 总数: ${this.clipboardItems.length}`, 'error');
                return;
            }
            
            // 调用后端API删除项目
            const response = await pywebview.api.delete_item(index);
            const result = JSON.parse(response);
            
            if (result.success) {
                // 去掉删除成功的通知弹窗
                await this.loadClipboardItems();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            this.showNotification(`删除失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * 清空所有项目
     */
    async clearAllItems() {
        try {
            const response = await pywebview.api.clear_all_items();
            const result = JSON.parse(response);
            
            if (result.success) {
                this.showNotification('已清空所有项目', 'success');
                await this.loadClipboardItems();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('清空失败:', error);
            this.showNotification('清空失败', 'error');
        }
    }
    
    /**
     * 搜索项目
     */
    async searchItems(keyword) {
        try {
            const response = await pywebview.api.search_items(keyword, this.searchType, this.timeFilter);
            const result = JSON.parse(response);
            
            if (result.success) {
                this.filteredItems = result.data;
                this.renderClipboardList();
                
                // 显示搜索结果提示
                if (keyword.trim() || this.timeFilter) {
                    this.showNotification(result.message, 'info');
                }
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showNotification(error.message || '搜索失败', 'error');
        }
    }
    
    /**
     * 切换搜索模式
     */
    toggleSearch() {
        if (this.searchContainer.classList.contains('active')) {
            this.closeSearch();
        } else {
            this.openSearch();
        }
    }
    
    /**
     * 打开搜索
     */
    openSearch() {
        this.searchContainer.classList.add('active');
        this.isSearchMode = true;
        setTimeout(() => {
            this.searchInput.focus();
        }, 300);
    }
    
    /**
     * 关闭搜索
     */
    closeSearch() {
        this.searchContainer.classList.remove('active');
        this.searchInput.value = '';
        this.isSearchMode = false;
        
        // 重置搜索选项
        this.searchType = 'normal';
        this.timeFilter = null;
        
        // 重置按钮状态
        document.querySelectorAll('.search-mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.normalSearchBtn.classList.add('active');
        
        document.querySelectorAll('.time-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.allTimeBtn.classList.add('active');
        
        // 重置搜索框提示文字
        this.searchInput.placeholder = '搜索剪贴板内容...';
        
        this.filteredItems = [...this.clipboardItems];
        this.renderClipboardList();
    }
    
    /**
     * 处理搜索输入
     */
    handleSearch(keyword) {
        // 防抖处理
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.searchItems(keyword);
        }, 300);
    }
    
    /**
     * 设置搜索类型
     */
    setSearchType(type) {
        this.searchType = type;
        
        // 更新按钮状态
        document.querySelectorAll('.search-mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        if (type === 'normal') {
            this.normalSearchBtn.classList.add('active');
            this.searchInput.placeholder = '搜索剪贴板内容...';
        } else if (type === 'regex') {
            this.regexSearchBtn.classList.add('active');
            this.searchInput.placeholder = '输入正则表达式...';
        }
        
        // 如果有搜索内容，重新搜索
        if (this.searchInput.value.trim() || this.timeFilter) {
            this.searchItems(this.searchInput.value);
        }
    }
    
    /**
     * 设置时间筛选
     */
    setTimeFilter(filter) {
        this.timeFilter = filter;
        
        // 更新按钮状态
        document.querySelectorAll('.time-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        if (filter === null) {
            this.allTimeBtn.classList.add('active');
        } else if (filter === 'today') {
            this.todayBtn.classList.add('active');
        } else if (filter === 'yesterday') {
            this.yesterdayBtn.classList.add('active');
        } else if (filter === 'week') {
            this.weekBtn.classList.add('active');
        } else if (filter === 'month') {
            this.monthBtn.classList.add('active');
        }
        
        // 重新搜索
        this.searchItems(this.searchInput.value);
    }
    
    /**
     * 处理搜索键盘事件
     */
    handleSearchKeydown(e) {
        if (e.key === 'Escape') {
            this.closeSearch();
        } else if (e.key === 'Enter') {
            // 如果有搜索结果，选择第一个
            if (this.filteredItems.length > 0) {
                const firstIndex = this.clipboardItems.findIndex(
                    item => item.hash === this.filteredItems[0].hash
                );
                this.selectItem(firstIndex);
                this.copyItem(firstIndex);
            }
        }
    }
    
    /**
     * 处理键盘事件
     */
    handleKeydown(e) {
        // 如果搜索框处于焦点状态，不处理导航键
        if (document.activeElement === this.searchInput) {
            if (e.key === 'Escape') {
                this.closeSearch();
                e.preventDefault();
            }
            return;
        }
        
        // Ctrl+F 打开搜索
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            this.toggleSearch();
        }
        // Escape 关闭搜索或模态框，或隐藏窗口
        else if (e.key === 'Escape') {
            if (this.isSearchMode) {
                this.closeSearch();
            } else if (this.modalOverlay.classList.contains('active')) {
                this.hideModal();
            } else {
                // Escape键隐藏窗口
                this.hideWindow();
            }
        }
        // 上下箭头选择项目
        else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            e.preventDefault();
            this.navigateItems(e.key === 'ArrowUp' ? -1 : 1);
        }
        // Enter 复制选中项目
        else if (e.key === 'Enter' && this.selectedIndex >= 0) {
            this.copyItem(this.selectedIndex);
        }
        // Delete 删除选中项目
        else if (e.key === 'Delete' && this.selectedIndex >= 0) {
            this.showDeleteConfirm(this.selectedIndex);
        }
    }
    
    /**
     * 导航项目
     */
    navigateItems(direction) {
        let items;
        
        if (this.isFavoriteMode) {
            items = this.clipboardItems.filter(item => item.favorite);
        } else if (this.isSearchMode) {
            items = this.filteredItems;
        } else {
            items = this.clipboardItems;
        }
        
        // 应用类型筛选
        if (this.filterType) {
            items = items.filter(item => item.type === this.filterType);
        }
        
        if (items.length === 0) return;
        
        let newIndex = this.selectedIndex + direction;
        
        if (newIndex < 0) {
            newIndex = items.length - 1;
        } else if (newIndex >= items.length) {
            newIndex = 0;
        }
        
        // 如果是搜索模式、收藏模式或类型筛选，需要找到实际索引
        if (this.isSearchMode || this.isFavoriteMode || this.filterType) {
            const actualIndex = this.clipboardItems.findIndex(
                item => item.hash === items[newIndex].hash
            );
            this.selectItem(actualIndex);
        } else {
            this.selectItem(newIndex);
        }
        
        // 滚动到可见区域
        this.scrollToSelected();
    }
    
    /**
     * 滚动到选中项目
     */
    scrollToSelected() {
        const selectedItem = this.clipboardList.querySelector('.clipboard-item.selected');
        if (selectedItem) {
            selectedItem.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }
    

    
    /**
     * 切换收藏模式
     */
    toggleFavoriteMode() {
        this.isFavoriteMode = !this.isFavoriteMode;
        
        // 更新按钮状态 - 添加特殊的收藏激活样式
        this.favoriteBtn.classList.toggle('active', this.isFavoriteMode);
        this.favoriteBtn.classList.toggle('favorite-active', this.isFavoriteMode);
        
        // 如果开启收藏模式，关闭搜索模式
        if (this.isFavoriteMode && this.isSearchMode) {
            this.closeSearch();
        }
        
        // 重新渲染列表
        this.renderClipboardList();
    }
    
    /**
     * 切换类型筛选
     */
    toggleTypeFilter(type) {
        // 如果当前已经是这个类型，则取消筛选
        if (this.filterType === type) {
            this.filterType = null;
        } else {
            this.filterType = type;
        }
        
        // 更新按钮状态
        this.textFilterBtn.classList.toggle('active', this.filterType === 'text');
        this.imageFilterBtn.classList.toggle('active', this.filterType === 'image');
        
        // 重新渲染列表
        this.renderClipboardList();
    }
    

    
    /**
     * 处理项目动作
     */
    handleItemAction(action, index) {
        switch (action) {
            case 'copy':
                this.copyItem(index);
                break;
            case 'copyText':
                this.copyTextOnly(index);
                break;
            case 'favorite':
                this.toggleFavorite(index);
                break;
            case 'note':
                this.showNoteEditor(index);
                break;
            case 'delete':
                this.showDeleteConfirm(index);
                break;
        }
    }
    
    /**
     * 显示备注编辑器
     */
    showNoteEditor(index) {
        const item = this.clipboardItems[index];
        if (!item) return;
        
        // 创建备注编辑模态框
        const noteModal = document.createElement('div');
        noteModal.className = 'modal-overlay';
        noteModal.innerHTML = `
            <div class="modal note-modal">
                <div class="modal-header">
                    <h3>编辑备注</h3>
                    <button class="btn btn-icon modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="note-preview">
                        <div class="note-item-preview">${this.escapeHtml(item.preview)}</div>
                    </div>
                    <div class="note-input-group">
                        <label class="note-label">备注内容：</label>
                        <textarea class="note-textarea" placeholder="请输入备注内容..." maxlength="200">${this.escapeHtml(item.note || '')}</textarea>
                        <div class="note-char-count">
                            <span class="current-count">${(item.note || '').length}</span>/200
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary note-cancel">取消</button>
                    <button class="btn btn-primary note-save">保存</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(noteModal);
        
        // 显示模态框（添加active类）
        setTimeout(() => {
            noteModal.classList.add('active');
        }, 10);
        
        // 获取元素
        const textarea = noteModal.querySelector('.note-textarea');
        const charCount = noteModal.querySelector('.current-count');
        const closeBtn = noteModal.querySelector('.modal-close');
        const cancelBtn = noteModal.querySelector('.note-cancel');
        const saveBtn = noteModal.querySelector('.note-save');
        
        // 字符计数
        textarea.addEventListener('input', () => {
            const length = textarea.value.length;
            charCount.textContent = length;
            
            // 超出限制时的样式
            if (length > 200) {
                charCount.parentElement.classList.add('over-limit');
                saveBtn.disabled = true;
            } else {
                charCount.parentElement.classList.remove('over-limit');
                saveBtn.disabled = false;
            }
        });
        
        // 关闭事件
        const closeModal = () => {
            noteModal.classList.remove('active');
            setTimeout(() => {
                if (document.body.contains(noteModal)) {
                    document.body.removeChild(noteModal);
                }
            }, 300); // 等待动画完成
        };
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // 点击背景关闭
        noteModal.addEventListener('click', (e) => {
            if (e.target === noteModal) {
                closeModal();
            }
        });
        
        // 保存事件
        saveBtn.addEventListener('click', async () => {
            const noteText = textarea.value.trim();
            if (noteText.length <= 200) {
                await this.updateItemNote(index, noteText);
                closeModal();
            }
        });
        
        // 键盘事件
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            } else if (e.key === 'Enter' && e.ctrlKey) {
                // Ctrl+Enter 保存
                saveBtn.click();
            }
        });
        
        // 自动聚焦并选中文本
        setTimeout(() => {
            textarea.focus();
            textarea.select();
        }, 100);
    }
    
    /**
     * 更新项目备注
     */
    async updateItemNote(index, note) {
        try {
            const response = await pywebview.api.update_item_note(index, note);
            const result = JSON.parse(response);
            
            if (result.success) {
                // 更新本地数据
                this.clipboardItems[index].note = note;
                // 重新渲染列表
                this.renderClipboardList();
                this.showNotification('备注更新成功', 'success');
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('更新备注失败:', error);
            this.showNotification('更新备注失败', 'error');
        }
    }
    
    /**
     * 显示删除确认（仅收藏项目需要确认）
     */
    showDeleteConfirm(index) {
        // 检查是否为收藏项目
        const item = this.clipboardItems[index];
        if (item && item.favorite) {
            // 收藏项目需要确认
            this.showModal(
                '确认删除',
                '确定要删除这个收藏的剪贴板项目吗？',
                () => this.deleteItem(index)
            );
        } else {
            // 非收藏项目直接删除
            this.deleteItem(index);
        }
    }
    
    /**
     * 显示清空确认
     */
    showClearConfirm() {
        this.showModal(
            '确认清空',
            '确定要清空所有剪贴板项目吗？此操作不可撤销。',
            () => this.clearAllItems()
        );
    }
    
    // 移除设置功能
    
    /**
     * 显示模态框
     */
    showModal(title, message, confirmCallback) {
        this.modalTitle.textContent = title;
        this.modalMessage.textContent = message;
        this.modalOverlay.classList.add('active');
        
        // 移除之前的事件监听器
        this.modalConfirm.replaceWith(this.modalConfirm.cloneNode(true));
        this.modalConfirm = document.getElementById('modalConfirm');
        
        // 添加新的事件监听器
        this.modalConfirm.addEventListener('click', () => {
            this.hideModal();
            if (confirmCallback) {
                confirmCallback();
            }
        });
    }
    
    /**
     * 隐藏模态框
     */
    hideModal() {
        this.modalOverlay.classList.remove('active');
    }
    
    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        const icon = this.notification.querySelector('.notification-icon');
        const messageEl = this.notification.querySelector('.notification-message');
        
        icon.className = `notification-icon ${iconMap[type]}`;
        messageEl.textContent = message;
        
        this.notification.className = `notification ${type} show`;
        
        // 3秒后自动隐藏
        setTimeout(() => {
            this.notification.classList.remove('show');
        }, 3000);
    }
    
    /**
     * 显示空状态
     */
    showEmptyState() {
        this.emptyState.style.display = 'flex';
        this.clipboardList.innerHTML = '';
    }
    
    /**
     * 隐藏空状态
     */
    hideEmptyState() {
        this.emptyState.style.display = 'none';
    }
    
    // 移除状态栏更新逻辑
    
    /**
     * 获取类型图标
     */
    getTypeIcon(type) {
        const iconMap = {
            text: 'fas fa-font',
            image: 'fas fa-image',
            file: 'fas fa-file'
        };
        return iconMap[type] || 'fas fa-question';
    }
    
    /**
     * 获取类型文本
     */
    getTypeText(type) {
        const textMap = {
            text: '文本',
            image: '图片',
            file: '文件'
        };
        return textMap[type] || '未知';
    }
    
    /**
     * 获取相对时间
     */
    getTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) {
            return `${days}天前`;
        } else if (hours > 0) {
            return `${hours}小时前`;
        } else if (minutes > 0) {
            return `${minutes}分钟前`;
        } else {
            return '刚刚';
        }
    }
    
    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 显示设置页面
     */
    /**
     * 显示设置页面并动态调整尺寸
     */
    showSettings() {
        this.loadSettings();
        this.settingsModal.classList.add('active');
        this.toggleAutoDeleteOptions();
        
        // 动态设置模态框尺寸以适应窗口
        this.adjustModalSize();
        
        // 监听窗口大小变化
        window.addEventListener('resize', this.adjustModalSize);
    }
    
    /**
     * 隐藏设置页面
     */
    hideSettings() {
        this.settingsModal.classList.remove('active');
        
        // 移除窗口大小变化监听器
        window.removeEventListener('resize', this.adjustModalSize);
    }
    
    /**
     * 动态调整模态框尺寸以适应窗口
     */
    /**
     * 动态调整模态框尺寸以适应窗口大小
     */
    adjustModalSize() {
        if (!this.settingsModal) return;
        
        // 获取窗口尺寸
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // 计算可用高度（减去四周间距）
        const padding = 40; // 上下左右各20px间距
        const availableHeight = windowHeight - padding;
        
        // 计算模态框尺寸（留出边距）
        const modalWidth = Math.min(windowWidth * 0.9, 800); // 最大90%宽度，但不超过800px
        const modalHeight = Math.min(availableHeight * 0.95, 700); // 使用可用高度的95%
        
        // 确保最小尺寸
        const finalWidth = Math.max(modalWidth, 400); // 最小宽度400px
        const finalHeight = Math.max(modalHeight, 350); // 最小高度350px
        
        // 应用尺寸
        const modalContent = this.settingsModal.querySelector('.settings-modal');
        if (modalContent) {
            modalContent.style.width = finalWidth + 'px';
            modalContent.style.height = finalHeight + 'px';
            modalContent.style.maxWidth = 'none'; // 移除CSS中的最大宽度限制
            modalContent.style.maxHeight = 'none'; // 移除CSS中的最大高度限制
            
            // 确保modal-body可以正常滚动
            const modalBody = modalContent.querySelector('.modal-body');
            if (modalBody) {
                // 清除任何固定高度设置，让flex布局和overflow-y: auto处理滚动
                modalBody.style.height = '';
                modalBody.style.maxHeight = '';
                // 确保滚动样式正确应用
                modalBody.style.overflowY = 'auto';
            }
        }
    }
    
    /**
     * 关闭设置页面并保存设置
     */
    /**
     * 关闭设置页面并静默保存设置（不显示通知）
     */
    async closeSettingsWithSave() {
        console.log('关闭设置页面，先保存设置...');
        
        // 获取当前设置
        this.settings.autoDelete.enabled = this.autoDeleteEnabled.checked;
        this.settings.autoDelete.byTime = this.deleteByTime.checked;
        this.settings.autoDelete.byCount = this.deleteByCount.checked;
        this.settings.autoDelete.days = parseInt(this.deleteDays.value) || 7;
        this.settings.autoDelete.maxItems = parseInt(this.maxItems.value) || 100;
        
        try {
            // 检查API是否可用
            if (!pywebview || !pywebview.api) {
                console.error('PyWebView API 不可用，无法保存设置');
                this.hideSettings();
                return;
            }
            
            console.log('保存设置:', this.settings);
            const response = await pywebview.api.save_settings(JSON.stringify(this.settings));
            const result = JSON.parse(response);
            
            if (result.success) {
                console.log('设置保存成功');
                // 移除通知显示，静默保存
            } else {
                console.error('保存设置失败:', result.message);
                // 移除通知显示，静默保存
            }
        } catch (error) {
            console.error('保存设置异常:', error);
            // 移除通知显示，静默保存
        }
        
        // 无论保存是否成功，都关闭设置页面
        this.hideSettings();
    }
    
    /**
     * 加载设置
     */
    async loadSettings() {
        try {
            const response = await pywebview.api.get_settings();
            const result = JSON.parse(response);
            if (result.success) {
                this.settings = { ...this.settings, ...result.data };
            }
        } catch (error) {
            console.log('加载设置失败，使用默认设置:', error);
        }
        
        // 更新UI
        this.autoDeleteEnabled.checked = this.settings.autoDelete.enabled;
        this.deleteByTime.checked = this.settings.autoDelete.byTime;
        this.deleteByCount.checked = this.settings.autoDelete.byCount;
        this.deleteDays.value = this.settings.autoDelete.days;
        this.maxItems.value = this.settings.autoDelete.maxItems;
    }
    
    /**
     * 自动保存设置（不显示通知，不关闭设置页面）
     * 使用防抖机制，避免频繁保存
     */
    autoSaveSettings() {
        // 清除之前的定时器
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // 设置新的定时器，500ms后执行保存
        this.autoSaveTimer = setTimeout(async () => {
            // 获取表单数据
            this.settings.autoDelete.enabled = this.autoDeleteEnabled.checked;
            this.settings.autoDelete.byTime = this.deleteByTime.checked;
            this.settings.autoDelete.byCount = this.deleteByCount.checked;
            this.settings.autoDelete.days = parseInt(this.deleteDays.value) || 7;
            this.settings.autoDelete.maxItems = parseInt(this.maxItems.value) || 100;
            
            console.log('准备保存设置:', this.settings); // 调试日志
            
            try {
                // 检查API是否可用
                if (!pywebview || !pywebview.api) {
                    console.error('PyWebView API 不可用');
                    return;
                }
                
                const response = await pywebview.api.save_settings(JSON.stringify(this.settings));
                console.log('API响应:', response); // 调试日志
                
                const result = JSON.parse(response);
                
                if (result.success) {
                    console.log('设置保存成功');
                } else {
                    console.error('自动保存设置失败:', result.message);
                    this.showNotification('设置保存失败: ' + result.message, 'error');
                }
            } catch (error) {
                console.error('自动保存设置失败:', error);
                this.showNotification('设置保存失败: ' + error.message, 'error');
            }
        }, 500);
    }
    
    /**
     * 手动保存设置（保留原方法以备其他地方调用）
     */
    async saveSettings() {
        await this.autoSaveSettings();
        this.showNotification('设置保存成功', 'success');
    }
    
    /**
     * 测试保存设置功能
     */
    async testSaveSettings() {
        console.log('开始测试保存设置...');
        
        // 获取当前设置
        this.settings.autoDelete.enabled = this.autoDeleteEnabled.checked;
        this.settings.autoDelete.byTime = this.deleteByTime.checked;
        this.settings.autoDelete.byCount = this.deleteByCount.checked;
        this.settings.autoDelete.days = parseInt(this.deleteDays.value) || 7;
        this.settings.autoDelete.maxItems = parseInt(this.maxItems.value) || 100;
        
        console.log('当前设置:', this.settings);
        
        try {
            // 检查API是否可用
            if (!pywebview || !pywebview.api) {
                const errorMsg = 'PyWebView API 不可用';
                console.error(errorMsg);
                this.showNotification(errorMsg, 'error');
                return;
            }
            
            console.log('调用API保存设置...');
            const response = await pywebview.api.save_settings(JSON.stringify(this.settings));
            console.log('API响应:', response);
            
            const result = JSON.parse(response);
            
            if (result.success) {
                console.log('设置保存成功');
                this.showNotification('设置保存成功！请检查 %APPDATA%\\Copee\\settings.json 文件', 'success');
            } else {
                console.error('保存设置失败:', result.message);
                this.showNotification('设置保存失败: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('保存设置异常:', error);
            this.showNotification('设置保存异常: ' + error.message, 'error');
        }
    }
    
    /**
     * 切换自动删除选项显示
     */
    toggleAutoDeleteOptions() {
        const enabled = this.autoDeleteEnabled.checked;
        const options = document.querySelector('.auto-delete-options');
        
        if (enabled) {
            options.style.display = 'block';
        } else {
            options.style.display = 'none';
        }
    }
    
    /**
     * 切换时间删除组显示
     */
    toggleTimeDeleteGroup() {
        const enabled = this.deleteByTime.checked;
        const group = document.querySelector('.time-delete-group');
        
        if (enabled) {
            group.style.display = 'block';
        } else {
            group.style.display = 'none';
        }
    }
    
    /**
     * 切换条数删除组显示
     */
    toggleCountDeleteGroup() {
        const enabled = this.deleteByCount.checked;
        const group = document.querySelector('.count-delete-group');
        
        if (enabled) {
            group.style.display = 'block';
        } else {
            group.style.display = 'none';
        }
    }
    
    /**
     * 隐藏窗口
     */
    async hideWindow() {
        try {
            await pywebview.api.hide_window();
        } catch (error) {
            console.error('隐藏窗口失败:', error);
        }
    }
}

/**
 * 全局函数 - 供Python调用
 */
window.updateClipboardList = async function() {
    if (window.clipboardUI) {
        await window.clipboardUI.loadClipboardItems();
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.clipboardUI = new ModernClipboardUI();
});