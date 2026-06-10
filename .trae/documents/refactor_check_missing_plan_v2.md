# 发票智能检测升级 + 检查遗漏逻辑修正 + 首页简化（v1.1.3）

---

## 核心理解确认（根据用户反馈修正）

### ✅ 检查遗漏逻辑（保持数据库层面）

**用户归档规则：**
- 发票按**业务月份**归档到文件夹
- 例：6月开了5月的账 → 发票放在 客户/2026-05/ 下
- 所以"检查遗漏"应该看**这个月有没有给客户创建过待办并完成开票**

**检查遗漏的正确逻辑：**
```
结算月份 = 系统当前月份（如 2026-06）

所有登记的客户":
  → 查 todos 表中是否有该客户的 business_month = 2026-06 且 invoice_status = done

没有 → 判定为遗漏

遗漏客户列表
```

**与当前v1.1.2 逻辑基本正确（已有 database 检查方式：
- 已经在用
- 唯一要微调：把"business_month=当前月"的"待办记录存在且已开票"为判定

---

## 🔧 改动1：发票检测 → 智能扫描（含 ZIP 解压扫描）

**文件：** [file_service.py](file:///workspace/invoice_helper/static/css/style.css)

**现有旧逻辑（v1.1.2：
```
扫描 invoices 子目录 → 看是否有 .pdf/.xml/.ofd 按扩展名直接判定 → 是
问题：
- 只看 invoices 子目录（用户可能把发票放在月目录根或其他子目录）
- .zip 只看扩展名可能是表格压缩包（用户说 zip 里可能是 xlsx 等非发票文件
```

**新逻辑：**

**新增 步骤1：扫描整个月目录递归（不限定 invoices 子目录）**
```
扫描目录：{根目录}/{客户路径}/{business_month}/ 下的所有文件（递归含所有子目录

**步骤2：按文件类型分别判断**
| 文件类型 | 判定规则 |
|-----------|---------|
| `.xml` | ✅ 直接判定为发票（用户说 xml 一定是发票） |
| `.pdf` / `.ofd` | 文件名含20位连续数字 或 含"发票"/"invoice"关键词 → 发票 |
| `.zip` | ⚠️ **需解压后扫描内部文件 |
| 其他扩展名（.xlsx, .doc, .jpg 等 | ❌ 跳过，不是发票

**步骤3：ZIP解压扫描规则**
对每个 `.zip` 文件：
- 解压到临时目录
- 读取 zip 内部文件列表（不解压全部文件到磁盘，只读取 zip 内部的文件名判断：
  - 内部有 `.xml` → ✅ 这个 zip 是发票压缩包
  - 内部有 `.pdf` / `.ofd` → 按文件名规则判断（20位数字/发票关键词）
- 只要 zip 内部文件命中任一符合 →
- 判断
- 扫描完即释放 zip 内部文件列表
**不实际解压到磁盘，用 Python zipfile 模块只读列表即可

**新增函数：**

```python
def _is_invoice_file(filename):
    """判断单个文件是否是发票
    规则：
    - .xml → True
    - .pdf/.ofd → 文件名含20位数字 or 含"发票"/"invoice" → True
    - 其他 → False
    """

def detect_invoice_files(customer_path, business_month):
    """
    扫描客户月目录，检测发票文件
    返回: {
        "has_invoice": True/False,
        "files": ["file1.pdf", "file2.zip"],
        "file_count": 2
    }
    扫描逻辑:
    1. 递归扫描 {root}/{customer_path}/{business_month}/ 下所有文件
    2. 对每个文件:
       - .xml → 直接加入
       - .pdf/.ofd → 按文件名规则判断
       - .zip → 读取内部文件列表，按内部文件名规则判断
    3. 收集所有命中的文件
    """

def _scan_zip_invoice_files(customer_path, business_month):
    """
    扫描 zip 内部文件，判断 zip 是否含发票
    只读取 zip 内部文件名，不解压到磁盘
    内部文件规则:
    - 有 .xml → 发票
    - .pdf/.ofd → 文件名含20位数字 或 含"发票"/"invoice" → 发票
    """
```

**技术实现要点：**
- 用 `os.walk() 递归扫描整个月目录
- 用 `zipfile.ZipFile` 读取内部文件列表，只读列表不实际解压
- 支持中文文件扩展名小写统一转为小写：
- 20位数字正则：`r'\d{20}`
- 关键词不区分大小写匹配

---

## 🔧 改动2：检查遗漏 → 修正逻辑微调

**文件：** [todo_service.py](file:///workspace/invoice_helper/services/todo_service.py#L284-L311)

**当前逻辑（v1.1.2逻辑基本正确，但用户确认：
```python
# 当前月 = datetime.now().strftime('%Y-%m')
# 所有客户中，谁的 todos 表中没有 business_month = 当前月的待办记录
```

**修正后逻辑（v1.1.3增加限定：
```python
# 当前月 = datetime.now().strftime('%Y-%m')
# 所有客户中：
#   → 查是否存在 business_month = 当前月 AND invoice_status = 'done' 的待办记录
# 如果没有 → 遗漏
```

**关键点：** 增加 `invoice_status = 'done'（已开票）才叫"没遗漏"，因为用户说"按我的填报自己记录当月有没有结算"——所以判定逻辑是：**这个月给客户有完成的待办** → 不算遗漏。

---

## 🔧 改动3：「刷新状态」→ 同步升级

**文件：** [todo_service.py](file:///workspace/invoice_helper/services/todo_service.py#L213-L252)

把 `check_invoices_exist()` 调用改为新的 `detect_invoice_files()`

- 刷新状态仍按待办记录的 business_month 查找发票

---

## 🔧 改动4：首页筛选栏简化

**文件：** [index.html](file:///workspace/invoice_helper/templates/index.html)

**改动：**
- 移除筛选栏中的"业务月份"筛选框
- 保留"发送状态"和"客户"两个筛选条件
- 首页加载待办列表时，**默认只取当月待办**（business_month = 当前月）

**同步修改前端 JS** [app.js](file:///workspace/invoice_helper/static/js/app.js)

---

## 🔧 改动5：版本升级

- version.json：1.1.2 → **1.1.3**

---

## 完整文件改动清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `services/file_service.py` | ✏️ 重写函数 | 新增 `detect_invoice_files()` + `_is_invoice_file()` + `_scan_zip_for_invoice()`，废弃旧的 `check_invoices_exist()` |
| `services/todo_service.py` | ✏️ 重写函数 | `get_missing_current_month` 增加 `invoice_status='done'` 限定；`refresh_invoice_status` 改为调用新函数 |
| `templates/index.html` | ✏️ 简化UI | 移除"业务月份"筛选框 |
| `static/js/app.js` | ✏️ 适配 | 首页默认按当月取待办 |
| `version.json` | ✏️ 版本升级 | 1.1.2 → 1.1.3 |

---

## 验证清单

- [ ] **刷新状态**：月目录放 `24117000000001234567.pdf` → 刷新状态 → 变为已开票
- [ ] **刷新状态**：月目录放 `合同.pdf → 刷新状态 → **不误判**（没有20位数字也不含"发票"）
- [ ] **刷新状态**：月目录放 `随便.xml` → 刷新状态 → ✅ 直接判定为发票
- [ ] **刷新状态**：放一个 zip 含 xml 的压缩包 `发票.zip（内部含 `24117000000001234567.xml`） → 刷新状态 → 识别为发票
- [ ] **刷新状态**：放一个 zip 是表格的压缩包 `数据.zip（内部含 `销售表.xlsx`） → 刷新状态 → **不误判**
- [ ] **检查遗漏**：A客户本月有待办且已开票 → 检查遗漏 → 不显示A
- [ ] **检查遗漏**：B客户本月有待办 pending 未开票 → 检查遗漏 → 显示B（未完成开票）
- [ ] **检查遗漏**：C客户本月无待办 → 检查遗漏 → 显示C
- [ ] **首页筛选**：只有发送状态、客户两个筛选框
- [ ] **历史记录页**：保留月份筛选
- [ ] **导航栏**：显示 v1.1.3

---

## 风险说明

⚠️ **潜在风险：**
1. **zipfile 读取中文文件名：Python 的 zipfile 在 Windows 下对中文文件名编码可能有兼容性问题（GBK/CP437 编码），需在代码中做编码兜底处理

✅ **无破坏性变更：**
- 数据库 schema 不变
- 不删除已有数据
- 不改变 API 返回格式
