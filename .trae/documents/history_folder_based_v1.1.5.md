# 历史记录：业务月份基于文件夹名智能匹配（v1.1.5）

---

## 用户需求

1. **历史记录的"业务月份"筛选值**：仍然按 `yyyy/mm` 格式展示和下拉（如 `2026/05`），支持手动输入
2. **筛选逻辑**：用户选 `2026/05` → 查数据库 `business_month = '2026-05'` 的已开票记录 → 对每条记录查客户目录下实际的月份文件夹名（可能是 `202605`、`202605月`、`202603-202606`）
3. **展示**：历史记录列表里的"业务月份"那一列，**显示实际文件夹名**
4. **跨月文件夹规则**：文件夹 `202503-202506` → 搜 `2025/03`、`2025/04`、`2025/05`、`2025/06` 都能命中（复用 v1.1.3 的 `find_month_folder` 逻辑）
5. **首页待办列表和遗漏检查**：保持不变，仍然按数据库的 `business_month`（结算月份）

---

## 改动清单

### 🔧 改动1：file_service.py 新增方法

**文件**：[file_service.py](file:///workspace/invoice_helper/services/file_service.py)

**新增方法 `get_folder_name(customer_path, business_month)`**：

```python
def get_folder_name(self, customer_path, business_month):
    """
    查找客户目录下匹配业务月份的文件夹，返回文件夹名（只取最后一级目录名）

    输入: customer_path（如 "运营商/移动/广东"），business_month（如 "2026-06"）
    输出: 文件夹名，如 "202603-202606" / "202606月" / "202606"
          找不到则返回 business_month
    """
    # 复用 find_month_folder 的匹配逻辑（支持 202606 / 202603-202606 / 202606月）
    folder_path = self.find_month_folder(customer_path, business_month)
    if folder_path:
        return os.path.basename(folder_path)
    return business_month
```

说明：直接复用现有的 `find_month_folder` 逻辑（v1.1.3 已写好），不新增匹配规则。

---

### 🔧 改动2：todo_service.py → get_history 改造

**文件**：[todo_service.py](file:///workspace/invoice_helper/services/todo_service.py)

**改造 `get_history` 方法**：

```python
def get_history(self, customer_id=None, business_month=None, send_status=None):
    # 原有查询逻辑不变
    # ...
    rows = cursor.fetchall()
    conn.close()

    records = [dict(row) for row in rows]

    # 对每条记录，查找实际的文件夹名
    file_service = self.get_file_service()
    for rec in records:
        folder_name = file_service.get_folder_name(
            rec['customer_path'],
            rec['business_month']
        )
        rec['folder_name'] = folder_name   # 新增字段，存实际文件夹名

    return records
```

这样每条历史记录会多一个 `folder_name` 字段（如 `202603-202606`），展示给用户看。

---

### 🔧 改动3：history.html → 月份筛选支持输入+下拉

**文件**：[history.html](file:///workspace/invoice_helper/templates/history.html)

**把业务月份的 `<select>` 改成 `<input list="monthList">`（HTML5 datalist）**

原有的 select 结构：
```html
<div class="filter-group">
    <label class="filter-label">业务月份：</label>
    <select class="filter-select" id="monthFilter">
        <option value="">全部月份</option>
    </select>
</div>
```

修改后：
```html
<div class="filter-group">
    <label class="filter-label">业务月份：</label>
    <input type="text" class="filter-input" id="monthFilter" list="monthOptions" placeholder="2026/06">
    <datalist id="monthOptions">
        <!-- JS动态填充：<option value="2026/06"> -->
    </datalist>
</div>
```

这样用户可以：
- 下拉选择（datalist 自动提供已有月份）
- 手动输入（按 `2026/06` 格式）

**同时：表格中的"业务月份"列，展示 `folder_name`（实际文件夹名）**

在 history.html 的表格列中，把 `business_month` 改成显示 `folder_name`：
```html
<td>${record.folder_name}</td>      <!-- 原来显示 business_month，现在显示实际文件夹名 -->
```

---

### 🔧 改动4：history.js → 月份筛选格式转换

**文件**：[history.js](file:///workspace/invoice_helper/static/js/history.js)

**修改 `loadHistory()` 中的月份参数处理**：

```js
// 用户输入的是 "2026/06" 格式，需转为 "2026-06" 传给后端
let businessMonth = document.getElementById('monthFilter').value.trim();
if (businessMonth) {
    // 兼容用户多种输入格式：2026/06、2026-06、202606 → 统一转成 2026-06
    businessMonth = normalizeMonth(businessMonth);
}
// params.append('business_month', businessMonth);
```

**新增辅助函数 `normalizeMonth(input)`**：
```js
function normalizeMonth(input) {
    if (!input) return '';
    const s = input.trim();
    // 2026/06 → 2026-06
    const m1 = s.match(/^(\d{4})[\/\-\.](\d{1,2})$/);
    if (m1) return `${m1[1]}-${m1[2].padStart(2, '0')}`;
    // 202606 → 2026-06
    const m2 = s.match(/^(\d{4})(\d{2})$/);
    if (m2) return `${m2[1]}-${m2[2]}`;
    return s;   // 无法识别时原样返回（可能查询为空，但不报错）
}
```

**月份下拉框的填充逻辑**：

从已有数据的 `business_month` 字段提取月份，统一转成 `yyyy/mm` 格式填入 datalist：
```js
const uniqueMonths = [...new Set(history.map(h => h.business_month))].sort((a, b) => b.localeCompare(a));
const optsHtml = uniqueMonths.map(m => {
    const [y, mm] = m.split('-');
    return `<option value="${y}/${mm}">`;
}).join('');
document.getElementById('monthOptions').innerHTML =
    '<option value="">全部月份</option>' + optsHtml;
```

**表格渲染时显示 `folder_name` 而非 `business_month`**：

在 `renderHistory` 中，把 `${item.business_month}` 改成 `${item.folder_name}`。

---

### 🔧 改动5：版本号升级

**文件**：[version.json](file:///workspace/invoice_helper/version.json)

- 1.1.4 → **1.1.5**

---

## 完整文件改动清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `services/file_service.py` | ✏️ 新增方法 | 新增 `get_folder_name(customer_path, business_month)` 返回文件夹名 |
| `services/todo_service.py` | ✏️ 改造方法 | `get_history` 每条记录附加 `folder_name` 字段 |
| `templates/history.html` | ✏️ 改造UI | 业务月份改为 input+datalist（可输入可下拉）；表格列显示 folder_name |
| `static/js/history.js` | ✏️ 改造逻辑 | 月份输入格式自动转换；下拉选项从已有数据填充；渲染表格展示 folder_name |
| `version.json` | ✏️ 版本号 | 1.1.4 → 1.1.5 |

---

## 数据流向示意

```
用户输入 "2026/05"
    ↓
normalizeMonth("2026/05") → "2026-05"
    ↓
/api/todos/history?business_month=2026-05
    ↓
SQL: WHERE business_month = '2026-05' → 查出客户A(2026-05)、客户B(2026-05)
    ↓
对每条记录调用 get_folder_name(customer_path, '2026-05'):
    客户A → 目录下有 "202603-202606" → 返回 "202603-202606"
    客户B → 目录下有 "202605月" → 返回 "202605月"
    ↓
返回: [{...business_month:"2026-05", folder_name:"202603-202606", ...}, ...]
    ↓
前端表格渲染: 显示 folder_name 列（"202603-202606"）
```

---

## 验证清单

- [ ] 首页待办：不受影响，筛选和展示都按数据库 business_month
- [ ] 历史记录：月份筛选框显示 `2026/06` 格式；可下拉也可手动输入
- [ ] 历史记录：选 `2026/05` → 表格展示的月份列显示实际文件夹名（如 `202603-202606`）
- [ ] 历史记录：输入各种格式（`2026/05`、`2026-05`、`202605`）都能正确解析
- [ ] 检查遗漏：不受影响，仍然按结算月份
- [ ] 导航栏显示 v1.1.5
