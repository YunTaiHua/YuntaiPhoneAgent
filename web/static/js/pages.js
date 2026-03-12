/**
 * pages.js - 页面切换和渲染
 */

// ==================== 页面切换 ====================
function switchPage(pageName) {
    state.currentPage = pageName;
    if (elements.navButtons) {
        elements.navButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.page === pageName));
    }
    if (elements.pages) {
        elements.pages.forEach(page => page.classList.toggle('active', page.id === `page-${pageName}`));
    }
    sendMessage('get_page_data', { page: pageName });

    // 重新初始化页面元素和事件（解决页面切换后按钮不能点击的问题）
    setTimeout(() => {
        initElements();
        rebindPageEvents(pageName);
    }, 100);
}

// 重新绑定页面特定事件
function rebindPageEvents(pageName) {
    // 不再使用eventsBound标志，因为会导致页面切换后事件失效
    // 改为在绑定前移除旧事件（使用cloneNode方式）

    if (pageName === 'dashboard') {
        // 控制中心页面 - 重新绑定按钮事件
        if (elements.clearBtn) {
            const newBtn = elements.clearBtn.cloneNode(true);
            elements.clearBtn.parentNode.replaceChild(newBtn, elements.clearBtn);
            elements.clearBtn = newBtn;
            newBtn.addEventListener('click', async () => {
                const confirmed = await showConfirm('确认清空', '确定要清空输出内容吗？');
                if (confirmed) {
                    if (elements.outputText) elements.outputText.value = '';
                    sendMessage('clear_output');
                    showToast('输出已清空', 'success');
                }
            });
        }
        if (elements.scrcpyBtn) {
            const newBtn = elements.scrcpyBtn.cloneNode(true);
            elements.scrcpyBtn.parentNode.replaceChild(newBtn, elements.scrcpyBtn);
            elements.scrcpyBtn = newBtn;
            newBtn.addEventListener('click', () => showScrcpyPopup());
        }
        if (elements.ttsBtn) {
            const newBtn = elements.ttsBtn.cloneNode(true);
            elements.ttsBtn.parentNode.replaceChild(newBtn, elements.ttsBtn);
            elements.ttsBtn = newBtn;
            newBtn.addEventListener('click', () => showTTSSettingsPopup());
        }
    } else if (pageName === 'connection') {
        // 设备管理页面
        if (elements.detectDevicesBtn) {
            const newBtn = elements.detectDevicesBtn.cloneNode(true);
            elements.detectDevicesBtn.parentNode.replaceChild(newBtn, elements.detectDevicesBtn);
            elements.detectDevicesBtn = newBtn;
            newBtn.addEventListener('click', () => showDeviceDetectPopup());
        }
    } else if (pageName === 'tts') {
        // TTS页面 - 重新绑定选择按钮
        document.querySelectorAll('.tts-select-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', () => {
                const modelType = newBtn.dataset.model;
                const modelKeyMap = {
                    'gpt': 'gpt_models',
                    'sovits': 'sovits_models',
                    'audio': 'audio_files',
                    'text': 'text_files'
                };
                const modelKey = modelKeyMap[modelType] || `${modelType}_models`;
                const models = state.ttsModels[modelKey] || [];

                if (models.length === 0) {
                    showToast('没有可用的模型，请先点击"加载模型"', 'warning');
                    return;
                }
                const titles = {
                    gpt: '选择GPT模型',
                    sovits: '选择SoVITS模型',
                    audio: '选择参考音频',
                    text: '选择参考文本'
                };
                showModal(titles[modelType], models, (selected) => {
                    sendMessage('tts_select_model', { model_type: modelType, model_name: selected });
                });
            });
        });
    }
}

function handlePageData(page, data) {
    if (page === 'tts') {
        state.ttsModels = data.models || state.ttsModels;
        updateTTSLabels();
        renderAudioList(data.audio_history);
    } else if (page === 'connection') {
        renderDeviceList(data.devices);
    } else if (page === 'history') {
        renderHistory(data.history);
    } else if (page === 'dynamic') {
        // 动态功能页面数据
    }
}

// ==================== 选项卡切换 ====================
function switchTab(tabName) {
    if (elements.tabButtons) {
        elements.tabButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabName));
    }
    if (elements.tabContents) {
        elements.tabContents.forEach(content => content.classList.toggle('active', content.id === `tab-${tabName}`));
    }
}

// ==================== 主题切换 ====================
function toggleTheme() {
    state.darkTheme = !state.darkTheme;
    document.documentElement.setAttribute('data-theme', state.darkTheme ? 'dark' : 'light');
    if (elements.themeToggle) elements.themeToggle.textContent = state.darkTheme ? '☀️' : '🌙';
    sendMessage('toggle_theme');
}

// 导出
window.switchPage = switchPage;
window.rebindPageEvents = rebindPageEvents;
window.handlePageData = handlePageData;
window.switchTab = switchTab;
window.toggleTheme = toggleTheme;
