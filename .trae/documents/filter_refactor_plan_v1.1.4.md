# 筛选栏统一改造（v1.1.4）

---

## 问题清单

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | 首页筛选没有"应用筛选"按钮 | index.html | 目前只有下拉框，靠 change 事件自动刷新，用户不清楚筛选如何触发 |
| 2 | 历史记录业务月份使用 `<input type="month">` | history.html | 在某些浏览器下表现为纯输入框，用户不知道输入格式（YYYY-MM） |
| 3 | "🔍 筛选记录" emoji 标题太难看 | index.html / history.html | 去掉文字标题，统一用"应用筛选"按钮风格 |

---

## 改动方案

### 🔧 改动1：首页筛选栏统一风格

**文件**：[index.html](file:///workspace/invoice_helper/templates/index.html)

**当前**（index.html 筛选栏部分）：
```html
<div class="filter-bar">
    <span class="filter-bar-title">🔍 筛选记录</span>
    <div class="filter-group">
        <label class="filter-label">发送状态：</label>
        <select class="filter-select" id="sendStatusFilter">
            <option value="unsent">未发送</option>
            <option value="sent">已发送</option>
            <option value="all">全部</option>
        </select>
    </div>
    <div class="filter-group">
        <label class="filter-label">客户：</label>
        <select class="filter-select" id="customerFilter">
            <option value="">全部客户</option>
        </select>
    </div>
</div>
```

**修改后**：
```html
<div class="filter-bar">
    <div class="filter-group">
        <label class="filter-label">发送状态：</label>
        <select class="filter-select" id="sendStatusFilter">
            <option value="unsent">未发送</option>
            <option value="sent">已发送</option>
            <option value="all">全部</option>
        </select>
    </div>
    <div class="filter-group">
        <label class="filter-label">客户：</label>
        <select class="filter-select" id="customerFilter">
            <option value="">全部客户</option>
        </select>
    </div>
    <button class="btn btn-secondary" id="applyFilterBtn">应用筛选</button>
</div>
```

**改动点**：
- ✅ 移除 `<span class="filter-bar-title">🔍 筛选记录</span>`
- ✅ 在最后加 `<button class="btn btn-secondary" id="applyFilterBtn">应用筛选</button>`

---

### 🔧 改动2：历史记录页筛选栏统一风格 + 业务月份改为下拉选择

**文件**：[history.html](file:///workspace/invoice_helper/templates/history.html)

**当前**：
```html
<div class="filter-bar">
    <span class="filter-bar-title">🔍 筛选记录</span>
    <div class="filter-group">
        <label class="filter-label">客户：</label>
        <select class="filter-select" id="customerFilter">
            <option value="">全部客户</option>
        </select>
    </div>
    <div class="filter-group">
        <label class="filter-label">业务月份：</label>
        <input type="month" class="filter-input" id="monthFilter">
    </div>
    <div class="filter-group">
        <label class="filter-label">发送状态：</label>
        <select class="filter-select" id="sendStatusFilter">
            <option value="">全部</option>
            <option value="unsent">未发送</option>
            <option value="sent">已发送</option>
        </select>
    </div>
    <button class="btn btn-secondary" id="applyFilterBtn">应用筛选</button>
</div>
```

**修改后**：
```html
<div class="filter-bar">
    <div class="filter-group">
        <label class="filter-label">客户：</label>
        <select class="filter-select" id="customerFilter">
            <option value="">全部客户</option>
        </select>
    </div>
    <div class="filter-group">
        <label class="filter-label">业务月份：</label>
        <select class="filter-select" id="monthFilter">
            <option value="">全部月份</option>
        </select>
    </div>
    <div class="filter-group">
        <label class="filter-label">发送状态：</label>
        <select class="filter-select" id="sendStatusFilter">
            <option value="">全部</option>
            <option value="unsent">未发送</option>
            <option value="sent">已发送</option>
        </select>
    </div>
    <button class="btn btn-secondary" id="applyFilterBtn">应用筛选</button>
</div>
```

**改动点**：
- ✅ 移除 `<span class="filter-bar-title">🔍 筛选记录</span>`
- ✅ `业务月份：` 的 `<input type="month">` 改为 `<select>` 下拉框，选项从已有数据动态生成

---

### 🔧 改动3：首页 app.js → 改为按钮触发筛选

**文件**：[app.js](file:///workspace/invoice_helper/static/js/app.js)

**当前 initFilters()**：
```js
function initFilters() {
    document.getElementById('sendStatusFilter').addEventListener('change', loadTodos);
    document.getElementById('customerFilter').addEventListener('change', loadTodos);
}
```

**修改后**：
```js
function initFilters() {
    document.getElementById('applyFilterBtn').addEventListener('click', loadTodos);
}
```

**改动点**：
- ✅ 首页筛选从"下拉即刷新"改为"点击应用筛选按钮才刷新"（与历史记录页一致）

---

### 🔧 改动4：历史记录 history.js → 业务月份改为动态下拉

**文件**：[history.js](file:///workspace/invoice_helper/static/js/history.js)

**修改点**：
1. `loadHistory()` 拿到历史记录数据后，提取所有 business_month，去重、按倒序排列，填充到 `monthFilter` 下拉框
2. 初始化时 `monthFilter` 默认选"全部月份"（不做月份筛选）

**具体修改**：

在 `loadHistory()` 函数内，`renderHistory(history)` 之前或之后追加：
```js
// 从历史记录中提取所有业务月份，去重后填充下拉框
const months = [...new Set(history.map(h => h.business_month))].sort((a, b) => b.localeCompare(a));
const monthSelect = document.getElementById('monthFilter');
const currentValue = monthSelect.value;
monthSelect.innerHTML = '<option value="">全部月份</option>' +
    months.map(m => `<option value="${m}">${m}</option>`).join('');
monthSelect.value = currentValue;
```

这样用户打开历史记录页后，能看到已有的所有月份列表，直接选一个就行，不用手动输入。

---

### 🔧 改动5：CSS 清理（可选）

**文件**：[style.css](file:///workspace/invoice_helper/static/css/style.css)

`.filter-bar-title` 这个 CSS 类目前可能不再使用，但保留不影响功能，不需要强制删除。

---

### 🔧 改动6：版本号升级

**文件**：[version.json](file:///workspace/invoice_helper/version.json)

- 1.1.3 → **1.1.4**

---

## 完整文件改动清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `templates/index.html` | ✏️ 修改筛选栏 | 去掉 "🔍 筛选记录" 标题；末尾加"应用筛选"按钮 |
| `templates/history.html` | ✏️ 修改筛选栏 | 去掉 "🔍 筛选记录" 标题；业务月份 `<input type="month">` 改为 `<select>` 下拉 |
| `static/js/app.js` | ✏️ 筛选触发方式 | initFilters() 改为监听 applyFilterBtn 的 click 事件 |
| `static/js/history.js` | ✏️ 月份下拉填充 | loadHistory() 中从历史数据提取月份列表，填充到 monthFilter 下拉 |
| `version.json` | ✏️ 版本号 | 1.1.3 → 1.1.4 |

---

## 验证清单

- [ ] **首页筛选**：有"应用筛选"按钮，点击后刷新列表
- [ ] **首页筛选**：没有 "🔍 筛选记录" 文字标题
- [ ] **历史记录筛选**：业务月份是下拉框，能选已有的月份
- [ ] **历史记录筛选**：没有 "🔍 筛选记录" 文字标题
- [ ] **历史记录筛选**：月份下拉的选项从已有数据动态生成，按倒序排列
- [ ] **两页风格一致**：都有"应用筛选"按钮，没有 emoji 标题
- [ ] **导航栏**：显示 v1.1.4
