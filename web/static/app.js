/**
 * app.js - Phone Agent Web 前端逻辑
 * 完整版本 - 与GUI功能一致
 */

// ==================== 全局状态 ====================
const state = {
    ws: null,
    connected: false,
    executing: false,
    continuousMode: false,
    darkTheme: false,
    ttsEnabled: false,
    attachedFiles: [],
    currentPage: 'dashboard',
    deviceType: 'android',
    connectionType: 'wireless',
    selectedDevice: null,
    selectedAudio: null,
    ttsModels: {
        gpt: [], sovits: [], audio: [], text: [],
        currentGpt: null, currentSovits: null, currentAudio: null, currentText: null
    },
    shortcuts: {},
    history: [],
    devices: [],
    generatedImagePath: null,
    generatedVideoPath: null,
    activePopups: [],  // 活动弹窗列表
    escHandler: null,  // ESC键处理器
    eventsBound: false  // 事件绑定标志
};

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

// ==================== DOM元素 ====================
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const elements = {};

// ==================== 初始化DOM元素 ====================
function initElements() {
    // 导航
    elements.navButtons = $$('.nav-btn');
    elements.connectionIndicator = $('connection-indicator');
    elements.ttsIndicator = $('tts-indicator');
    elements.themeToggle = $('theme-toggle');
    elements.pages = $$('.page');
    
    // 控制中心
    elements.outputText = $('output-text');
    elements.commandInput = $('command-input');
    elements.executeBtn = $('execute-btn');
    elements.terminateBtn = $('terminate-btn');
    elements.clearBtn = $('clear-btn');
    elements.enterBtn = $('enter-btn');
    elements.ttsBtn = $('tts-btn');
    elements.scrcpyBtn = $('scrcpy-btn');
    elements.attachedFiles = $('attached-files');
    elements.shortcutsGrid = $('shortcuts-grid');
    elements.fileList = $('file-list');
    elements.uploadBtn = $('upload-btn');
    elements.fileInput = $('file-input');
    
    // 设备管理
    elements.connectionStatus = $('connection-status');
    elements.deviceTypeSelect = $('device-type-select');
    elements.usbOption = $('usb-option');
    elements.wirelessOption = $('wireless-option');
    elements.usbSection = $('usb-section');
    elements.wirelessSection = $('wireless-section');
    elements.usbDeviceId = $('usb-device-id');
    elements.ipAddress = $('ip-address');
    elements.portNumber = $('port-number');
    elements.detectDevicesBtn = $('detect-devices-btn');
    elements.connectBtn = $('connect-btn');
    elements.disconnectBtn = $('disconnect-btn');
    elements.deviceList = $('device-list');
    
    // TTS
    elements.ttsGptLabel = $('tts-gpt-label');
    elements.ttsSovitsLabel = $('tts-sovits-label');
    elements.ttsAudioLabel = $('tts-audio-label');
    elements.ttsTextLabel = $('tts-text-label');
    elements.ttsTextInput = $('tts-text-input');
    elements.ttsLog = $('tts-log');
    elements.audioList = $('audio-list');
    elements.ttsSynthBtn = $('tts-synth-btn');
    elements.ttsLoadBtn = $('tts-load-btn');
    elements.ttsStopBtn = $('tts-stop-btn');
    elements.audioPlayBtn = $('audio-play-btn');
    elements.audioRefreshBtn = $('audio-refresh-btn');
    elements.audioDeleteBtn = $('audio-delete-btn');
    
    // 历史记录
    elements.historyList = $('history-list');
    elements.refreshHistoryBtn = $('refresh-history-btn');
    elements.clearHistoryBtn = $('clear-history-btn');
    
    // 动态功能
    elements.tabButtons = $$('.tab-btn');
    elements.tabContents = $$('.tab-content');
    elements.imagePrompt = $('image-prompt');
    elements.imageSize = $('image-size');
    elements.imageQuality = $('image-quality');
    elements.generateImageBtn = $('generate-image-btn');
    elements.previewImageBtn = $('preview-image-btn');
    elements.imageLog = $('image-log');
    elements.videoPrompt = $('video-prompt');
    elements.imageUrl1 = $('image-url1');
    elements.imageUrl2 = $('image-url2');
    elements.videoSize = $('video-size');
    elements.videoFps = $('video-fps');
    elements.videoQuality = $('video-quality');
    elements.videoAudio = $('video-audio');
    elements.generateVideoBtn = $('generate-video-btn');
    elements.previewVideoBtn = $('preview-video-btn');
    elements.videoLog = $('video-log');
    
    // 设置
    elements.settingsCards = $$('.settings-card');
    elements.settingsDetail = $('settings-detail');
    elements.settingsDetailTitle = $('settings-detail-title');
    elements.settingsDetailContent = $('settings-detail-content');
    elements.settingsBackBtn = $('settings-back-btn');
    
    // 通用
    elements.toast = $('toast');
    elements.loadingOverlay = $('loading-overlay');
    elements.loadingText = $('loading-text');
    elements.modalOverlay = $('modal-overlay');
    elements.modalTitle = $('modal-title');
    elements.modalList = $('modal-list');
    elements.modalCancelBtn = $('modal-cancel-btn');
    elements.modalConfirmBtn = $('modal-confirm-btn');
    elements.confirmOverlay = $('confirm-overlay');
    elements.confirmTitle = $('confirm-title');
    elements.confirmMessage = $('confirm-message');
    elements.confirmCancelBtn = $('confirm-cancel-btn');
    elements.confirmOkBtn = $('confirm-ok-btn');
    elements.audioPlayer = $('audio-player');
}

