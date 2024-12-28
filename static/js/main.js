import { dataManager } from './api.js';
import { updateSystemOverview, updateChatHistory, updateUserInputAnalysis, 
         updateRecentHistory, updateActiveWorkflow, updateLatestCompletedWorkflow, 
         updateHistoryWorkflows, updateOtherWorkflows } from './workflow.js';

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM加载完成，开始注册回调');

    // 注册系统状态更新
    dataManager.onUpdate('system-overview', (data) => {
        console.log('系统状态更新回调触发');
        updateSystemOverview(data);
    });

    // 注册对话历史更新
    dataManager.onUpdate('chat-history', (data) => {
        console.log('对话历史更新回调触发');
        updateChatHistory(data);
    });

    // 注册用户输入更新
    dataManager.onUpdate('user-input', (data) => {
        console.log('用户输入更新回调触发');
        updateUserInputAnalysis(data);
    });

    // 注册近期历史更新
    dataManager.onUpdate('recent-history', (data) => {
        console.log('近期历史更新回调触发');
        updateRecentHistory(data);
    });

    // 注册活跃工作流更新
    dataManager.onUpdate('active-workflow', (data) => {
        console.log('活跃工作流更新回调触发');
        const activeWorkflows = data.system.workflows_overview.value.active_workflows;
        if (activeWorkflows.length > 0) {
            updateActiveWorkflow(activeWorkflows[0], data);  // 显示第一个活跃工作流
            updateOtherWorkflows(data);  // 更新其他活跃工作流
        }
    });

    // 注册最近完成工作流更新
    dataManager.onUpdate('completed-workflow', (data) => {
        console.log('最近完成工作流更新回调触发');
        updateLatestCompletedWorkflow(data);
    });

    // 注册历史工作流更新
    dataManager.onUpdate('history-workflows', (data) => {
        console.log('历史工作流更新回调触发');
        updateHistoryWorkflows(data);
    });

    // 启动自动刷新
    console.log('启动数据刷新');
    dataManager.startAutoRefresh(1000);
}); 