// 更新系统状态概览
function updateSystemOverview(data) {
    if (!data || !data.system) return;
    
    // 更新运行时间
    const startTime = new Date(data.system.start_time.value);
    document.getElementById('system-runtime').textContent = getRunningTime(startTime);
    
    // 更新系统状态
    document.getElementById('system-status').textContent = data.system.status.value;
    
    // 更新工作流统计
    const stats = data.system.workflows_overview.value;
    document.getElementById('workflow-total').textContent = stats.all_workflows.length;
    document.getElementById('workflow-active').textContent = stats.active_workflows.length;
    document.getElementById('workflow-completed').textContent = stats.completed_workflows.length;
    document.getElementById('workflow-failed').textContent = stats.failed_workflows.length;
    
    // 更新活跃工作流ID列表
    document.getElementById('active-workflow-ids').textContent = 
        stats.active_workflows.join(', ') || '--';
}

// 更新对话历史
function updateChatHistory(data) {
    try {
        console.log('开始更新对话历史:', data);
        if (!data || !data.chat) {
            console.warn('对话数据无效');
            return;
        }
        
        const history = document.querySelector('.chat-history');
        const userInput = document.querySelector('.user-input-analysis');
        const recentHistory = document.querySelector('.recent-history');
        
        if (!history || !userInput || !recentHistory) {
            console.error('未找到对话历史相关元素');
            return;
        }

        const chatData = data.chat;
        
        // 更新系统对话历史
        if (chatData.system_history && chatData.system_history.value) {
            console.log('更新系统对话历史');
            const systemHistory = chatData.system_history.value;
            const historyHtml = systemHistory
                .filter(msg => msg.role !== 'system') // 过滤掉系统提示
                .map(msg => `
                    <div class="message ${msg.role}">
                        <div class="message-content">${msg.content}</div>
                        ${msg.timestamp ? `<div class="message-time">${formatTime(msg.timestamp)}</div>` : ''}
                    </div>
                `).join('');
            history.innerHTML = historyHtml;
            console.log('系统对话历史已更新');
        }
        
        // 更新处理的用户输入
        if (chatData.process_user_input && chatData.process_user_input.value) {
            console.log('更新用户输入分析');
            userInput.innerHTML = `
                <div>RAG检索结果:</div>
                <div class="rag-result">${chatData.process_user_input.value}</div>
            `;
            console.log('用户输入分析已更新');
        }
        
        // 更新近期历史对话
        if (chatData.recent_history && chatData.recent_history.value) {
            console.log('更新近期历史对话');
            const recentData = chatData.recent_history.value;
            const recentHtml = recentData.map(msg => `
                <div class="message ${msg.role}">
                    <div class="message-content">${msg.content}</div>
                    ${msg.timestamp ? `<div class="message-time">${formatTime(msg.timestamp)}</div>` : ''}
                </div>
            `).join('');
            recentHistory.innerHTML = recentHtml;
            console.log('近期历史对话已更新');
        }
    } catch (error) {
        console.error('更新对话历史失败:', error);
    }
}

// 更新活跃工作流
function updateActiveWorkflow(workflowId, data) {
    try {
        console.log('开始更新工作流:', workflowId, data);
        if (!data || !data.workflows || !data.workflows[workflowId]) {
            console.warn('工作流数据无效');
            return;
        }
        
        const activeWorkflow = document.querySelector('.active-workflow');
        if (!activeWorkflow) {
            console.error('未找到工作流容器元素');
            return;
        }

        const workflowData = data.workflows[workflowId];
        console.log('工作流数据:', workflowData);
        
        // 创建执行日志流
        console.log('生成执行日志HTML');
        const executionLog = workflowData.execution_log.map(log => `
            <div class="log-card">
                <div class="time">${formatTime(log.timestamp)}</div>
                <div class="status ${log.value.status}">${log.value.status}</div>
                <div class="message">${log.value.message}</div>
            </div>
        `).join('');
        
        // 创建结果卡片流
        console.log('生成结果卡片HTML');
        const resultCards = (workflowData.node_results || []).map(result => {
            const [nodeType] = Object.keys(result.value);
            return `
                <div class="result-card">
                    <div class="node-type">${nodeType}</div>
                    <div class="content">
                        <button class="btn btn-sm btn-primary" onclick="toggleContent(this)">
                            查看内容
                        </button>
                        <div class="content-detail hidden">
                            ${JSON.stringify(result.value[nodeType].content, null, 2)}
                        </div>
                    </div>
                    <div class="time">${formatTime(result.timestamp)}</div>
                </div>
            `;
        }).join('');
        
        console.log('更新DOM');
        activeWorkflow.innerHTML = `
            <div class="workflow-header">
                工作流 #${workflowId}
            </div>
            <div class="execution-log">
                <h5>执行日志流</h5>
                <div class="log-container">
                    ${executionLog}
                </div>
            </div>
            <div class="result-cards">
                <h5>结果卡片流</h5>
                <div class="cards-container">
                    ${resultCards}
                </div>
            </div>
        `;
        console.log('工作流更新完成');
    } catch (error) {
        console.error('更新工作流失败:', error);
    }
}

// 辅助函数
function getRunningTime(startTime) {
    const now = new Date();
    const diff = now - startTime;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}小时${minutes}分钟`;
}

function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('zh-CN');
}

function toggleContent(btn) {
    const content = btn.nextElementSibling;
    content.classList.toggle('hidden');
    btn.textContent = content.classList.contains('hidden') ? '查看内容' : '隐藏内容';
}

// 导出函数
export { updateSystemOverview, updateChatHistory, updateActiveWorkflow }; 