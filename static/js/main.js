import { dataManager } from './api.js';
import { updateSystemOverview, updateChatHistory, updateUserInputAnalysis, 
         updateRecentHistory, updateActiveWorkflow, updateLatestCompletedWorkflow, 
         updateHistoryWorkflows, updateOtherWorkflows } from './workflow.js';

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
    // 统一的数据更新处理函数
    function handleDataUpdate(data) {
        if (!data) return;
        
        // 更新系统状态
        updateSystemOverview(data);
        
        // 更新对话相关
        updateChatHistory(data);
        updateUserInputAnalysis(data);
        updateRecentHistory(data);
        
        // 更新工作流相关
        const activeWorkflows = data.system.workflows_overview.value.active_workflows;
        if (activeWorkflows.length > 0) {
            updateActiveWorkflow(activeWorkflows[0], data);
            updateOtherWorkflows(data);
        }
        
        // 更新完成和历史工作流
        updateLatestCompletedWorkflow(data);
        updateHistoryWorkflows(data);
    }

    // 只注册一个统一的回调
    dataManager.onUpdate('all', handleDataUpdate);

    // 启动自动刷新，间隔改为3秒
    console.log('启动数据刷新');
    dataManager.startAutoRefresh(3000);
}); 