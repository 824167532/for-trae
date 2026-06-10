/**
 * 开票待办助手 - 历史记录页面JavaScript
 */

// 全局变量
let customers = [];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();
    loadHistory();
    initFilters();
});

// 加载客户列表
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        customers = await response.json();
        
        // 更新客户选择下拉框
        const select = document.getElementById('customerFilter');
        select.innerHTML = '<option value="">全部客户</option>';
        
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.display_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载客户失败:', error);
    }
}

// 加载历史记录
async function loadHistory() {
    const customerId = document.getElementById('customerFilter').value;
    const businessMonth = document.getElementById('monthFilter').value;
    const sendStatus = document.getElementById('sendStatusFilter').value;
    
    const params = new URLSearchParams();
    if (customerId) params.append('customer_id', customerId);
    if (businessMonth) params.append('business_month', businessMonth);
    if (sendStatus) params.append('send_status', sendStatus);
    
    try {
        const response = await fetch(`/api/todos/history?${params}`);
        const history = await response.json();
        renderHistory(history);
    } catch (error) {
        console.error('加载历史记录失败:', error);
    }
}

// 渲染历史记录
function renderHistory(history) {
    const tbody = document.getElementById('historyList');
    const emptyState = document.getElementById('emptyState');
    
    if (history.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = history.map(item => {
        const sendStatusClass = item.send_status === 'sent' ? 'sent' : 'unsent';
        const sendStatusText = item.send_status === 'sent' ? '已发送' : '未发送';
        
        const amountText = item.amount ? `¥${parseFloat(item.amount).toFixed(2)}` : '-';
        const sentAtText = item.sent_at ? formatDateTime(item.sent_at) : '-';
        const completedAtText = item.completed_at ? formatDateTime(item.completed_at) : '-';
        
        return `
            <tr>
                <td>${item.customer_name}</td>
                <td>${item.business_month}</td>
                <td>${amountText}</td>
                <td><span class="status-badge ${sendStatusClass}">${sendStatusText}</span></td>
                <td>${sentAtText}</td>
                <td>${completedAtText}</td>
                <td class="action-buttons">
                    <button class="btn btn-small btn-secondary" onclick="openMonthFolder(${item.id})">
                        打开文件夹
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// 格式化日期时间
function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// 初始化筛选器
function initFilters() {
    document.getElementById('applyFilterBtn').addEventListener('click', loadHistory);
}

// 打开月份文件夹
async function openMonthFolder(todoId) {
    try {
        const response = await fetch(`/api/todos/history`);
        const history = await response.json();
        const item = history.find(h => h.id === todoId);
        
        if (!item) return;
        
        await fetch('/api/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_path: item.customer_path,
                business_month: item.business_month,
                folder_type: 'month'
            })
        });
    } catch (error) {
        console.error('打开文件夹失败:', error);
    }
}