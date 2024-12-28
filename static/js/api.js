// 1. 首先实现基础的API调用
class MonitorAPI {
    static async getAllData() {
        try {
            const response = await fetch('/monitor/all');
            return await response.json();
        } catch (error) {
            console.error('获取监控数据失败:', error);
            throw error;
        }
    }
}

// 2. 实现数据处理和更新
class DataManager {
    constructor() {
        this.data = null;
        this.updateCallbacks = new Map();
        this.lastTimestamps = {
            workflows: {},  // 记录每个工作流的最后更新时间
            system: {},    // 记录系统状态的最后更新时间
            chat: {}       // 记录对话数据的最后更新时间
        };
    }

    async refreshData() {
        try {
            const newData = await MonitorAPI.getAllData();
            console.log('获取到新数据:', newData);
            
            if (!this.data) {
                // 首次加载，注册所有工作流的回调
                Object.keys(newData.workflows || {}).forEach(workflowId => {
                    this.onUpdate(`workflow-${workflowId}`, (data) => {
                        updateActiveWorkflow(workflowId, data);
                    });
                });
            }

            // 通知更新
            this.updateCallbacks.forEach((callback, key) => {
                try {
                    console.log('触发回调:', key);
                    if (key.startsWith('workflow-')) {
                        const workflowId = key.replace('workflow-', '');
                        callback(workflowId, newData);
                    } else if (key === 'system-overview') {
                        callback(newData);
                    } else if (key === 'chat-history') {
                        callback(newData);
                    }
                } catch (error) {
                    console.error(`回调执行失败 ${key}:`, error);
                }
            });

            this.data = newData;
        } catch (error) {
            console.error('刷新数据失败:', error);
        }
    }

    // 检查是否有新数据
    _hasNewData(newData, oldData) {
        if (!oldData) return true;
        return JSON.stringify(newData) !== JSON.stringify(oldData);
    }

    // 通知工作流更新
    _notifyWorkflowUpdate(workflowId, data) {
        console.log('正在通知工作流更新:', workflowId);
        const callbacks = Array.from(this.updateCallbacks.entries())
            .filter(([key]) => key.startsWith('workflow-'))
            .map(([, callback]) => callback);
        
        callbacks.forEach(callback => {
            try {
                callback(workflowId, data);
            } catch (error) {
                console.error('工作流更新回调执行失败:', error);
            }
        });
    }

    // 通知系统状态更新
    _notifySystemUpdate(data) {
        console.log('正在通知系统状态更新');
        const callbacks = Array.from(this.updateCallbacks.entries())
            .filter(([key]) => key.startsWith('system-'))
            .map(([, callback]) => callback);
        
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('系统状态更新回调执行失败:', error);
            }
        });
    }

    // 通知对话数据更新
    _notifyChatUpdate(data) {
        console.log('正在通知对话历史更新');
        const callbacks = Array.from(this.updateCallbacks.entries())
            .filter(([key]) => key.startsWith('chat-'))
            .map(([, callback]) => callback);
        
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('对话历史更新回调执行失败:', error);
            }
        });
    }

    // 启动定时刷新，默认1秒刷新一次
    startAutoRefresh(interval = 1000) {
        // 立即执行一次
        this.refreshData();
        // 设置定时刷新
        setInterval(() => this.refreshData(), interval);
    }

    // 添加回 onUpdate 方法
    onUpdate(key, callback) {
        this.updateCallbacks.set(key, callback);
    }
}

// 导出单例实例
export const dataManager = new DataManager();

export { MonitorAPI, dataManager }; 