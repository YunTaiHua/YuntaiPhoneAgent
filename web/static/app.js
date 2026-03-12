/**
 * app.js - Phone Agent Web 前端逻辑
 * 重构版本 - 按功能模块拆分
 *
 * 模块说明:
 * - state.js: 全局状态管理
 * - utils.js: 工具函数（弹窗、Toast、加载遮罩等）
 * - websocket.js: WebSocket连接和消息处理
 * - pages.js: 页面切换和渲染
 * - renderers.js: 列表渲染函数
 * - actions.js: 用户操作函数
 * - popups.js: 弹窗函数
 * - events.js: 事件绑定和初始化
 */

// 所有模块通过 window 对象导出，在此文件中按顺序加载
// 实际的模块加载由 HTML 中的 script 标签完成