// ==================== WebSocket连接 ====================
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onopen = () => {
        console.log('WebSocket连接成功');
        state.connected = true;
    };
    
    state.ws.onclose = () => {
        console.log('WebSocket连接断开');
        state.connected = false;
        setTimeout(connectWebSocket, 5000);
    };
    
    state.ws.onerror = (error) => console.error('WebSocket错误:', error);
    
    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

function sendMessage(type, data = {}) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type, ...data }));
    }
}

function handleMessage(data) {
    switch (data.type) {
        case 'init':
            updateState(data.data);
            if (data.tts_models) {
                state.ttsModels = data.tts_models;
                updateTTSLabels();
            }
            break;
        case 'output':
            appendOutput(data.data);
            break;
        case 'clear_output':
            if (elements.outputText) elements.outputText.value = '';
            break;
        case 'toast':
            showToast(data.message, data.msg_type);
            break;
        case 'state_update':
            updateState(data.data);
            break;
        case 'tts_loading':
            showLoading(data.show, data.message);
            break;
        case 'tts_models_update':
            state.ttsModels = data.data;
            updateTTSLabels();
            break;
        case 'tts_synth_complete':
            if (data.audio_path && elements.audioPlayer) {
                elements.audioPlayer.src = data.audio_path;
                // 尝试自动播放，处理浏览器自动播放策略
                elements.audioPlayer.play().catch(e => {
                    console.log('自动播放被阻止，需要用户交互');
                    showToast('点击播放按钮播放音频', 'info');
                });
            }
            // 使用后端发送的audio_history更新列表
            if (data.audio_history) {
                renderAudioList(data.audio_history);
            } else {
                refreshAudioList();
            }
            break;
        case 'page_data':
            handlePageData(data.page, data.data);
            break;
        case 'devices_update':
            renderDeviceList(data.devices);
            break;
        case 'audio_deleted':
            renderAudioList(data.audio_history);
            break;
        case 'history_cleared':
            renderHistory([]);
            break;
        case 'image_generated':
            state.generatedImagePath = data.image_path;
            appendLog('image', `✅ 图像生成成功: ${data.image_path}\n`);
            break;
        case 'video_generated':
            state.generatedVideoPath = data.video_path;
            appendLog('video', `✅ 视频生成成功: ${data.video_path}\n`);
            break;
        case 'scrcpy_started':
            showToast('手机投屏已启动', 'success');
            break;
        case 'tts_log':
            // TTS日志输出
            appendLog('tts', data.message || '');
            break;
        case 'image_log':
            // 图像生成日志输出
            appendLog('image', data.message || '');
            break;
        case 'video_log':
            // 视频生成日志输出
            appendLog('video', data.message || '');
            break;
        case 'agent_output':
            // Phone Agent执行输出
            appendOutput(data.message || '');
            break;
        // 新增消息类型处理
        case 'devices_detected':
            // 更新设备检测弹窗
            if (state.currentDetectPopup) {
                const statusEl = state.currentDetectPopup.querySelector('#detect-status');
                const contentEl = state.currentDetectPopup.querySelector('.popup-content');
                if (data.devices && data.devices.length > 0) {
                    if (statusEl) statusEl.textContent = `✅ 检测到 ${data.devices.length} 个设备`;
                    if (statusEl) statusEl.style.color = 'var(--success)';
                    if (contentEl) {
                        contentEl.innerHTML = `
                            <div class="popup-section">
                                <div class="popup-section-title">设备列表（可全选复制）:</div>
                                <textarea class="popup-textarea" readonly>${data.devices.map((d, i) => `${i+1}. ${d}`).join('\n')}</textarea>
                            </div>
                        `;
                    }
                } else {
                    if (statusEl) statusEl.textContent = '❌ 未检测到任何设备';
                    if (statusEl) statusEl.style.color = 'var(--danger)';
                    if (contentEl) {
                        contentEl.innerHTML = `
                            <div class="popup-section">
                                <div class="popup-section-title">故障排除指南:</div>
                                <textarea class="popup-textarea" readonly>请检查以下项目：
1. 手机是否已通过USB线连接电脑
2. 手机是否已开启【开发者选项】和【USB调试】
3. 连接电脑时，手机上是否点击了【允许USB调试】
4. 尝试重新插拔USB线或重启ADB服务
5. 如果是无线连接，请确保IP和端口正确</textarea>
                            </div>
                        `;
                    }
                }
            }
            break;
        case 'system_check_result':
            // 更新系统检查弹窗
            if (state.currentSystemCheckPopup) {
                const resultEl = state.currentSystemCheckPopup.querySelector('#system-check-result');
                const statusEl = state.currentSystemCheckPopup.querySelector('#system-check-status');
                if (resultEl) resultEl.value = data.result || '';
                if (statusEl) {
                    statusEl.textContent = data.status || '检查完成';
                    statusEl.style.color = data.success ? 'var(--success)' : 'var(--warning)';
                }
            }
            break;
        case 'file_management_result':
            // 更新文件管理弹窗
            if (state.currentFileManagementPopup) {
                const resultEl = state.currentFileManagementPopup.querySelector('#file-management-result');
                if (resultEl) resultEl.value = data.result || '';
            }
            break;
    }
}

