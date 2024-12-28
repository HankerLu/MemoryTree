import {dataManager} from './api.js';

import {
    updateSystemOverview, updateChatHistory, updateUserInputAnalysis,

    updateRecentHistory, updateActiveWorkflow, updateLatestCompletedWorkflow,

    updateHistoryWorkflows, updateOtherWorkflows
} from './workflow.js';


// 等待 DOM 加载完成

document.addEventListener('DOMContentLoaded', () => {

    // 统一的数据更新处理函数

    function handleDataUpdate(data) {

        if (!data) return;


        // 更新系统状态

        updateSystemOverview(data);


        // 更新对话相关

        if (data.chat) {

            updateChatHistory(data);

            updateUserInputAnalysis(data);

            updateRecentHistory(data);

        }


        // 更新工作流相关

        if (data.system?.workflows_overview?.value) {

            const activeWorkflows = data.system.workflows_overview.value.active_workflows || [];


            // 无论是否有活跃工作流都更新，让函数内部处理空状态

            updateActiveWorkflow(activeWorkflows[0], data);

            updateOtherWorkflows(data);


            // 只有当有已完成工作流时才更新

            if (data.system.workflows_overview.value.completed_workflows?.length > 0) {

                updateLatestCompletedWorkflow(data);

            }


            // 更新历史工作流

            updateHistoryWorkflows(data);

        }

    }


    // 只注册一个统一的回调

    dataManager.onUpdate('all', handleDataUpdate);


    // 启动自动刷新，间隔改为3秒

    console.log('启动数据刷新');

    dataManager.startAutoRefresh(3000);

});