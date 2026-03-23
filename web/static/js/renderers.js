/**
 * renderers.js - 列表渲染函数
 */

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
                const uploadedFiles = data.attached_files || [];
                renderFileList(uploadedFiles);
                showToast(`已上传 ${uploadedFiles.length} 个文件`, 'success');
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
        // 单击选择
        item.addEventListener('click', () => {
            elements.audioList.querySelectorAll('.audio-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            state.selectedAudio = item.dataset.path;
        });

        // 双击播放
        item.addEventListener('dblclick', () => {
            if (elements.audioPlayer) {
                elements.audioPlayer.src = item.dataset.path;
                elements.audioPlayer.play();
                showToast('正在播放: ' + item.dataset.name, 'info');
            }
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

// ==================== 加载连接配置 ====================
function loadConnectionConfig() {
    fetch('/api/connection_config')
        .then(res => res.json())
        .then(data => {
            if (data && data.ip && elements.ipAddress) {
                elements.ipAddress.value = data.ip;
            }
            if (data && data.port && elements.portNumber) {
                elements.portNumber.value = data.port;
            }
        })
        .catch(err => {
            console.log('加载连接配置失败:', err);
        });
}

// 导出
window.initShortcuts = initShortcuts;
window.renderShortcuts = renderShortcuts;
window.handleFileUpload = handleFileUpload;
window.renderFileList = renderFileList;
window.deleteUploadedFile = deleteUploadedFile;
window.removeAttachedFile = removeAttachedFile;
window.renderDeviceList = renderDeviceList;
window.renderAudioList = renderAudioList;
window.refreshAudioList = refreshAudioList;
window.renderHistory = renderHistory;
window.refreshHistory = refreshHistory;
window.loadConnectionConfig = loadConnectionConfig;