// ==================== 状态更新 ====================
function updateState(newState) {
    Object.assign(state, newState);
    
    // 更新连接状态指示器
    if (elements.connectionIndicator) {
        elements.connectionIndicator.textContent = state.is_connected ? `● ${state.device_id}` : '● 未连接';
        elements.connectionIndicator.className = `status-indicator ${state.is_connected ? 'connected' : 'disconnected'}`;
    }
    
    // 更新设备管理页面的连接状态
    if (elements.connectionStatus) {
        elements.connectionStatus.textContent = state.is_connected ? `● 已连接: ${state.device_id}` : '● 未连接';
        elements.connectionStatus.className = `connection-status ${state.is_connected ? 'connected' : ''}`;
    }
    
    // 更新TTS状态指示器
    if (elements.ttsIndicator) {
        elements.ttsIndicator.textContent = state.tts_enabled ? '● TTS: 开' : '● TTS: 关';
        elements.ttsIndicator.className = `status-indicator ${state.tts_enabled ? 'connected' : 'disconnected'}`;
    }
    
    // 更新按钮状态 - 使用 is_executing 而不是 executing
    const isExecuting = state.is_executing || state.executing;
    if (elements.executeBtn) elements.executeBtn.disabled = isExecuting;
    if (elements.terminateBtn) elements.terminateBtn.disabled = !isExecuting;
    if (elements.enterBtn) elements.enterBtn.classList.toggle('visible', isExecuting);
    if (elements.connectBtn) elements.connectBtn.disabled = state.is_connected;
    if (elements.disconnectBtn) elements.disconnectBtn.disabled = !state.is_connected;
    
    updateAttachedFiles();
}

function updateTTSLabels() {
    // currentGpt等存储的是文件路径，需要提取文件名显示
    // 支持两种key格式：current_gpt 和 currentGpt
    const getFileName = (path) => {
        if (!path) return '未选择';
        // 如果是路径，提取文件名
        const parts = path.replace(/\\/g, '/').split('/');
        return parts[parts.length - 1] || path;
    };
    
    // 获取当前模型，支持两种key格式
    const currentGpt = state.ttsModels.currentGpt || state.ttsModels.current_gpt;
    const currentSovits = state.ttsModels.currentSovits || state.ttsModels.current_sovits;
    const currentAudio = state.ttsModels.currentAudio || state.ttsModels.current_audio;
    const currentText = state.ttsModels.currentText || state.ttsModels.current_text;
    
    if (elements.ttsGptLabel) elements.ttsGptLabel.textContent = getFileName(currentGpt);
    if (elements.ttsSovitsLabel) elements.ttsSovitsLabel.textContent = getFileName(currentSovits);
    if (elements.ttsAudioLabel) elements.ttsAudioLabel.textContent = getFileName(currentAudio);
    if (elements.ttsTextLabel) elements.ttsTextLabel.textContent = getFileName(currentText);
}

function updateAttachedFiles() {
    if (!elements.attachedFiles) return;
    
    if (state.attachedFiles.length === 0) {
        elements.attachedFiles.classList.remove('visible');
        elements.attachedFiles.innerHTML = '';
        return;
    }
    
    elements.attachedFiles.classList.add('visible');
    elements.attachedFiles.innerHTML = state.attachedFiles.map((file, index) => `
        <div class="attached-file">
            <span>📌 ${file}</span>
            <button class="file-remove-btn" data-index="${index}">×</button>
        </div>
    `).join('');
    
    elements.attachedFiles.querySelectorAll('.file-remove-btn').forEach(btn => {
        btn.addEventListener('click', () => removeAttachedFile(parseInt(btn.dataset.index)));
    });
}

// ==================== 辅助函数 ====================
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

function showToast(message, type = 'info') {
    if (elements.toast) {
        elements.toast.textContent = message;
        elements.toast.className = `toast ${type} show`;
        setTimeout(() => elements.toast.classList.remove('show'), 2000);
    }
}

function showLoading(show, text = '正在加载...') {
    if (elements.loadingText) elements.loadingText.textContent = text;
    if (elements.loadingOverlay) elements.loadingOverlay.classList.toggle('show', show);
}

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
    // 使用标志防止重复绑定
    if (state.eventsBound) return;

    if (pageName === 'dashboard') {
        // 控制中心页面 - 重新绑定按钮事件
        if (elements.clearBtn) {
            elements.clearBtn.addEventListener('click', async () => {
                const confirmed = await showConfirm('确认清空', '确定要清空输出内容吗？');
                if (confirmed) {
                    if (elements.outputText) elements.outputText.value = '';
                    sendMessage('clear_output');
                    showToast('输出已清空', 'success');
                }
            });
        }
        if (elements.scrcpyBtn) {
            elements.scrcpyBtn.addEventListener('click', () => showScrcpyPopup());
        }
        if (elements.ttsBtn) {
            elements.ttsBtn.addEventListener('click', () => showTTSSettingsPopup());
        }
        if (elements.uploadBtn) {
            elements.uploadBtn.addEventListener('click', () => {
                if (elements.fileInput) elements.fileInput.click();
            });
        }
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileUpload(e.target.files);
                    e.target.value = '';
                }
            });
        }
    } else if (pageName === 'connection') {
        // 设备管理页面
        if (elements.detectDevicesBtn) {
            elements.detectDevicesBtn.addEventListener('click', () => showDeviceDetectPopup());
        }
    } else if (pageName === 'tts') {
        // TTS页面 - 重新绑定选择按钮
        document.querySelectorAll('.tts-select-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const modelType = btn.dataset.model;
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

    state.eventsBound = true;
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

// ==================== 快捷键 ====================
function initShortcuts() {
    fetch('/api/shortcuts')
        .then(res => res.json())
        .then(shortcuts => {
            state.shortcuts = shortcuts;
            renderShortcuts();
        });
}

function renderShortcuts() {
    if (!elements.shortcutsGrid) return;
    
    const icons = { '微信': '💬', 'QQ': '🐧', '抖音': '🎵', '快手': '🎬', '淘宝': '🛒', 'QQ音乐': '🎶' };
    elements.shortcutsGrid.innerHTML = Object.entries(state.shortcuts).map(([key, command]) => {
        const appName = command.replace('打开', '');
        return `<button class="shortcut-btn" data-key="${key}">${icons[appName] || '📱'} ${appName}</button>`;
    }).join('');
    
    elements.shortcutsGrid.querySelectorAll('.shortcut-btn').forEach(btn => {
        btn.addEventListener('click', () => sendMessage('shortcut', { key: btn.dataset.key }));
    });
}

// ==================== 文件上传 ====================
function handleFileUpload(files) {
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append('file', file));

    fetch('/api/upload', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // 更新文件管理卡片中的文件列表
                renderFileList(data.files || data.attached_files || []);
                showToast(`已上传 ${files.length} 个文件`, 'success');
            } else {
                showToast(data.message, 'error');
            }
        });
}

