/**
 * 开票待办助手 - 设置页面JavaScript
 */

// 全局变量
let customers = [];
let editingCustomerId = null;
let scannedFolders = [];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadRootDirectory();
    loadCustomers();
    initButtons();
    initModals();
    initScanTool();
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

// ========== 文件夹扫描工具 ==========

function initScanTool() {
    // 使用根目录路径
    document.getElementById('pasteRootDirBtn').addEventListener('click', () => {
        const rootDir = document.getElementById('rootDirectoryInput').value;
        document.getElementById('scanDirectoryInput').value = rootDir;
    });
    
    // 扫描按钮
    document.getElementById('scanFoldersBtn').addEventListener('click', scanFolders);
    
    // 全选/取消全选
    document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.folder-checkbox:not(:disabled)');
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
            updateRowStatus(cb.closest('tr'), cb.checked ? '待导入' : '未选择');
        });
    });
    
    document.getElementById('selectAllFoldersBtn').addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.folder-checkbox:not(:disabled)');
        checkboxes.forEach(cb => {
            cb.checked = true;
            updateRowStatus(cb.closest('tr'), '待导入');
        });
        document.getElementById('selectAllCheckbox').checked = true;
    });
    
    document.getElementById('deselectAllFoldersBtn').addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.folder-checkbox:not(:disabled)');
        checkboxes.forEach(cb => {
            cb.checked = false;
            updateRowStatus(cb.closest('tr'), '未选择');
        });
        document.getElementById('selectAllCheckbox').checked = false;
    });
    
    // 批量导入选中
    document.getElementById('importSelectedFoldersBtn').addEventListener('click', importSelectedFolders);
}

// 扫描文件夹
async function scanFolders() {
    const dirPath = document.getElementById('scanDirectoryInput').value.trim();
    
    if (!dirPath) {
        alert('请输入目录路径');
        return;
    }
    
    const scanBtn = document.getElementById('scanFoldersBtn');
    const originalText = scanBtn.innerHTML;
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 6v6l4 2"></path></svg>扫描中...';
    
    try {
        const response = await fetch('/api/scan/folders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ base_dir: dirPath })
        });
        
        const result = await response.json();
        
        if (result.success) {
            scannedFolders = result.folders;
            renderScanResult(scannedFolders);
        } else {
            alert(result.error || '扫描失败');
            document.getElementById('scanResultSection').style.display = 'none';
        }
    } catch (error) {
        console.error('扫描失败:', error);
        alert('扫描失败，请检查目录路径是否正确');
        document.getElementById('scanResultSection').style.display = 'none';
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = originalText;
    }
}

// 渲染扫描结果
function renderScanResult(folders) {
    const resultSection = document.getElementById('scanResultSection');
    const tbody = document.getElementById('scanResultList');
    
    if (!folders || folders.length === 0) {
        document.getElementById('scanFolderCount').textContent = '0';
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 24px; color: var(--text-muted);">该目录下没有可用的子文件夹</td></tr>';
        resultSection.style.display = 'block';
        return;
    }
    
    document.getElementById('scanFolderCount').textContent = folders.length;
    
    // 获取已有客户的名称
    const existingNames = new Set(customers.map(c => c.display_name));
    
    tbody.innerHTML = folders.map(folder => {
        const isExists = existingNames.has(folder.display_name);
        return `
            <tr data-folder-name="${folder.display_name}">
                <td>
                    <input type="checkbox" class="folder-checkbox" 
                           data-name="${folder.display_name}" 
                           data-path="${folder.relative_path}"
                           ${isExists ? 'disabled checked' : ''}>
                </td>
                <td>${folder.display_name}${folder.has_sub_dirs ? ' <span style="color: var(--text-muted); font-size: 12px;">(包含子目录)</span>' : ''}</td>
                <td><code style="color: var(--text-secondary);">${folder.relative_path}</code></td>
                <td>
                    ${isExists 
                        ? '<span style="color: var(--success-color); font-weight: 600;">✓ 已存在</span>' 
                        : '<span style="color: var(--text-muted);">未选择</span>'}
                </td>
            </tr>
        `;
    }).join('');
    
    // 为复选框添加事件监听
    document.querySelectorAll('.folder-checkbox').forEach(cb => {
        cb.addEventListener('change', (e) => {
            updateRowStatus(e.target.closest('tr'), e.target.checked ? '待导入' : '未选择');
        });
    });
    
    // 重置全选状态
    document.getElementById('selectAllCheckbox').checked = false;
    
    resultSection.style.display = 'block';
}

// 更新行状态显示
function updateRowStatus(row, status) {
    const statusCell = row.querySelector('td:last-child');
    const checkbox = row.querySelector('.folder-checkbox');
    
    if (checkbox.disabled) {
        statusCell.innerHTML = '<span style="color: var(--success-color); font-weight: 600;">✓ 已存在</span>';
        return;
    }
    
    if (status === '待导入') {
        statusCell.innerHTML = '<span style="color: var(--warning-color); font-weight: 600;">&bull; 待导入</span>';
    } else if (status === '导入中') {
        statusCell.innerHTML = '<span style="color: var(--info-color); font-weight: 600;">&rarr; 导入中...</span>';
    } else if (status === '成功') {
        statusCell.innerHTML = '<span style="color: var(--success-color); font-weight: 600;">✓ 成功</span>';
    } else if (status === '失败') {
        statusCell.innerHTML = '<span style="color: var(--danger-color); font-weight: 600;">✗ 失败</span>';
    } else {
        statusCell.innerHTML = '<span style="color: var(--text-muted);">未选择</span>';
    }
}

// 批量导入选中的文件夹
async function importSelectedFolders() {
    const checkboxes = document.querySelectorAll('.folder-checkbox:checked:not(:disabled)');
    
    if (checkboxes.length === 0) {
        alert('请至少选择一个文件夹');
        return;
    }
    
    if (!confirm(`确定要导入选中的 ${checkboxes.length} 个客户吗？`)) {
        return;
    }
    
    const importBtn = document.getElementById('importSelectedFoldersBtn');
    const originalText = importBtn.innerHTML;
    importBtn.disabled = true;
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const cb of checkboxes) {
        const row = cb.closest('tr');
        const name = cb.dataset.name;
        const path = cb.dataset.path;
        
        updateRowStatus(row, '导入中');
        
        try {
            const response = await fetch('/api/customers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    display_name: name,
                    relative_path: path
                })
            });
            
            if (response.ok) {
                successCount++;
                updateRowStatus(row, '成功');
                cb.disabled = true;
            } else {
                errorCount++;
                updateRowStatus(row, '失败');
            }
        } catch (error) {
            errorCount++;
            updateRowStatus(row, '失败');
        }
    }
    
    importBtn.disabled = false;
    importBtn.innerHTML = originalText;
    
    // 重新加载客户列表
    loadCustomers();
    
    // 提示结果
    let message = `导入完成！\n成功: ${successCount} 个`;
    if (errorCount > 0) {
        message += `\n失败: ${errorCount} 个`;
    }
    alert(message);
}