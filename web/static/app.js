// AI Agent Framework - 前端JavaScript

// 全局变量
let currentTab = 'chat';
let autoRefreshInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initChatEvents();
    loadAgentStatus();
    loadStats();

    // 默认显示对话标签
    switchTab('chat');
});

// 标签切换
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // 更新标签状态
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
        }
    });
    
    currentTab = tabName;
    
    // 根据标签加载数据
    switch (tabName) {
        case 'chat':
            // 对话标签不需要加载数据
            break;
        case 'history':
            loadTaskHistory();
            break;
        case 'agent':
            loadAgentStatus();
            break;
        case 'stats':
            loadStats();
            break;
    }
    
    // 停止自动刷新（如果是统计或状态标签）
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    if (tabName === 'agent' || tabName === 'stats') {
        autoRefreshInterval = setInterval(() => {
            if (currentTab === 'agent') {
                loadAgentStatus();
            } else if (currentTab === 'stats') {
                loadStats();
            }
        }, 3000); // 每3秒刷新
    }
}

// 对话功能
function initChatEvents() {
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            sendMessage();
        }
    });

    document.getElementById('clear-btn').addEventListener('click', clearConversation);

    // 任务历史事件
    document.getElementById('refresh-history').addEventListener('click', loadTaskHistory);
    document.getElementById('filter-status').addEventListener('change', loadTaskHistory);
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (!message) {
        showToast('请输入问题', 'error');
        return;
    }
    
    // 显示用户消息
    addMessage('user', message);
    input.value = '';
    
    // 显示加载状态
    showLoading();
    
    try {
        // 发送任务到后端
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: message
            })
        });
        
        const result = await response.json();
        
        // 隐藏加载状态
        hideLoading();
        
        if (result.status === 'completed') {
            // 显示助手回复
            addMessage('assistant', result.result.content);
        } else {
            // 显示错误消息
            addMessage('system', `任务处理失败：${result.result.content || '未知错误'}`);
            showToast('任务处理失败', 'error');
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        hideLoading();
        addMessage('system', `网络错误：${error.message}`);
        showToast('网络错误，请重试', 'error');
    }
}

function addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const paragraph = document.createElement('p');
    paragraph.textContent = content;
    messageDiv.appendChild(paragraph);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function clearConversation() {
    try {
        const response = await fetch('/api/conversation/clear', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 清空对话显示
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="system-message">
                    <p>对话历史已清空，请开始新对话。</p>
                </div>
            `;
            
            showToast('对话历史已清空', 'success');
        }
        
    } catch (error) {
        console.error('清空对话失败:', error);
        showToast('清空对话失败', 'error');
    }
}

// 任务历史功能
async function loadTaskHistory() {
    const statusFilter = document.getElementById('filter-status').value;
    const tasksList = document.getElementById('tasks-list');
    
    tasksList.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        let url = '/api/tasks';
        if (statusFilter) {
            url += `?status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.tasks && result.tasks.length > 0) {
            tasksList.innerHTML = result.tasks.map(task => createTaskElement(task)).join('');
        } else {
            tasksList.innerHTML = '<div class="empty">暂无任务记录</div>';
        }
        
    } catch (error) {
        console.error('加载任务历史失败:', error);
        tasksList.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
}

function createTaskElement(task) {
    const statusClass = task.status;
    const statusText = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
    }[task.status] || task.status;
    
    const createdTime = new Date(task.created_at).toLocaleString('zh-CN');
    
    return `
        <div class="task-item ${statusClass}">
            <div class="task-header">
                <span class="task-id">#${task.task_id.substring(0, 8)}...</span>
                <span class="task-status status-${statusClass}">${statusText}</span>
            </div>
            <div class="task-content">
                <p>${escapeHtml(task.content)}</p>
            </div>
            <div class="task-meta">
                <span>创建时间：${createdTime}</span>
                ${task.completed_at ? `<span>完成时间：${new Date(task.completed_at).toLocaleString('zh-CN')}</span>` : ''}
            </div>
        </div>
    `;
}

// Agent状态功能
async function loadAgentStatus() {
    const statusContainer = document.getElementById('agent-status');
    
    statusContainer.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/agents/status');
        const result = await response.json();
        
        const statusText = {
            'running': '运行中',
            'stopped': '已停止',
            'created': '已创建',
            'not_loaded': '未加载'
        }[result.status] || result.status;
        
        const statusColor = result.status === 'running' ? '#4caf50' : 
                           result.status === 'stopped' ? '#f44336' : '#ff9800';
        
        statusContainer.innerHTML = `
            <div class="status-card">
                <div class="status-item">
                    <div class="status-label">Agent名称</div>
                    <div class="status-value">${escapeHtml(result.name || 'N/A')}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Agent ID</div>
                    <div class="status-value">${escapeHtml(result.agent_id || 'N/A')}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Agent类型</div>
                    <div class="status-value">${escapeHtml(result.type || 'N/A')}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">运行状态</div>
                    <div class="status-value" style="color: ${statusColor}">${statusText}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">已处理任务</div>
                    <div class="status-value">${result.info ? result.info.processed_count : 0}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">错误次数</div>
                    <div class="status-value">${result.info ? result.info.error_count : 0}</div>
                </div>
                ${result.info && result.info.current_task ? `
                <div class="status-item">
                    <div class="status-label">当前任务</div>
                    <div class="status-value">${escapeHtml(result.info.current_task)}</div>
                </div>
                ` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('加载Agent状态失败:', error);
        statusContainer.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
}

// 统计功能
async function loadStats() {
    const statsPanel = document.getElementById('stats-panel');
    
    statsPanel.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        
        const successRate = result.performance.success_rate ? (result.performance.success_rate * 100).toFixed(1) : '0';
        const avgTime = result.performance.avg_execution_time ? result.performance.avg_execution_time.toFixed(2) : '0';
        
        statsPanel.innerHTML = `
            <div class="stats-panel">
                <div class="stat-card">
                    <div class="stat-title">
                        <span>📋</span>
                        <span>总任务数</span>
                    </div>
                    <div class="stat-value">${result.tasks ? result.tasks.total : 0}</div>
                    <div class="stat-subtitle">完成：${result.tasks ? result.tasks.completed : 0} | 失败：${result.tasks ? result.tasks.failed : 0}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">
                        <span>⏳</span>
                        <span>待处理</span>
                    </div>
                    <div class="stat-value">${result.tasks ? result.tasks.pending : 0}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">
                        <span>✅</span>
                        <span>成功率</span>
                    </div>
                    <div class="stat-value">${successRate}%</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">
                        <span>⚡</span>
                        <span>平均响应时间</span>
                    </div>
                    <div class="stat-value">${avgTime}秒</div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('加载统计失败:', error);
        statsPanel.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
    }
}

// 工具函数
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.classList.remove('hidden');
    
    // 3秒后自动隐藏
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