// 渲染文件管理卡片中的文件列表
function renderFileList(files) {
    if (!elements.fileList) return;

    if (!files || files.length === 0) {
        elements.fileList.innerHTML = '<div class="empty-hint">暂无文件</div>';
        return;
    }

    elements.fileList.innerHTML = files.map((file, index) => `
        <div class="file-item">
            <span class="file-name">📄 ${typeof file === 'string' ? file : file.name}</span>
            <button class="file-delete-btn" data-index="${index}">×</button>
        </div>
    `).join('');

    // 绑定删除按钮事件
    elements.fileList.querySelectorAll('.file-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filename = files[parseInt(btn.dataset.index)];
            deleteUploadedFile(typeof filename === 'string' ? filename : filename.name);
        });
    });
}

function deleteUploadedFile(filename) {
    fetch(`/api/upload/${encodeURIComponent(filename)}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderFileList(data.files || data.attached_files || []);
                showToast('已删除文件', 'info');
            }
        });
}

function removeAttachedFile(index) {
    const filename = state.attachedFiles[index];
    fetch(`/api/upload/${encodeURIComponent(filename)}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                state.attachedFiles = data.attached_files;
                updateAttachedFiles();
                showToast('已移除文件', 'info');
            }
        });
}

// ==================== 设备管理 ====================
function renderDeviceList(devices) {
    state.devices = devices || [];
    if (!elements.deviceList) return;
    
    if (state.devices.length === 0) {
        elements.deviceList.innerHTML = '<div class="empty-hint">未找到设备</div>';
        return;
    }
    
    elements.deviceList.innerHTML = state.devices.map(device => `
        <div class="device-item ${state.selectedDevice === device ? 'selected' : ''}" data-id="${device}">
            <div class="device-info">
                <span class="device-id">${device}</span>
                <span class="device-status">可用</span>
            </div>
        </div>
    `).join('');
    
    elements.deviceList.querySelectorAll('.device-item').forEach(item => {
        item.addEventListener('click', () => {
            elements.deviceList.querySelectorAll('.device-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            state.selectedDevice = item.dataset.id;
        });
    });
}

// ==================== TTS ====================
function renderAudioList(audioHistory) {
    if (!elements.audioList) return;
    
    if (!audioHistory || audioHistory.length === 0) {
        elements.audioList.innerHTML = '<div class="empty-hint">暂无历史音频</div>';
        return;
    }
    
    elements.audioList.innerHTML = audioHistory.map(audio => `
        <div class="audio-item ${state.selectedAudio === audio.path ? 'selected' : ''}" data-path="${audio.path}" data-name="${audio.name}">🎵 ${audio.name}</div>
    `).join('');
    
    elements.audioList.querySelectorAll('.audio-item').forEach(item => {
        item.addEventListener('click', () => {
            elements.audioList.querySelectorAll('.audio-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            state.selectedAudio = item.dataset.path;
        });
    });
}

function refreshAudioList() {
    fetch('/api/tts/audio_history')
        .then(res => res.json())
        .then(data => renderAudioList(data));
}

// ==================== 历史记录 ====================
function renderHistory(history) {
    state.history = history || [];
    if (!elements.historyList) return;
    
    if (state.history.length === 0) {
        elements.historyList.innerHTML = '<div class="empty-hint">暂无历史记录</div>';
        return;
    }
    
    elements.historyList.innerHTML = state.history.map(item => `
        <div class="history-item">
            <div class="history-time">${item.timestamp}</div>
            <div class="history-command">💭 ${item.command}</div>
            <div class="history-result">${item.result || '无结果'}</div>
        </div>
    `).join('');
}

function refreshHistory() {
    fetch('/api/history')
        .then(res => res.json())
        .then(data => renderHistory(data));
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

// ==================== 设置页面 ====================
function showSettingsDetail(setting) {
    const settings = {
        connection: {
            title: '连接配置',
            content: `
                <div class="settings-row">
                    <span class="settings-label">设备类型</span>
                    <span class="settings-value">${state.deviceType === 'android' ? 'Android' : 'HarmonyOS'}</span>
                </div>
                <div class="settings-row">
                    <span class="settings-label">连接状态</span>
                    <span class="settings-value">${state.is_connected ? '已连接' : '未连接'}</span>
                </div>
            `
        },
        system: {
            title: '系统检查',
            content: `
                <div class="settings-row">
                    <span class="settings-label">API状态</span>
                    <span class="settings-value" id="api-status">检查中...</span>
                </div>
                <div class="settings-row">
                    <span class="settings-label">版本</span>
                    <span class="settings-value">v1.3.3</span>
                </div>
            `
        },
        tts: {
            title: 'TTS语音配置',
            content: `
                <div class="settings-row">
                    <span class="settings-label">TTS状态</span>
                    <span class="settings-value">${state.tts_enabled ? '已启用' : '未启用'}</span>
                </div>
                <div class="settings-row">
                    <span class="settings-label">GPT模型</span>
                    <span class="settings-value">${state.ttsModels.currentGpt || '未选择'}</span>
                </div>
                <div class="settings-row">
                    <span class="settings-label">SoVITS模型</span>
                    <span class="settings-value">${state.ttsModels.currentSovits || '未选择'}</span>
                </div>
            `
        },
        files: {
            title: '文件管理',
            content: `
                <div class="settings-row">
                    <span class="settings-label">上传目录</span>
                    <span class="settings-value">temp/uploads/</span>
                </div>
                <div class="settings-row">
                    <span class="settings-label">TTS输出目录</span>
                    <span class="settings-value">temp/tts_output/</span>
                </div>
            `
        }
    };
    
    const settingData = settings[setting];
    if (settingData && elements.settingsDetailTitle && elements.settingsDetailContent) {
        elements.settingsDetailTitle.textContent = settingData.title;
        elements.settingsDetailContent.innerHTML = settingData.content;
        elements.settingsDetail.style.display = 'block';
        
        // 检查API状态
        if (setting === 'system') {
            checkApiStatus();
        }
    }
}

function hideSettingsDetail() {
    if (elements.settingsDetail) {
        elements.settingsDetail.style.display = 'none';
    }
}

function checkApiStatus() {
    const apiStatus = $('api-status');
    if (apiStatus) {
        fetch('/api/state')
            .then(res => res.json())
            .then(() => {
                apiStatus.textContent = '正常';
                apiStatus.style.color = 'var(--success)';
            })
            .catch(() => {
                apiStatus.textContent = '异常';
                apiStatus.style.color = 'var(--danger)';
            });
    }
}

// ==================== 主题切换 ====================
function toggleTheme() {
    state.darkTheme = !state.darkTheme;
    document.documentElement.setAttribute('data-theme', state.darkTheme ? 'dark' : 'light');
    if (elements.themeToggle) elements.themeToggle.textContent = state.darkTheme ? '☀️' : '🌙';
    sendMessage('toggle_theme');
}

// ==================== 命令执行 ====================
function executeCommand() {
    const command = elements.commandInput ? elements.commandInput.value.trim() : '';
    if (!command && state.attachedFiles.length === 0) {
        showToast('请输入命令或选择文件', 'warning');
        return;
    }
    sendMessage('command', { command });
    if (elements.commandInput) {
        elements.commandInput.value = '';
        elements.commandInput.style.height = '42px';
    }
}

// ==================== 图像生成 ====================
function generateImage() {
    const prompt = elements.imagePrompt ? elements.imagePrompt.value.trim() : '';
    if (!prompt) {
        showToast('请输入图像描述', 'warning');
        return;
    }
    
    const size = elements.imageSize ? elements.imageSize.value : '1024x1024';
    const quality = elements.imageQuality ? elements.imageQuality.value : 'standard';
    
    appendLog('image', `🎨 正在生成图像...\n描述: ${prompt}\n尺寸: ${size}\n质量: ${quality}\n`);
    
    sendMessage('generate_image', { prompt, size, quality });
}

function previewImage() {
    if (state.generatedImagePath) {
        showImagePreviewPopup(state.generatedImagePath);
    } else {
        showToast('暂无生成的图像', 'warning');
    }
}

// 图像预览弹窗
function showImagePreviewPopup(imagePath) {
    // 关闭所有已存在的弹窗
    closeAllPopups();

    const popup = document.createElement('div');
    popup.id = 'image-preview-popup';
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog image-preview-dialog">
            <div class="popup-header">
                <h3>🖼️ 图像预览</h3>
                <button class="popup-close-btn" id="image-preview-close">✕</button>
            </div>
            <div class="popup-content">
                <img src="${imagePath}" alt="生成的图像" class="preview-image" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'error-hint\\'>图像加载失败<br>路径: ${imagePath}</div>';">
            </div>
            <div class="popup-footer">
                <button class="btn btn-primary" id="image-preview-open">在新窗口打开</button>
                <button class="btn btn-secondary" id="image-preview-close-btn">关闭</button>
            </div>
        </div>
    `;

    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('image-preview-close').addEventListener('click', () => closePopup(popup));
    document.getElementById('image-preview-close-btn').addEventListener('click', () => closePopup(popup));
    document.getElementById('image-preview-open').addEventListener('click', () => window.open(imagePath, '_blank'));
    popup.addEventListener('click', (e) => {
        if (e.target === popup) closePopup(popup);
    });
}

// ==================== 视频生成 ====================
function generateVideo() {
    const prompt = elements.videoPrompt ? elements.videoPrompt.value.trim() : '';
    if (!prompt) {
        showToast('请输入视频描述', 'warning');
        return;
    }
    
    const imageUrl1 = elements.imageUrl1 ? elements.imageUrl1.value.trim() : '';
    const imageUrl2 = elements.imageUrl2 ? elements.imageUrl2.value.trim() : '';
    const size = elements.videoSize ? elements.videoSize.value : '1920x1080';
    const fps = elements.videoFps ? elements.videoFps.value : '30';
    const quality = elements.videoQuality ? elements.videoQuality.value : 'quality';
    const withAudio = elements.videoAudio ? elements.videoAudio.checked : true;
    
    appendLog('video', `🎬 正在生成视频...\n描述: ${prompt}\n尺寸: ${size}\n帧率: ${fps}\n质量: ${quality}\n音效: ${withAudio ? '是' : '否'}\n`);
    
    sendMessage('generate_video', { 
        prompt, 
        image_urls: [imageUrl1, imageUrl2].filter(Boolean),
        size, 
        fps, 
        quality, 
        with_audio: withAudio 
    });
}

function previewVideo() {
    if (state.generatedVideoPath) {
        window.open(state.generatedVideoPath, '_blank');
    } else {
        showToast('暂无生成的视频', 'warning');
    }
}

// ==================== 事件绑定 ====================
function initEventListeners() {
    // 导航
    if (elements.navButtons) {
        elements.navButtons.forEach(btn => btn.addEventListener('click', () => switchPage(btn.dataset.page)));
    }
    
    // 主题
    if (elements.themeToggle) elements.themeToggle.addEventListener('click', toggleTheme);
    
    // 命令输入
    if (elements.commandInput) {
        elements.commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.ctrlKey) {
                e.preventDefault();
                executeCommand();
            }
        });
        elements.commandInput.addEventListener('input', function() {
            this.style.height = '42px';
            this.style.height = Math.min(this.scrollHeight, 175) + 'px';
        });
    }
    
    // 控制中心按钮
    if (elements.executeBtn) elements.executeBtn.addEventListener('click', executeCommand);
    if (elements.terminateBtn) elements.terminateBtn.addEventListener('click', () => sendMessage('terminate'));
    // 清空历史按钮 - 需要确认（与GUI一致）
    if (elements.clearBtn) elements.clearBtn.addEventListener('click', async () => {
        const confirmed = await showConfirm('确认清空', '确定要清空输出内容吗？');
        if (confirmed) {
            if (elements.outputText) elements.outputText.value = '';
            sendMessage('clear_output');
            showToast('输出已清空', 'success');
        }
    });
    if (elements.enterBtn) elements.enterBtn.addEventListener('click', () => sendMessage('simulate_enter'));
    // 语音播报按钮 - 显示TTS设置弹窗（与GUI一致）
    if (elements.ttsBtn) {
        elements.ttsBtn.addEventListener('click', () => showTTSSettingsPopup());
    }
    // 手机投屏按钮 - 显示scrcpy设置弹窗（与GUI一致）
    if (elements.scrcpyBtn) {
        elements.scrcpyBtn.addEventListener('click', () => showScrcpyPopup());
    }
    
    // 文件上传
    if (elements.uploadBtn) elements.uploadBtn.addEventListener('click', () => { if (elements.fileInput) elements.fileInput.click(); });
    if (elements.fileInput) {
        elements.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files);
                e.target.value = '';
            }
        });
    }
    
    // 设备管理
    if (elements.deviceTypeSelect) {
        elements.deviceTypeSelect.addEventListener('change', (e) => {
            state.deviceType = e.target.value;
        });
    }
    
    // 连接方式切换
    if (elements.usbOption) {
        elements.usbOption.addEventListener('change', () => {
            state.connectionType = 'usb';
            if (elements.usbSection) elements.usbSection.style.display = 'block';
            if (elements.wirelessSection) elements.wirelessSection.style.display = 'none';
        });
    }
    if (elements.wirelessOption) {
        elements.wirelessOption.addEventListener('change', () => {
            state.connectionType = 'wireless';
            if (elements.usbSection) elements.usbSection.style.display = 'none';
            if (elements.wirelessSection) elements.wirelessSection.style.display = 'block';
        });
    }
    
    // 检测设备按钮 - 显示设备检测结果弹窗（与GUI一致）
    if (elements.detectDevicesBtn) {
        elements.detectDevicesBtn.addEventListener('click', () => showDeviceDetectPopup());
    }
    if (elements.connectBtn) {
        elements.connectBtn.addEventListener('click', () => {
            const connectData = {
                device_type: state.deviceType,
                connection_type: state.connectionType
            };
            
            if (state.connectionType === 'usb') {
                connectData.device_id = elements.usbDeviceId ? elements.usbDeviceId.value.trim() : '';
            } else {
                connectData.ip = elements.ipAddress ? elements.ipAddress.value.trim() : '';
                connectData.port = elements.portNumber ? elements.portNumber.value.trim() : '5555';
            }
            
            sendMessage('connect_device', connectData);
        });
    }
    if (elements.disconnectBtn) elements.disconnectBtn.addEventListener('click', () => sendMessage('disconnect_device'));
    
    // TTS模型选择
    document.querySelectorAll('.tts-select-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const modelType = btn.dataset.model;
            // 正确的key映射
            const modelKeyMap = {
                'gpt': 'gpt_models',
                'sovits': 'sovits_models', 
                'audio': 'audio_files',
                'text': 'text_files'
            };
            const modelKey = modelKeyMap[modelType] || `${modelType}_models`;
            const models = state.ttsModels[modelKey] || [];
            
            console.log(`TTS模型选择: type=${modelType}, key=${modelKey}, models=`, models);
            
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
                console.log(`选择了模型: ${modelType} = ${selected}`);
                sendMessage('tts_select_model', { model_type: modelType, model_name: selected });
            });
        });
    });
    
    // TTS操作
    if (elements.ttsSynthBtn) {
        elements.ttsSynthBtn.addEventListener('click', () => {
            const text = elements.ttsTextInput ? elements.ttsTextInput.value.trim() : '';
            if (!text) { showToast('请输入要合成的文本', 'warning'); return; }
            sendMessage('tts_synth', { text });
        });
    }
    if (elements.ttsLoadBtn) elements.ttsLoadBtn.addEventListener('click', () => sendMessage('tts_load_models'));
    if (elements.ttsStopBtn) {
        elements.ttsStopBtn.addEventListener('click', () => { 
            sendMessage('tts_stop'); 
            if (elements.audioPlayer) elements.audioPlayer.pause(); 
        });
    }
    if (elements.audioPlayBtn) {
        elements.audioPlayBtn.addEventListener('click', () => {
            if (state.selectedAudio) { 
                if (elements.audioPlayer) {
                    elements.audioPlayer.src = state.selectedAudio; 
                    elements.audioPlayer.play(); 
                }
            } else { showToast('请先选择音频', 'warning'); }
        });
    }
    if (elements.audioRefreshBtn) elements.audioRefreshBtn.addEventListener('click', refreshAudioList);
    if (elements.audioDeleteBtn) {
        elements.audioDeleteBtn.addEventListener('click', () => {
            if (state.selectedAudio) {
                const filename = state.selectedAudio.split('/').pop();
                sendMessage('delete_audio', { filename });
            } else {
                showToast('请先选择音频', 'warning');
            }
        });
    }
    
    // 历史记录
    if (elements.refreshHistoryBtn) {
        elements.refreshHistoryBtn.addEventListener('click', refreshHistory);
    }
    if (elements.clearHistoryBtn) {
        elements.clearHistoryBtn.addEventListener('click', async () => {
            const confirmed = await showConfirm('确认清空', '确定要清空所有历史记录吗？');
            if (confirmed) {
                sendMessage('clear_history');
            }
        });
    }
    
    // 选项卡切换
    if (elements.tabButtons) {
        elements.tabButtons.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        });
    }
    
    // 动态功能
    if (elements.generateImageBtn) elements.generateImageBtn.addEventListener('click', generateImage);
    if (elements.previewImageBtn) elements.previewImageBtn.addEventListener('click', previewImage);
    if (elements.generateVideoBtn) elements.generateVideoBtn.addEventListener('click', generateVideo);
    if (elements.previewVideoBtn) elements.previewVideoBtn.addEventListener('click', previewVideo);
    
    // 设置页面 - 点击卡片跳转或显示弹窗（与GUI一致）
    if (elements.settingsCards) {
        elements.settingsCards.forEach(card => {
            card.addEventListener('click', () => {
                const setting = card.dataset.setting;
                // 连接配置 -> 跳转到设备管理页面
                if (setting === 'connection') {
                    switchPage('connection');
                }
                // 系统检查 -> 显示系统检查弹窗
                else if (setting === 'system') {
                    showSystemCheckPopup();
                }
                // TTS语音 -> 跳转到TTS页面
                else if (setting === 'tts') {
                    switchPage('tts');
                }
                // 文件管理 -> 显示文件管理弹窗
                else if (setting === 'files') {
                    showFileManagementPopup();
                }
            });
        });
    }
    if (elements.settingsBackBtn) {
        elements.settingsBackBtn.addEventListener('click', hideSettingsDetail);
    }
    
    // 模态框
    if (elements.modalCancelBtn) elements.modalCancelBtn.addEventListener('click', hideModal);
    if (elements.modalOverlay) {
        elements.modalOverlay.addEventListener('click', (e) => { if (e.target === elements.modalOverlay) hideModal(); });
    }
}

// ==================== 初始化 ====================
function init() {
    initElements();
    connectWebSocket();
    initEventListeners();
    initShortcuts();
}

document.addEventListener('DOMContentLoaded', init);

// ==================== 弹窗函数（与GUI一致） ====================

// TTS设置弹窗
function showTTSSettingsPopup() {
    // 获取当前模型，支持两种key格式
    const currentGpt = state.ttsModels.currentGpt || state.ttsModels.current_gpt;
    const currentSovits = state.ttsModels.currentSovits || state.ttsModels.current_sovits;
    const currentAudio = state.ttsModels.currentAudio || state.ttsModels.current_audio;
    
    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog">
            <div class="popup-title">🎤 TTS语音设置</div>
            <div class="popup-subtitle">（语音合成有延迟）</div>
            <div class="popup-content">
                <label class="popup-checkbox">
                    <input type="checkbox" id="tts-enabled-check" ${state.tts_enabled ? 'checked' : ''}>
                    <span>启用语音播报</span>
                </label>
                <div class="popup-section">
                    <div class="popup-section-title">选择TTS模型:</div>
                    <div class="popup-row">
                        <span class="popup-label">GPT模型:</span>
                        <select class="popup-select" id="tts-gpt-select">
                            <option value="">未选择</option>
                            ${(state.ttsModels.gpt_models || []).map(m => `<option value="${m}" ${currentGpt && currentGpt.includes(m) ? 'selected' : ''}>${m}</option>`).join('')}
                        </select>
                    </div>
                    <div class="popup-row">
                        <span class="popup-label">SoVITS模型:</span>
                        <select class="popup-select" id="tts-sovits-select">
                            <option value="">未选择</option>
                            ${(state.ttsModels.sovits_models || []).map(m => `<option value="${m}" ${currentSovits && currentSovits.includes(m) ? 'selected' : ''}>${m}</option>`).join('')}
                        </select>
                    </div>
                    <div class="popup-row">
                        <span class="popup-label">参考音频:</span>
                        <select class="popup-select" id="tts-audio-select">
                            <option value="">未选择</option>
                            ${(state.ttsModels.audio_files || []).map(m => `<option value="${m}" ${currentAudio && currentAudio.includes(m) ? 'selected' : ''}>${m}</option>`).join('')}
                        </select>
                    </div>
                </div>
            </div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="tts-popup-cancel">取消</button>
                <button class="btn btn-primary" id="tts-popup-save">保存设置</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('tts-popup-cancel').addEventListener('click', () => closePopup(popup));
    document.getElementById('tts-popup-save').addEventListener('click', () => {
        const enabled = document.getElementById('tts-enabled-check').checked;
        const gpt = document.getElementById('tts-gpt-select').value;
        const sovits = document.getElementById('tts-sovits-select').value;
        const audio = document.getElementById('tts-audio-select').value;

        // 发送设置到后端
        sendMessage('tts_settings', { enabled, gpt, sovits, audio });
        showToast('TTS设置已保存', 'success');
        closePopup(popup);
    });
    popup.addEventListener('click', (e) => { if (e.target === popup) closePopup(popup); });
}

// 手机投屏弹窗
function showScrcpyPopup() {
    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog">
            <div class="popup-title">📱 手机投屏设置</div>
            <div class="popup-content">
                <div class="popup-section">
                    <div class="popup-section-title">当前设备: ${state.device_id || '未连接'}</div>
                </div>
                <label class="popup-checkbox">
                    <input type="checkbox" id="scrcpy-always-top">
                    <span>窗口置顶</span>
                </label>
            </div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="scrcpy-popup-cancel">取消</button>
                <button class="btn btn-accent" id="scrcpy-popup-start">启动投屏</button>
            </div>
            <div class="popup-info">注意：请确保手机已开启USB调试模式<br>点击其他地方时窗口会自动最小化</div>
        </div>
    `;
    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('scrcpy-popup-cancel').addEventListener('click', () => closePopup(popup));
    document.getElementById('scrcpy-popup-start').addEventListener('click', () => {
        if (!state.is_connected) {
            showToast('请先连接设备', 'warning');
            return;
        }
        const alwaysOnTop = document.getElementById('scrcpy-always-top').checked;
        sendMessage('start_scrcpy', { always_on_top: alwaysOnTop });
        closePopup(popup);
    });
    popup.addEventListener('click', (e) => { if (e.target === popup) closePopup(popup); });
}

// 设备检测弹窗
function showDeviceDetectPopup() {
    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog popup-dialog-large">
            <div class="popup-title">📱 设备检测结果</div>
            <div class="popup-subtitle" id="device-type-label">设备类型: ${state.deviceType === 'harmonyos' ? 'HarmonyOS (HDC)' : 'Android (ADB)'}</div>
            <div class="popup-status" id="detect-status">正在检测设备，请稍候...</div>
            <div class="popup-content">
                <div class="popup-loading">
                    <div class="loading-spinner"></div>
                    <span>正在扫描设备...</span>
                </div>
            </div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="detect-popup-close">关闭</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('detect-popup-close').addEventListener('click', () => closePopup(popup));
    popup.addEventListener('click', (e) => { if (e.target === popup) closePopup(popup); });

    // 发送检测请求
    sendMessage('detect_devices', { device_type: state.deviceType });

    // 保存popup引用以便更新结果
    state.currentDetectPopup = popup;
}

// 系统检查弹窗
function showSystemCheckPopup() {
    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog popup-dialog-large">
            <div class="popup-title">🔍 系统检查</div>
            <div class="popup-subtitle">正在检查系统配置...</div>
            <div class="popup-content">
                <textarea class="popup-textarea" id="system-check-result" readonly>正在准备系统检查，请稍候...</textarea>
            </div>
            <div class="popup-status" id="system-check-status">准备开始检查...</div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="system-check-close">关闭</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('system-check-close').addEventListener('click', () => closePopup(popup));
    popup.addEventListener('click', (e) => { if (e.target === popup) closePopup(popup); });

    // 发送系统检查请求
    sendMessage('system_check');

    // 保存popup引用以便更新结果
    state.currentSystemCheckPopup = popup;
}

// 文件管理弹窗
function showFileManagementPopup() {
    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog popup-dialog-large">
            <div class="popup-title">📁 文件管理</div>
            <div class="popup-content">
                <textarea class="popup-textarea" id="file-management-result" readonly>正在加载文件信息...</textarea>
            </div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="file-management-close">关闭</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    registerPopup(popup);

    // 绑定事件
    document.getElementById('file-management-close').addEventListener('click', () => closePopup(popup));
    popup.addEventListener('click', (e) => { if (e.target === popup) closePopup(popup); });

    // 发送文件管理请求
    sendMessage('get_file_management');

    // 保存popup引用以便更新结果
    state.currentFileManagementPopup = popup;
}
