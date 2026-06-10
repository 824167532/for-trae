/**
 * 开票待办助手 - 设置页面JavaScript
 */

// 全局变量
let customers = [];
let editingCustomerId = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadRootDirectory();
    loadCustomers();
    initButtons();
    initModals();
});

// 加载根目录
async function loadRootDirectory() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        const input = document.getElementById('rootDirectoryInput');
        input.value = settings.root_directory || '';
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

// 加载客户列表
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        customers = await response.json();
        renderCustomers();
    } catch (error) {
        console.error('加载客户失败:', error);
    }
}

// 渲染客户列表
function renderCustomers() {
    const tbody = document.getElementById('customerList');
    const emptyState = document.getElementById('emptyState');
    
    if (customers.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = customers.map(customer => `
        <tr>
            <td>${customer.display_name}</td>
            <td>${customer.relative_path}</td>
            <td class="action-buttons">
                <button class="btn btn-small btn-secondary" onclick="editCustomer(${customer.id})">
                    编辑
                </button>
                <button class="btn btn-small btn-danger" onclick="deleteCustomer(${customer.id})">
                    删除
                </button>
            </td>
        </tr>
    `).join('');
}

// 初始化按钮
function initButtons() {
    // 保存根目录
    document.getElementById('saveRootDirBtn').addEventListener('click', saveRootDirectory);
    
    // 下载模板
    document.getElementById('downloadTemplateBtn').addEventListener('click', downloadTemplate);
    
    // 导入客户
    document.getElementById('importCustomersBtn').addEventListener('click', () => {
        document.getElementById('importFileInput').click();
    });
    
    document.getElementById('importFileInput').addEventListener('change', importCustomers);
    
    // 添加客户
    document.getElementById('addCustomerBtn').addEventListener('click', () => {
        document.getElementById('customerNameInput').value = '';
        document.getElementById('customerPathInput').value = '';
        document.getElementById('addCustomerModal').style.display = 'flex';
    });
}

// 初始化弹窗
function initModals() {
    // 添加客户弹窗
    document.getElementById('closeAddCustomerModal').addEventListener('click', () => {
        document.getElementById('addCustomerModal').style.display = 'none';
    });
    
    document.getElementById('cancelAddCustomerBtn').addEventListener('click', () => {
        document.getElementById('addCustomerModal').style.display = 'none';
    });
    
    document.getElementById('confirmAddCustomerBtn').addEventListener('click', addCustomer);
    
    // 编辑客户弹窗
    document.getElementById('closeEditCustomerModal').addEventListener('click', () => {
        document.getElementById('editCustomerModal').style.display = 'none';
        editingCustomerId = null;
    });
    
    document.getElementById('cancelEditCustomerBtn').addEventListener('click', () => {
        document.getElementById('editCustomerModal').style.display = 'none';
        editingCustomerId = null;
    });
    
    document.getElementById('confirmEditCustomerBtn').addEventListener('click', saveEditCustomer);
    
    // 导入结果弹窗
    document.getElementById('closeImportResultModal').addEventListener('click', () => {
        document.getElementById('importResultModal').style.display = 'none';
    });
    
    document.getElementById('closeImportResultBtn').addEventListener('click', () => {
        document.getElementById('importResultModal').style.display = 'none';
    });
}

// 保存根目录
async function saveRootDirectory() {
    const rootDirectory = document.getElementById('rootDirectoryInput').value;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ root_directory: rootDirectory })
        });
        
        if (response.ok) {
            alert('根目录保存成功');
        } else {
            alert('保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败，请重试');
    }
}

// 下载模板
function downloadTemplate() {
    window.location.href = '/api/customers/template';
}

// 导入客户
async function importCustomers(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/customers/import', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // 显示导入结果
        const importResult = document.getElementById('importResult');
        importResult.innerHTML = `
            <div class="import-count">成功导入 ${result.imported_count} 个客户</div>
            ${result.errors.length > 0 ? `
                <div class="import-errors">
                    <p>以下客户导入失败：</p>
                    ${result.errors.map(error => `<div class="import-error-item">${error}</div>`).join('')}
                </div>
            ` : ''}
        `;
        
        document.getElementById('importResultModal').style.display = 'flex';
        
        // 重新加载客户列表
        loadCustomers();
        
        // 清空文件输入
        e.target.value = '';
    } catch (error) {
        console.error('导入失败:', error);
        alert('导入失败，请重试');
    }
}

// 添加客户
async function addCustomer() {
    const name = document.getElementById('customerNameInput').value;
    const path = document.getElementById('customerPathInput').value;
    
    if (!name || !path) {
        alert('请填写完整信息');
        return;
    }
    
    try {
        const response = await fetch('/api/customers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                display_name: name,
                relative_path: path
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('addCustomerModal').style.display = 'none';
            loadCustomers();
            alert('客户添加成功');
        } else {
            alert(result.error || '添加失败');
        }
    } catch (error) {
        console.error('添加失败:', error);
        alert('添加失败，请重试');
    }
}

// 编辑客户
function editCustomer(customerId) {
    editingCustomerId = customerId;
    
    const customer = customers.find(c => c.id === customerId);
    if (!customer) return;
    
    document.getElementById('editCustomerNameInput').value = customer.display_name;
    document.getElementById('editCustomerPathInput').value = customer.relative_path;
    
    document.getElementById('editCustomerModal').style.display = 'flex';
}

// 保存编辑客户
async function saveEditCustomer() {
    if (!editingCustomerId) return;
    
    const name = document.getElementById('editCustomerNameInput').value;
    const path = document.getElementById('editCustomerPathInput').value;
    
    if (!name || !path) {
        alert('请填写完整信息');
        return;
    }
    
    try {
        const response = await fetch(`/api/customers/${editingCustomerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                display_name: name,
                relative_path: path
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('editCustomerModal').style.display = 'none';
            editingCustomerId = null;
            loadCustomers();
            alert('保存成功');
        } else {
            alert(result.error || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败，请重试');
    }
}

// 删除客户
async function deleteCustomer(customerId) {
    if (!confirm('确定要删除这个客户吗？删除后该客户的所有待办记录也会被删除。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/customers/${customerId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCustomers();
            alert('删除成功');
        } else {
            alert('删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}