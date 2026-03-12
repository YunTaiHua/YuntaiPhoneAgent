/**
 * utils.js - 工具函数
 */

// ==================== 弹窗管理 ====================
function registerPopup(popup) {
    state.activePopups.push(popup);
    // 确保只有一个ESC处理器
    if (!state.escHandler) {
        state.escHandler = (e) => {
            if (e.key === 'Escape' && state.activePopups.length > 0) {
                const lastPopup = state.activePopups[state.activePopups.length - 1];
                closePopup(lastPopup);
            }
        };
        document.addEventListener('keydown', state.escHandler);
    }
}

function closePopup(popup) {
    if (!popup) return;
    const index = state.activePopups.indexOf(popup);
    if (index > -1) {
        state.activePopups.splice(index, 1);
    }
    popup.remove();
    // 如果没有活动弹窗，移除ESC处理器
    if (state.activePopups.length === 0 && state.escHandler) {
        document.removeEventListener('keydown', state.escHandler);
        state.escHandler = null;
    }
}

function closeAllPopups() {
    state.activePopups.forEach(popup => popup.remove());
    state.activePopups = [];
    if (state.escHandler) {
        document.removeEventListener('keydown', state.escHandler);
        state.escHandler = null;
    }
}

// ==================== 输出和日志 ====================
function appendOutput(text) {
    if (elements.outputText) {
        elements.outputText.value += text;
        elements.outputText.scrollTop = elements.outputText.scrollHeight;
    }
}

function appendLog(type, text) {
    const logElement = type === 'image' ? elements.imageLog :
                       type === 'video' ? elements.videoLog :
                       type === 'tts' ? elements.ttsLog : null;
    if (logElement) {
        // 检查元素类型，div使用textContent，textarea使用value
        if (logElement.tagName === 'TEXTAREA') {
            logElement.value += text;
            logElement.scrollTop = logElement.scrollHeight;
        } else {
            logElement.textContent += text;
            logElement.scrollTop = logElement.scrollHeight;
        }
    }
}

// ==================== Toast提示 ====================
function showToast(message, type = 'info') {
    if (elements.toast) {
        elements.toast.textContent = message;
        elements.toast.className = `toast ${type} show`;
        setTimeout(() => elements.toast.classList.remove('show'), 2000);
    }
}

// ==================== 加载遮罩 ====================
function showLoading(show, text = '正在加载...') {
    if (elements.loadingText) elements.loadingText.textContent = text;
    if (elements.loadingOverlay) elements.loadingOverlay.classList.toggle('show', show);
}

// ==================== 模态框 ====================
function showModal(title, items, onSelect) {
    if (!elements.modalTitle || !elements.modalList) return;

    elements.modalTitle.textContent = title;
    elements.modalList.innerHTML = items.map((item, index) => `
        <div class="modal-list-item" data-index="${index}">${item}</div>
    `).join('');

    let selectedIndex = -1;
    elements.modalList.querySelectorAll('.modal-list-item').forEach(item => {
        item.addEventListener('click', () => {
            elements.modalList.querySelectorAll('.modal-list-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            selectedIndex = parseInt(item.dataset.index);
        });
    });

    elements.modalConfirmBtn.onclick = () => {
        if (selectedIndex >= 0) onSelect(items[selectedIndex]);
        hideModal();
    };

    if (elements.modalOverlay) elements.modalOverlay.classList.add('show');
}

function hideModal() {
    if (elements.modalOverlay) elements.modalOverlay.classList.remove('show');
}

// ==================== 确认对话框 ====================
function showConfirm(title, message) {
    return new Promise((resolve) => {
        if (elements.confirmTitle) elements.confirmTitle.textContent = title;
        if (elements.confirmMessage) elements.confirmMessage.textContent = message;
        if (elements.confirmOverlay) elements.confirmOverlay.classList.add('show');

        elements.confirmOkBtn.onclick = () => {
            if (elements.confirmOverlay) elements.confirmOverlay.classList.remove('show');
            resolve(true);
        };

        elements.confirmCancelBtn.onclick = () => {
            if (elements.confirmOverlay) elements.confirmOverlay.classList.remove('show');
            resolve(false);
        };
    });
}

// ==================== 欢迎遮罩 ====================
function showWelcomeOverlay() {
    // 创建欢迎遮罩层
    const welcomeOverlay = document.createElement('div');
    welcomeOverlay.id = 'welcome-overlay';
    welcomeOverlay.className = 'welcome-overlay';
    welcomeOverlay.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon">👋</div>
            <div class="welcome-text">正在加载，请稍候...</div>
            <div class="welcome-spinner"></div>
        </div>
    `;
    document.body.appendChild(welcomeOverlay);

    // 标记欢迎遮罩已显示
    state.welcomeOverlay = welcomeOverlay;

    // 设置超时机制，最多等待30秒后自动关闭遮罩
    state.welcomeTimeout = setTimeout(() => {
        console.log('欢迎遮罩超时，自动关闭');
        hideWelcomeOverlay();
    }, 30000);
}

function hideWelcomeOverlay() {
    // 清除超时定时器
    if (state.welcomeTimeout) {
        clearTimeout(state.welcomeTimeout);
        state.welcomeTimeout = null;
    }

    const welcomeOverlay = document.getElementById('welcome-overlay');
    if (welcomeOverlay) {
        welcomeOverlay.classList.add('fade-out');
        setTimeout(() => {
            welcomeOverlay.remove();
        }, 500);
    }
}

// 导出
window.registerPopup = registerPopup;
window.closePopup = closePopup;
window.closeAllPopups = closeAllPopups;
window.appendOutput = appendOutput;
window.appendLog = appendLog;
window.showToast = showToast;
window.showLoading = showLoading;
window.showModal = showModal;
window.hideModal = hideModal;
window.showConfirm = showConfirm;
window.showWelcomeOverlay = showWelcomeOverlay;
window.hideWelcomeOverlay = hideWelcomeOverlay;
