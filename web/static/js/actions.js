/**
 * actions.js - 用户操作函数
 */

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
            <div class="popup-content image-preview-content">
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

// 导出
window.executeCommand = executeCommand;
window.generateImage = generateImage;
window.previewImage = previewImage;
window.showImagePreviewPopup = showImagePreviewPopup;
window.generateVideo = generateVideo;
window.previewVideo = previewVideo;
window.showSettingsDetail = showSettingsDetail;
window.hideSettingsDetail = hideSettingsDetail;
window.checkApiStatus = checkApiStatus;
