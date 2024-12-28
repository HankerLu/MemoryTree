// 1. 首先实现基础的API调用
class MonitorAPI {

    static BASE_URL = 'http://127.0.0.1:8000';

    static async getAllData() {
        try {
            const response = await fetch(`${this.BASE_URL}/monitor/all`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
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
    }

    async refreshData() {
        try {
            const newData = await MonitorAPI.getAllData();
            console.log('获取到新数据:', newData);

            // 通知更新
            this.updateCallbacks.forEach((callback, key) => {
                try {
                    console.log('触发回调:', key);
                    if (key.startsWith('workflow-')) {
                        const workflowId = key.replace('workflow-', '');
                        callback(workflowId, newData);
                    } else {
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

    // 启动定时刷新
    startAutoRefresh(interval = 1000) {
        // 立即执行一次
        this.refreshData();
        // 设置定时刷新
        setInterval(() => this.refreshData(), interval);
    }

    // 注册回调
    onUpdate(key, callback) {
        this.updateCallbacks.set(key, callback);
    }
}

// 创建单例实例并导出
const dataManager = new DataManager();
export {MonitorAPI, dataManager};