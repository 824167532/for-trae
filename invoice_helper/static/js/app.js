/**
 * 开票待办助手 - 主页面JavaScript
 */

// 全局变量
let customers = [];
let currentImageData = null;
let editingTodoId = null;
let deletingTodoId = null;

// DOM元素
const pasteZone = document.getElementById('pasteZone');
const uploadModal = document.getElementById('uploadModal');
const duplicateModal = document.getElementById('duplicateModal');
const missingModal = document.getElementById('missingModal');
const editModal = document.getElementById('editModal');
const deleteModal = document.getElementById('deleteModal');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();
    loadTodos();
    initPasteZone();
    initFilters();
    initModals();
    initButtons();
    
    // 设置当前月份
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    document.getElementById('monthInput').value = currentMonth;
    document.getElementById('monthFilter').value = currentMonth;
});

// 加载客户列表
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        customers = await response.json();
        
        // 更新客户选择下拉框
        updateCustomerSelects();
    } catch (error) {
        console.error('加载客户失败:', error);
    }
}

// 更新客户选择下拉框
function updateCustomerSelects() {
    const selects = [
        document.getElementById('customerSelect'),
        document.getElementById('customerFilter')
    ];
    
    selects.forEach(select => {
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">请选择客户</option>';
        
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.display_name;
            select.appendChild(option);
        });
        
        if (currentValue) {
            select.value = currentValue;
        }
    });
}

// 加载待办列表
async function loadTodos() {
    const sendStatus = document.getElementById('sendStatusFilter').value;
    const customerId = document.getElementById('customerFilter').value;
    const businessMonth = document.getElementById('monthFilter').value;
    
    const params = new URLSearchParams();
    params.append('send_status', sendStatus);
    if (customerId) params.append('customer_id', customerId);
    if (businessMonth) params.append('business_month', businessMonth);
    
    try {
        const response = await fetch(`/api/todos?${params}`);
        const todos = await response.json();
        renderTodos(todos);
    } catch (error) {
        console.error('加载待办失败:', error);
    }
}

