// 将 processSVGContent 函数移到文件顶部，作为公共函数

function processSVGContent(content) {

    try {

        if (Array.isArray(content)) {

            // SVG 数组的情况

            return content.map(svg => {

                // 如果已经是字符串，直接返回

                if (typeof svg === 'string') return svg;

                // 否则尝试解析和处理

                return JSON.stringify(svg)

                    .replace(/\\\\/g, '\\')

                    .replace(/\\"/g, '"')

                    .replace(/\\n/g, '\n')

                    .slice(1, -1); // 移除首尾的引号

            }).join('\n');

        } else if (typeof content === 'string') {

            return content;

        }

        return JSON.stringify(content, null, 2);

    } catch (error) {

        console.error('处理SVG内容时出错:', error);

        return '处理SVG内容时出错';

    }

}


// 创建结果卡片的函数（抽取为公共函数）

function createResultCard(nodeType, result) {

    let contentDisplay;

    if (nodeType === 'svg') {

        contentDisplay = processSVGContent(result.content);

        return `

            <div class="result-card">

                <div class="node-type">${nodeType}</div>

                <div class="content">

                    <button class="btn btn-sm btn-primary" 

                            onclick='window.toggleContent(this, "${nodeType}", ${JSON.stringify(contentDisplay)})'>

                        查看内容

                    </button>

                </div>

            </div>

        `;

    } else {

        contentDisplay = JSON.stringify(result.content, null, 2);

        return `

            <div class="result-card">

                <div class="node-type">${nodeType}</div>

                <div class="content">

                    <button class="btn btn-sm btn-primary" 

                            onclick='window.toggleContent(this, "${nodeType}", ${JSON.stringify(contentDisplay)})'>

                        查看内容

                    </button>

                </div>

            </div>

        `;

    }

}


// 更新系统状态概览

function updateSystemOverview(data) {

    if (!data?.system?.start_time?.value || !data?.system?.status?.value) {

        console.log('系统状态数据未就绪');

        return;

    }


    const systemData = data.system;


    // 更新运行时间

    const startTime = new Date(systemData.start_time.value);

    document.getElementById('system-runtime').textContent = getRunningTime(startTime);


    // 更新系统状态

    document.getElementById('system-status').textContent = systemData.status.value;


    // 更新工作流概览

    if (systemData.workflows_overview?.value) {

        const stats = systemData.workflows_overview.value;

        document.getElementById('workflow-total').textContent = stats.all_workflows?.length || 0;

        document.getElementById('workflow-active').textContent = stats.active_workflows?.length || 0;

        document.getElementById('workflow-completed').textContent = stats.completed_workflows?.length || 0;

        document.getElementById('workflow-failed').textContent = stats.failed_workflows?.length || 0;


        // 更新活跃工作流ID列表

        document.getElementById('active-workflow-ids').textContent =

            (stats.active_workflows?.length > 0) ? stats.active_workflows.join(', ') : '--';

    } else {

        // 如果没有工作流数据，显示默认值

        document.getElementById('workflow-total').textContent = '0';

        document.getElementById('workflow-active').textContent = '0';

        document.getElementById('workflow-completed').textContent = '0';

        document.getElementById('workflow-failed').textContent = '0';

        document.getElementById('active-workflow-ids').textContent = '--';

    }

}


// 更新对话历史

function updateChatHistory(data) {

    if (!data || !data.chat) return;


    const chatData = data.chat;

    const history = document.querySelector('.chat-history');


    // 更新系统对话历史

    if (chatData.system_history && chatData.system_history.value) {

        const messages = chatData.system_history.value

            .filter(msg => msg.role !== 'system')

            .map(msg => `

                <div class="message ${msg.role}">

                    <div class="message-content">${msg.content}</div>

                    ${msg.timestamp ? `<div class="message-time">${formatTime(msg.timestamp)}</div>` : ''}

                </div>

            `).join('');

        history.innerHTML = messages;

    }

}


// 更新用户输入处理结果

function updateUserInputAnalysis(data) {

    if (!data || !data.chat || !data.chat.process_user_input) return;


    const userInput = document.querySelector('.user-input-analysis');

    const result = data.chat.process_user_input.value;


    userInput.innerHTML = `

        <div class="rag-result">

            <div class="time">${formatTime(data.chat.process_user_input.timestamp)}</div>

            <div class="content">${result}</div>

        </div>

    `;

}


// 更新期历史对话

function updateRecentHistory(data) {

    if (!data || !data.chat || !data.chat.recent_history) return;


    const recentHistory = document.querySelector('.recent-history');

    const messages = data.chat.recent_history.value.map(msg => `

        <div class="history-message">

            <span class="time">${formatTime(msg.timestamp)}</span>

            <span class="role">${msg.role === 'user' ? '用户' : '助手'}:</span>

            <span class="content">${msg.content}</span>

        </div>

    `).join('');


    recentHistory.innerHTML = messages || '<div class="text-center text-muted">暂无历史对话</div>';

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


// 将 toggleContent 函数暴露到全局

window.toggleContent = function (btn, nodeType, content) {

    const modalTitle = document.querySelector('#contentModal .modal-title');

    const modalContent = document.querySelector('#modalContent');


    // 设置标题

    modalTitle.textContent = `${nodeType} 内容详情`;


    // 设置内容

    if (nodeType === 'svg') {

        modalContent.innerHTML = `

            <div class="svg-container">

                ${content}

            </div>

        `;

    } else if (nodeType === 'narrative') {

        // 特殊处理 narrative 内容，处理 \n\n 为段落分隔

        modalContent.innerHTML = `

            <div class="narrative-content">

                ${content

            .replace(/\\n\\n/g, '\n\n')  // 先处理 \n\n

            .replace(/\\n/g, '\n')       // 再处理单个 \n

            .split('\n\n')               // 按段落分割

            .map(para => `<p>${para.trim()}</p>`)  // 每个段落包装在 p 标签中

            .join('')}

            </div>

        `;

    } else {

        modalContent.innerHTML = `

            <pre class="content-detail">${content}</pre>

        `;

    }


    // 显示 Modal

    const modal = new bootstrap.Modal(document.getElementById('contentModal'));

    modal.show();

};


// 更新活跃工作流

function updateActiveWorkflow(workflowId, data) {

    const activeWorkflow = document.querySelector('.active-workflow');


    // 如果没有工作流ID或数据，显示空状态

    if (!workflowId || !data?.workflows?.[workflowId]) {

        activeWorkflow.innerHTML = `

            <div class="text-center text-muted py-3">

                <i class="bi bi-hourglass"></i>

                <p>暂无活跃工作流</p>

            </div>

        `;

        return;

    }


    const workflowData = data.workflows[workflowId];


    // 更新工作流头部信息

    const workflowHeader = `

        <div class="workflow-info">

            <div class="d-flex justify-content-between">

                <h5 class="workflow-id">工作流 #${workflowId}</h5>

                <span class="workflow-status badge ${getStatusBadgeClass(getWorkflowStatus(workflowData))}">

                    ${getWorkflowStatus(workflowData)}

                </span>

            </div>

        </div>

    `;


    // 创建执行日志流

    const executionLog = workflowData.execution_log.map(log => `

        <div class="log-card">

            <div class="time">${formatTime(log.timestamp)}</div>

            <div class="status ${log.value.status}">${log.value.status}</div>

            <div class="node">${log.value.node}</div>

            <div class="message">${log.value.message}</div>

        </div>

    `).join('');


    // 修改结果卡片生成部分

    const resultCards = Object.entries(workflowData.node_results || {})

        .map(([nodeType, result]) => createResultCard(nodeType, result))

        .join('');


    // 更新DOM

    activeWorkflow.innerHTML = `

        ${workflowHeader}

        <div class="execution-log mt-3">

            <h6>执行日志流</h6>

            <div class="log-container">

                ${executionLog}

            </div>

        </div>

        <div class="result-cards mt-3">

            <h6>结果卡片流</h6>

            <div class="cards-container">

                ${resultCards}

            </div>

        </div>

    `;

}


// 更新最近完成的工作流

function updateLatestCompletedWorkflow(data) {

    if (!data?.system?.workflows_overview?.value?.completed_workflows) {

        console.log('已完成工作流数据未就绪');

        return;

    }


    const completedWorkflows = data.system.workflows_overview.value.completed_workflows;

    const recentComplete = document.getElementById('recentComplete');


    if (completedWorkflows.length === 0) {

        recentComplete.innerHTML = `

            <div class="text-center text-muted py-3">

                <i class="bi bi-check2-circle"></i>

                <p>暂无已完成工作流</p>

            </div>

        `;

        return;

    }


    // 获取最新完成的工作流

    const latestWorkflowId = completedWorkflows[completedWorkflows.length - 1];

    const workflowData = data.workflows[latestWorkflowId];


    // 计算执行时间

    const startTime = new Date(workflowData.execution_log[0].timestamp);

    const endTime = new Date(workflowData.execution_log[workflowData.execution_log.length - 1].timestamp);

    const executionTime = getExecutionTime(startTime, endTime);


    // 生成HTML

    recentComplete.innerHTML = `

        <div class="recent-workflow">

            <div class="workflow-info">

                <h5>最近完成工作流 #${latestWorkflowId}</h5>

                <div class="execution-time">

                    <label>执行时间:</label>

                    <span>${executionTime}</span>

                </div>

            </div>

            <div class="execution-log mt-3">

                <h6>执行日志流</h6>

                <div class="log-container">

                    ${workflowData.execution_log.map(log => `

                        <div class="log-card">

                            <div class="time">${formatTime(log.timestamp)}</div>

                            <div class="status ${log.value.status}">${log.value.status}</div>

                            <div class="node">${log.value.node}</div>

                            <div class="message">${log.value.message}</div>

                        </div>

                    `).join('')}

                </div>

            </div>

            <div class="result-cards mt-3">

                <h6>结果卡片流</h6>

                <div class="cards-container">

                    ${Object.entries(workflowData.node_results || {})

        .map(([nodeType, result]) => createResultCard(nodeType, result))

        .join('')}

                </div>

            </div>

        </div>

    `;

}


// 辅助函数

function getWorkflowStatus(workflowData) {

    const lastLog = workflowData.execution_log[workflowData.execution_log.length - 1];

    return lastLog.value.status;

}


function getStatusBadgeClass(status) {

    const statusClasses = {

        'processing': 'bg-primary',

        'completed': 'bg-success',

        'failed': 'bg-danger'

    };

    return statusClasses[status] || 'bg-secondary';

}


function getExecutionTime(startTime, endTime) {

    const diff = endTime - startTime;

    const minutes = Math.floor(diff / (1000 * 60));

    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${minutes}分${seconds}秒`;

}


// 更新历史工作流表格

function updateHistoryWorkflows(data) {

    if (!data?.system?.workflows_overview?.value?.all_workflows) {

        console.log('历史工作流数据未就绪');

        return;

    }


    const historyList = document.getElementById('history-workflow-list');

    const allWorkflows = data.system.workflows_overview.value.all_workflows;


    if (allWorkflows.length === 0) {

        historyList.innerHTML = `

            <tr>

                <td colspan="5" class="text-center text-muted">

                    <div class="py-3">

                        <i class="bi bi-clock-history"></i>

                        <p>暂无历史工作流</p>

                    </div>

                </td>

            </tr>

        `;

        return;

    }


    // 按时间倒序排序工作流

    const sortedWorkflows = allWorkflows

        .map(workflowId => ({

            id: workflowId,

            data: data.workflows[workflowId]

        }))

        .sort((a, b) => {

            const timeA = new Date(a.data.execution_log[0].timestamp);

            const timeB = new Date(b.data.execution_log[0].timestamp);

            return timeB - timeA;  // 倒序排列

        });


    // 生成表格行

    const rows = sortedWorkflows.map(workflow => {

        const {id, data} = workflow;

        const firstLog = data.execution_log[0];

        const lastLog = data.execution_log[data.execution_log.length - 1];

        const type = getWorkflowType(data);

        const status = lastLog.value.status;

        const time = formatTime(firstLog.timestamp);


        return `

            <tr>

                <td>${id}</td>

                <td>${type}</td>

                <td>

                    <span class="badge ${getStatusBadgeClass(status)}">

                        ${status}

                    </span>

                </td>

                <td>${time}</td>

                <td>

                    <button class="btn btn-sm btn-outline-primary" 

                            onclick="showWorkflowDetails('${id}')">

                        查看详情

                    </button>

                </td>

            </tr>

        `;

    }).join('');


    historyList.innerHTML = rows;

}


// 获取工作流类型

function getWorkflowType(workflowData) {

    // 从第一个节点的类型判断工作流类型

    const firstNode = workflowData.execution_log[0].value.node;

    const typeMap = {

        'workflow': '标准工作流',

        'narrative': '叙事生成',

        'parallel': '并行处理',

        'analysis': '数据分析'

    };

    return typeMap[firstNode] || firstNode;

}


// 初始化工作流查询功能

function initWorkflowSearch(data) {

    const searchInput = document.querySelector('.workflow-search input');

    const searchButton = document.querySelector('.workflow-search button');


    searchButton.onclick = () => {

        const workflowId = searchInput.value.trim();

        if (!workflowId) {

            alert('请输入工作流ID');

            return;

        }


        if (data.workflows[workflowId]) {

            showWorkflowDetails(workflowId);

        } else {

            alert('未找到该工作流');

        }

    };

}


// 显示工作流详情

function showWorkflowDetails(workflowId) {

    // 这里可以实现弹窗显示详情或跳转到详情页

    // 暂时用 alert 代替

    alert(`显示工作流 ${workflowId} 的详细信息`);

}


// 更新其他活跃工作流

function updateOtherWorkflows(data) {

    if (!data || !data.system || !data.workflows) return;


    const activeWorkflows = data.system.workflows_overview.value.active_workflows;

    const otherWorkflows = activeWorkflows.slice(1);  // 除了第一个之外的所有活跃工作流

    const otherWorkflowsContainer = document.querySelector('.other-workflows');

    const workflowCount = document.querySelector('.other-workflow-count');


    // 更新数量

    workflowCount.textContent = otherWorkflows.length;


    if (otherWorkflows.length === 0) {

        otherWorkflowsContainer.innerHTML = `

            <div class="text-center text-muted py-3">

                <i class="bi bi-list-task"></i>

                <p>暂无其他活跃工作流</p>

            </div>

        `;

        return;

    }


    // 生成其他工作流HTML

    const workflowsHtml = otherWorkflows.map(workflowId => {

        const workflowData = data.workflows[workflowId];

        const status = getWorkflowStatus(workflowData);


        return `

            <div class="workflow-item mb-3">

                <div class="workflow-info">

                    <div class="d-flex justify-content-between">

                        <h6>工作流 #${workflowId}</h6>

                        <span class="badge ${getStatusBadgeClass(status)}">${status}</span>

                    </div>

                </div>

                <div class="execution-log mt-2">

                    <div class="log-container">

                        ${workflowData.execution_log.map(log => `

                            <div class="log-card">

                                <div class="time">${formatTime(log.timestamp)}</div>

                                <div class="status ${log.value.status}">${log.value.status}</div>

                                <div class="node">${log.value.node}</div>

                                <div class="message">${log.value.message}</div>

                            </div>

                        `).join('')}

                    </div>

                </div>

            </div>

        `;

    }).join('');


    otherWorkflowsContainer.innerHTML = workflowsHtml;

}


// 导出函数

export {

    updateSystemOverview,

    updateChatHistory,

    updateUserInputAnalysis,

    updateRecentHistory,

    updateActiveWorkflow,

    updateLatestCompletedWorkflow,

    updateHistoryWorkflows,

    updateOtherWorkflows

};
