/**
 * websocket.js - WebSocket连接和消息处理
 */

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

// ==================== 消息处理 ====================
function handleMessage(data) {
    switch (data.type) {
        case 'init':
            updateState(data.data);
            if (data.tts_models) {
                state.ttsModels = data.tts_models;
                updateTTSLabels();
            }
            // 根据后端状态决定是否显示欢迎遮罩
            // is_first_connection 为 true 表示这是后端启动后的第一个连接
            if (data.is_first_connection) {
                showWelcomeOverlay();
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
        case 'agent_event':
            console.log('[agent_event]', data.event || null);
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
        case 'welcome_complete':
            // 欢迎语音播放完成，隐藏遮罩
            hideWelcomeOverlay();
            // 后端已经标记首次连接完成，前端无需再设置localStorage
            if (data.tts_success) {
                console.log('✅ TTS测试成功');
            } else {
                console.log('⚠️ TTS测试失败');
            }
            break;
    }
}

// ==================== 状态更新 ====================
function updateState(newState) {
    Object.assign(state, newState);

    // 更新连接状态指示器
    if (elements.connectionIndicator) {
        elements.connectionIndicator.innerHTML = state.is_connected 
            ? `<span class="status-dot"></span>${state.device_id}` 
            : '<span class="status-dot"></span>未连接';
        elements.connectionIndicator.className = `status-indicator ${state.is_connected ? 'connected' : 'disconnected'}`;
    }

    // 更新设备管理页面的连接状态
    if (elements.connectionStatus) {
        elements.connectionStatus.textContent = state.is_connected 
            ? `已连接: ${state.device_id}` 
            : '未连接';
        elements.connectionStatus.className = `connection-status ${state.is_connected ? 'connected' : ''}`;
    }

    // 更新TTS状态指示器
    if (elements.ttsIndicator) {
        elements.ttsIndicator.innerHTML = state.tts_enabled 
            ? '<span class="status-dot"></span>TTS: 开' 
            : '<span class="status-dot"></span>TTS: 关';
        elements.ttsIndicator.className = `status-indicator ${state.tts_enabled ? 'connected' : 'disconnected'}`;
    }

    // 更新按钮状态 - 使用 is_executing 而不是 executing
    const isExecuting = state.is_executing || state.executing;
    if (elements.executeBtn) elements.executeBtn.disabled = isExecuting;
    if (elements.terminateBtn) elements.terminateBtn.disabled = !isExecuting;
    if (elements.enterBtn) elements.enterBtn.classList.toggle('visible', isExecuting);
    if (elements.connectBtn) elements.connectBtn.disabled = state.is_connected;
    if (elements.disconnectBtn) elements.disconnectBtn.disabled = !state.is_connected;

    // 同步更新文件管理卡片
    if (newState.hasOwnProperty('attached_files')) {
        renderFileList(newState.attached_files);
    }

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

// 导出
window.connectWebSocket = connectWebSocket;
window.sendMessage = sendMessage;
window.handleMessage = handleMessage;
window.updateState = updateState;
window.updateTTSLabels = updateTTSLabels;
window.updateAttachedFiles = updateAttachedFiles;
