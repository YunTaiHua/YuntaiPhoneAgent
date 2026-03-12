/**
 * popups.js - 弹窗函数
 */

// TTS设置弹窗
function showTTSSettingsPopup() {
    // 获取当前模型，支持两种key格式
    const currentGpt = state.ttsModels.currentGpt || state.ttsModels.current_gpt;
    const currentSovits = state.ttsModels.currentSovits || state.ttsModels.current_sovits;
    const currentAudio = state.ttsModels.currentAudio || state.ttsModels.current_audio;

    const popup = document.createElement('div');
    popup.className = 'popup-overlay';
    popup.innerHTML = `
        <div class="popup-dialog popup-dialog-large">
            <div class="popup-title">🎤 TTS语音设置</div>
            <div class="popup-subtitle">（语音合成有延迟）</div>
            <div class="popup-content">
                <div class="popup-checkbox-center">
                    <label class="popup-checkbox">
                        <input type="checkbox" id="tts-enabled-check" ${state.tts_enabled ? 'checked' : ''}>
                        <span>启用语音播报</span>
                    </label>
                </div>
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
                <button class="btn btn-primary" id="tts-popup-save">保存</button>
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
                <div class="popup-checkbox-center">
                    <label class="popup-checkbox">
                        <input type="checkbox" id="scrcpy-always-top">
                        <span>窗口置顶</span>
                    </label>
                </div>
            </div>
            <div class="popup-buttons">
                <button class="btn btn-secondary" id="scrcpy-popup-cancel">取消</button>
                <button class="btn btn-accent" id="scrcpy-popup-start">启动投屏</button>
            </div>
            <div class="popup-info">注意：请确保手机已开启USB调试模式</div>
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

// 导出
window.showTTSSettingsPopup = showTTSSettingsPopup;
window.showScrcpyPopup = showScrcpyPopup;
window.showDeviceDetectPopup = showDeviceDetectPopup;
window.showSystemCheckPopup = showSystemCheckPopup;
window.showFileManagementPopup = showFileManagementPopup;
