/**
 * events.js - 事件绑定和初始化
 */

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
            if (e.key === 'Enter') {
                if (e.ctrlKey) {
                    // Ctrl+Enter: 插入换行
                    e.preventDefault();
                    const textarea = e.target;
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    const value = textarea.value;
                    textarea.value = value.substring(0, start) + '\n' + value.substring(end);
                    textarea.selectionStart = textarea.selectionEnd = start + 1;
                    // 触发input事件以调整高度
                    textarea.dispatchEvent(new Event('input'));
                } else {
                    // 普通Enter: 发送命令
                    e.preventDefault();
                    executeCommand();
                }
            }
        });
        elements.commandInput.addEventListener('input', function() {
            this.style.height = '42px';
            this.style.height = Math.min(this.scrollHeight, 175) + 'px';
        });
    }

    // 控制中心按钮
    if (elements.executeBtn) elements.executeBtn.addEventListener('click', executeCommand);
    if (elements.terminateBtn) elements.terminateBtn.addEventListener('click', () => {
        // 点击终止时，两个按钮都禁用
        if (elements.executeBtn) elements.executeBtn.disabled = true;
        if (elements.terminateBtn) elements.terminateBtn.disabled = true;
        sendMessage('terminate');
    });
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
        elements.audioDeleteBtn.addEventListener('click', async () => {
            const confirmed = await showConfirm('确认删除', '确定要删除所有历史音频文件吗？此操作不可恢复！');
            if (confirmed) {
                sendMessage('delete_all_audio');
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
    // 显示欢迎遮罩
    showWelcomeOverlay();
    // 加载保存的连接配置
    loadConnectionConfig();
    // 加载版本号
    loadVersion();
}

// 加载版本号
async function loadVersion() {
    try {
        const response = await fetch('/api/version');
        const data = await response.json();
        const versionEl = $('version');
        if (versionEl && data.version) {
            versionEl.textContent = `Version ${data.version}`;
        }
    } catch (e) {
        console.log('获取版本号失败:', e);
    }
}

document.addEventListener('DOMContentLoaded', init);

// 导出
window.initElements = initElements;
window.initEventListeners = initEventListeners;
window.init = init;
