/**
 * state.js - 全局状态管理
 */

// 全局状态
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
    escHandler: null   // ESC键处理器
};

// DOM元素缓存
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const elements = {};

// 导出
window.state = state;
window.$ = $;
window.$$ = $$;
window.elements = elements;