// 渲染待办列表
function renderTodos(todos) {
    const tbody = document.getElementById('todoList');
    const emptyState = document.getElementById('emptyState');
    
    if (todos.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = todos.map(todo => {
        const rowClass = todo.is_overdue ? 'overdue' : '';
        const invoiceStatusClass = todo.invoice_status === 'done' ? 'done' : 'pending';
        const invoiceStatusText = todo.invoice_status === 'done' ? '已开票' : '待开票';
        const sendStatusClass = todo.send_status === 'sent' ? 'sent' : 'unsent';
        const sendStatusText = todo.send_status === 'sent' ? '已发送' : '未发送';
        
        const amountText = todo.amount ? `¥${parseFloat(todo.amount).toFixed(2)}` : '-';
        const createdText = formatDateTime(todo.created_at);
        
        // 操作按钮
        let actionButtons = `
            <button class="btn btn-small btn-secondary" onclick="openMonthFolder(${todo.id})">
                打开文件夹
            </button>
        `;
        
        if (todo.invoice_status === 'done' && todo.send_status === 'unsent') {
            actionButtons += `
                <button class="btn btn-small btn-secondary" onclick="openInvoicesFolder(${todo.id})">
                    发送给客户
                </button>
                <button class="btn btn-small btn-success" onclick="markSent(${todo.id})">
                    标记已发送
                </button>
            `;
        }
        
        actionButtons += `
            <button class="btn btn-small btn-secondary" onclick="editTodo(${todo.id})">
                编辑
            </button>
            <button class="btn btn-small btn-danger" onclick="deleteTodo(${todo.id})">
                删除
            </button>
        `;
        
        return `
            <tr class="${rowClass}">
                <td>${todo.customer_name}</td>
                <td>${todo.business_month}</td>
                <td>${amountText}</td>
                <td><span class="status-badge ${invoiceStatusClass}">${invoiceStatusText}</span></td>
                <td><span class="status-badge ${sendStatusClass}">${sendStatusText}</span></td>
                <td>${createdText}</td>
                <td class="action-buttons">${actionButtons}</td>
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

// 初始化粘贴区域
function initPasteZone() {
    pasteZone.addEventListener('click', () => {
        pasteZone.classList.add('active');
        pasteZone.focus();
    });
    
    pasteZone.addEventListener('blur', () => {
        pasteZone.classList.remove('active');
    });
    
    // 监听粘贴事件
    document.addEventListener('paste', async (e) => {
        const items = e.clipboardData.items;
        
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const blob = item.getAsFile();
                const reader = new FileReader();
                
                reader.onload = (event) => {
                    currentImageData = event.target.result;
                    showUploadModal(currentImageData);
                };
                
                reader.readAsDataURL(blob);
                e.preventDefault();
                break;
            }
        }
    });
}

// 显示上传弹窗
function showUploadModal(imageData) {
    const previewImage = document.getElementById('previewImage');
    previewImage.src = imageData;
    
    // 生成默认文件名
    const now = new Date();
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
    
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    document.getElementById('monthInput').value = currentMonth;
    
    // 清空客户选择和金额
    document.getElementById('customerSelect').value = '';
    document.getElementById('amountInput').value = '';
    
    uploadModal.style.display = 'flex';
}

// 初始化筛选器
function initFilters() {
    document.getElementById('sendStatusFilter').addEventListener('change', loadTodos);
    document.getElementById('customerFilter').addEventListener('change', loadTodos);
    document.getElementById('monthFilter').addEventListener('change', loadTodos);
}

// 初始化弹窗
function initModals() {
    // 上传弹窗
    document.getElementById('closeUploadModal').addEventListener('click', () => {
        uploadModal.style.display = 'none';
        currentImageData = null;
    });
    
    document.getElementById('cancelUploadBtn').addEventListener('click', () => {
        uploadModal.style.display = 'none';
        currentImageData = null;
    });
    
    document.getElementById('confirmUploadBtn').addEventListener('click', createTodo);
    
    // 重复警告弹窗
    document.getElementById('closeDuplicateModal').addEventListener('click', () => {
        duplicateModal.style.display = 'none';
    });
    
    document.getElementById('cancelDuplicateBtn').addEventListener('click', () => {
        duplicateModal.style.display = 'none';
        uploadModal.style.display = 'flex';
    });
    
    document.getElementById('confirmDuplicateBtn').addEventListener('click', forceCreateTodo);
    
    // 遗漏弹窗
    document.getElementById('closeMissingModal').addEventListener('click', () => {
        missingModal.style.display = 'none';
    });
    
    document.getElementById('closeMissingBtn').addEventListener('click', () => {
        missingModal.style.display = 'none';
    });
    
    // 编辑弹窗
    document.getElementById('closeEditModal').addEventListener('click', () => {
        editModal.style.display = 'none';
        editingTodoId = null;
    });
    
    document.getElementById('cancelEditBtn').addEventListener('click', () => {
        editModal.style.display = 'none';
        editingTodoId = null;
    });
    
    document.getElementById('confirmEditBtn').addEventListener('click', saveEditTodo);
    
    // 删除弹窗
    document.getElementById('closeDeleteModal').addEventListener('click', () => {
        deleteModal.style.display = 'none';
        deletingTodoId = null;
    });
    
    document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
        deleteModal.style.display = 'none';
        deletingTodoId = null;
    });
    
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDeleteTodo);
}

// 初始化按钮
function initButtons() {
    // 刷新状态按钮
    document.getElementById('refreshStatusBtn').addEventListener('click', refreshStatus);
    
    // 检查遗漏按钮
    document.getElementById('checkMissingBtn').addEventListener('click', checkMissing);
}

// 创建待办
async function createTodo() {
    const customerId = document.getElementById('customerSelect').value;
    const businessMonth = document.getElementById('monthInput').value;
    const amount = document.getElementById('amountInput').value;
    let filename = document.getElementById('filenameInput').value;
    
    if (!customerId) {
        alert('请选择客户');
        return;
    }
    
    if (!businessMonth) {
        alert('请选择业务月份');
        return;
    }
    
    if (!currentImageData) {
        alert('请先粘贴截图');
        return;
    }
    
    // 生成默认文件名
    if (!filename) {
        const customer = customers.find(c => c.id === parseInt(customerId));
        const now = new Date();
        const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
        filename = `${customer.display_name}_${businessMonth}_${timestamp}.png`;
    }
    
    // 检查重复
    try {
        const checkResponse = await fetch('/api/todos/check-duplicate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer_id: customerId, business_month: businessMonth })
        });
        
        const checkResult = await checkResponse.json();
        
        if (checkResult.duplicate) {
            uploadModal.style.display = 'none';
            duplicateModal.style.display = 'flex';
            return;
        }
    } catch (error) {
        console.error('检查重复失败:', error);
    }
    
    // 创建待办
    try {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_id: parseInt(customerId),
                business_month: businessMonth,
                amount: amount ? parseFloat(amount) : null,
                filename: filename,
                image_data: currentImageData
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            uploadModal.style.display = 'none';
            currentImageData = null;
            loadTodos();
            alert('待办创建成功');
        } else {
            alert(result.error || '创建失败');
        }
    } catch (error) {
        console.error('创建待办失败:', error);
        alert('创建失败，请重试');
    }
}

// 强制创建待办（忽略重复警告）
async function forceCreateTodo() {
    duplicateModal.style.display = 'none';
    
    const customerId = document.getElementById('customerSelect').value;
    const businessMonth = document.getElementById('monthInput').value;
    const amount = document.getElementById('amountInput').value;
    let filename = document.getElementById('filenameInput').value;
    
    if (!filename) {
        const customer = customers.find(c => c.id === parseInt(customerId));
        const now = new Date();
        const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
        filename = `${customer.display_name}_${businessMonth}_${timestamp}.png`;
    }
    
    try {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_id: parseInt(customerId),
                business_month: businessMonth,
                amount: amount ? parseFloat(amount) : null,
                filename: filename,
                image_data: currentImageData
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentImageData = null;
            loadTodos();
            alert('待办创建成功');
        } else {
            uploadModal.style.display = 'flex';
            alert(result.error || '创建失败');
        }
    } catch (error) {
        console.error('创建待办失败:', error);
        uploadModal.style.display = 'flex';
        alert('创建失败，请重试');
    }
}

// 打开月份文件夹
async function openMonthFolder(todoId) {
    try {
        const response = await fetch(`/api/todos`);
        const todos = await response.json();
        const todo = todos.find(t => t.id === todoId);
        
        if (!todo) return;
        
        await fetch('/api/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_path: todo.customer_path,
                business_month: todo.business_month,
                folder_type: 'month'
            })
        });
    } catch (error) {
        console.error('打开文件夹失败:', error);
    }
}

// 打开发票文件夹
async function openInvoicesFolder(todoId) {
    try {
        const response = await fetch(`/api/todos`);
        const todos = await response.json();
        const todo = todos.find(t => t.id === todoId);
        
        if (!todo) return;
        
        await fetch('/api/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_path: todo.customer_path,
                business_month: todo.business_month,
                folder_type: 'invoices'
            })
        });
    } catch (error) {
        console.error('打开文件夹失败:', error);
    }
}

// 标记已发送
async function markSent(todoId) {
    try {
        const response = await fetch(`/api/todos/${todoId}/mark-sent`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadTodos();
            alert('已标记为已发送');
        } else {
            alert(result.error || '标记失败');
        }
    } catch (error) {
        console.error('标记失败:', error);
        alert('标记失败，请重试');
    }
}

// 编辑待办
async function editTodo(todoId) {
    editingTodoId = todoId;
    
    try {
        const response = await fetch(`/api/todos`);
        const todos = await response.json();
        const todo = todos.find(t => t.id === todoId);
        
        if (!todo) return;
        
        document.getElementById('editMonthInput').value = todo.business_month;
        document.getElementById('editAmountInput').value = todo.amount || '';
        
        editModal.style.display = 'flex';
    } catch (error) {
        console.error('获取待办信息失败:', error);
    }
}

// 保存编辑
async function saveEditTodo() {
    if (!editingTodoId) return;
    
    const businessMonth = document.getElementById('editMonthInput').value;
    const amount = document.getElementById('editAmountInput').value;
    
    try {
        const response = await fetch(`/api/todos/${editingTodoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                business_month: businessMonth,
                amount: amount ? parseFloat(amount) : null
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            editModal.style.display = 'none';
            editingTodoId = null;
            loadTodos();
            alert('保存成功');
        } else {
            alert(result.error || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败，请重试');
    }
}

// 删除待办
function deleteTodo(todoId) {
    deletingTodoId = todoId;
    document.getElementById('deleteFileCheckbox').checked = false;
    deleteModal.style.display = 'flex';
}

// 确认删除
async function confirmDeleteTodo() {
    if (!deletingTodoId) return;
    
    const deleteFile = document.getElementById('deleteFileCheckbox').checked;
    
    try {
        const response = await fetch(`/api/todos/${deletingTodoId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delete_file: deleteFile })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            deleteModal.style.display = 'none';
            deletingTodoId = null;
            loadTodos();
            alert('删除成功');
        } else {
            alert(result.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}

// 刷新状态
async function refreshStatus() {
    try {
        const response = await fetch('/api/todos/refresh-status', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadTodos();
            alert(`刷新完成，更新了 ${result.updated_count} 条待办状态`);
        } else {
            alert(result.error || '刷新失败');
        }
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败，请重试');
    }
}

// 检查遗漏
async function checkMissing() {
    try {
        const response = await fetch('/api/todos/missing-current-month');
        const missing = await response.json();
        
        const missingList = document.getElementById('missingList');
        
        if (missing.length === 0) {
            missingList.innerHTML = '<div class="missing-item">所有客户当月都有开票记录</div>';
        } else {
            missingList.innerHTML = missing.map(customer => 
                `<div class="missing-item">${customer.display_name}</div>`
            ).join('');
        }
        
        missingModal.style.display = 'flex';
    } catch (error) {
        console.error('检查遗漏失败:', error);
        alert('检查失败，请重试');
    }
}