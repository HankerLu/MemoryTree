import { MonitorAPI, dataManager } from './api.js';
import { updateSystemOverview, updateChatHistory, updateActiveWorkflow } from './workflow.js';

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM加载完成，开始注册回调');

    // 注册系统状态更新
    dataManager.onUpdate('system-overview', (data) => {
        console.log('系统状态更新回调触发');
        if (data && data.system) {
            updateSystemOverview(data);
            // 更新调试信息
            document.getElementById('callback-status').textContent = '系统状态已更新';
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
    });

    // 注册对话历史更新
    dataManager.onUpdate('chat-history', (data) => {
        console.log('对话历史更新回调触发');
        if (data && data.chat) {
            updateChatHistory(data);
        }
    });

    // 获取初始数据来注册工作流回调
    try {
        const initialData = await MonitorAPI.getAllData();
        console.log('获取初始数据:', initialData);
        
        // 注册工作流更新
        if (initialData && initialData.workflows) {
            Object.keys(initialData.workflows).forEach(workflowId => {
                console.log('注册工作流更新:', workflowId);
                dataManager.onUpdate(`workflow-${workflowId}`, (data) => {
                    console.log('工作流更新回调触发:', workflowId);
                    updateActiveWorkflow(workflowId, data);
                });
            });
        }

        // 启动自动刷新
        console.log('启动数据刷新');
        dataManager.startAutoRefresh(1000);
    } catch (error) {
        console.error('初始化失败:', error);
        document.getElementById('callback-status').textContent = '初始化失败';
    }
}); 