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
        
        // 搜索事件
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        this.searchInput.addEventListener('keydown', (e) => this.handleSearchKeydown(e));
        this.searchClose.addEventListener('click', () => this.closeSearch());
        
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
        const typeIcon = this.getTypeIcon(item.type);
        const timeAgo = this.getTimeAgo(new Date(item.timestamp));
        const isSelected = index === this.selectedIndex ? 'selected' : '';
        const isFavorite = item.favorite || false; // 检查是否收藏
        
        // 根据内容类型设置不同的图标和预览
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
        
        return `
            <div class="clipboard-item ${isSelected}" data-index="${index}">
                <div class="item-content">
                    <div class="item-icon">
                        <i class="${typeIcon}"></i>
                    </div>
                    <div class="item-text">
                        <div class="item-preview">${preview}</div>
                        <div class="item-meta">
                            <span class="item-type">${this.getTypeText(item.type)}</span>
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
                this.showNotification(result.message, 'success');
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
                this.showNotification(result.message || '项目已删除', 'success');
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
        if (!keyword.trim()) {
            this.filteredItems = [...this.clipboardItems];
            this.renderClipboardList();
            return;
        }
        
        try {
            const response = await pywebview.api.search_items(keyword);
            const result = JSON.parse(response);
            
            if (result.success) {
                this.filteredItems = result.data;
                this.renderClipboardList();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showNotification('搜索失败', 'error');
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
            case 'delete':
                this.showDeleteConfirm(index);
                break;
        }
    }
    
    /**
     * 显示删除确认
     */
    showDeleteConfirm(index) {
        this.showModal(
            '确认删除',
            '确定要删除这个剪贴板项目吗？',
            () => this.deleteItem(index)
        );
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