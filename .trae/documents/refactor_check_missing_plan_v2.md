# 发票智能检测（含ZIP解压扫描）+ 检查遗漏修正 + 月份文件夹智能识别 + 首页简化（v1.1.3）

---

## 核心理解确认（根据用户反馈修正）

### ✅ 检查遗漏逻辑（数据库层面）

**用户归档规则：**
- 发票按**业务月份**归档到文件夹
- 例：6月开了5月的账 → 发票放在 客户/202605/ 下（文件夹命名见下方）
- 所以"检查遗漏"应该看**这个月有没有给客户创建过待办并完成开票**

**检查遗漏的判定逻辑：**
```
结算月份 = 系统当前月份（如 2026-06）

对"每个已登记的客户":
  → 查 todos 表中是否存在 business_month = 当前月 AND invoice_status = 'done' 的记录
  → 如果没有 → 判定为遗漏

返回遗漏客户列表
```

---

### ✅ 月份文件夹命名变体（用户新增要求）

**用户实际文件夹命名：**
| 格式 | 示例 | 说明 |
|------|------|------|
| 纯6位数字 | `202604` | 常见标准格式 |
| 跨月区间 | `202603-202604` | 跨月结算 |
| 6位+月字 | `202604月` | 带中文"月" |

**当前系统的月份格式：** `YYYY-MM`（如 `2026-06`）

**需要智能匹配：** 系统要自动在客户目录下找到匹配当前月的文件夹名

---

## 🔧 改动1：新增月份文件夹智能识别

**文件：** [file_service.py](file:///workspace/invoice_helper/services/file_service.py)

**新增函数 `find_month_folder(customer_path, business_month)`：**

```
输入: customer_path（客户相对路径如 "运营商/移动/广东"）
      business_month（业务月份如 "2026-06"）

步骤:
  1. 取出目标年月 → "2026" + "06"
  2. 目标文件名目标 = "202606"
  3. 扫描客户根目录下的一级子文件夹（只看一层，不递归）
  4. 对每个文件夹名做匹配:
     → 规则1：文件夹名包含 "202606" → 命中
         例: "202606" ✓, "202604-202606" ✓, "202606月" ✓
     → 规则2：取文件夹名中所有 6 位连续数字段，任一字段 == "202606" → 命中
         例: "202603-202606" → 提取 "202603"/"202606" → 第二个字段命中
  5. 返回第一个命中的文件夹完整路径（绝对路径）
  6. 没有命中返回 None（表示该客户该月没有文件夹）

输出: /absolute/path/to/客户/202606/  或  None
```

**设计说明：**
- 只扫描客户目录下的**一级子文件夹**（不递归更深层，月份文件夹一定在第一层）
- 用"包含匹配"而非"精确等于"，覆盖所有命名变体
- 跨月文件夹（`202603-202604`）会被匹配为202603月和202604月都命中——这符合用户习惯（跨月结的发票都放进去）
- 如果找不到任何匹配的文件夹 → 返回 None → 该客户该月判定为"没有发票"

---

## 🔧 改动2：发票检测 → 智能扫描（含 ZIP 解压扫描）

**文件：** [file_service.py](file:///workspace/invoice_helper/services/file_service.py)

**现有旧逻辑（v1.1.2）：**
```
扫描 invoices 子目录 → 按扩展名直接判定 .pdf/.xml/.ofd
问题:
- 只看 invoices 子目录（用户可能把发票放在月目录根或其他子目录）
- .zip 只看扩展名可能是表格压缩包（用户说 zip 里可能是 xlsx 等非发票文件）
```

**新逻辑（v1.1.3）：**

**步骤1：用 find_month_folder() 找到月目录**
```
月目录 = find_month_folder(customer_path, business_month)
如果月目录不存在 → 返回 {"has_invoice": False, ...}
```

**步骤2：递归扫描月目录下所有文件（不限定子目录）**
```
对月目录下所有文件（递归）做分类判断:
```

**步骤3：按文件类型分别判断**

| 文件类型 | 判定规则 |
|-----------|---------|
| `.xml` | ✅ **直接判定为发票**（用户明确说 xml 一定是发票） |
| `.pdf` / `.ofd` | 文件名含 20 位连续数字 **或** 含"发票"/"invoice"关键词 → 发票 |
| `.zip` | ⚠️ **需读取 zip 内部文件列表**判断 |
| 其他（.xlsx, .doc, .jpg 等） | ❌ **跳过，不是发票** |

**步骤4：ZIP 解压扫描（只读列表，不实际解压到磁盘）**
```
对每个 .zip 文件:
  用 Python zipfile.ZipFile 读取内部文件列表
  对内部每个文件做判断:
    - .xml → ✅ 这个 zip 含发票
    - .pdf/.ofd → 按文件名规则判断（20位数字 或 发票关键词）
  如果 zip 内部有任何命中 → 该 zip 判定为发票压缩包
  扫描完即释放 zip 对象，不写出任何文件到磁盘
```

**新增函数：**

```python
def _is_invoice_file(filename):
    """判断单个文件是否是发票
    规则：
    - .xml → True（用户说xml一定是发票）
    - .pdf/.ofd → 文件名含20位数字 or 含"发票"/"invoice" → True
    - 其他 → False
    """

def _scan_zip_for_invoice(zip_path):
    """读取 zip 内部文件列表，判断 zip 是否含发票
    不实际解压到磁盘，仅读 zip 内部文件名列表
    内部文件规则:
    - 有 .xml → 发票
    - .pdf/.ofd → 文件名含20位数字 或 含"发票"/"invoice" → 发票
    返回: True/False
    """

def detect_invoice_files(customer_path, business_month):
    """
    检测客户某月目录下是否存在发票文件
    步骤:
    1. find_month_folder() 找到月目录
    2. 递归扫描月目录下所有文件
    3. 对每个文件按类型判断
    4. 对 zip 额外读取内部列表判断
    返回: {
        "has_invoice": True/False,
        "files": ["file1.pdf", "file2.zip"],
        "file_count": 2,
        "folder_path": "/absolute/path/to/月文件夹"
    }
    """
```

**技术实现要点：**
- 用 `os.walk()` 递归扫描整个月目录
- 用 `zipfile.ZipFile` + `namelist()` 只读 zip 内部文件名
- 20位数字正则：`r'\d{20}'`
- 关键词不区分大小写：`'发票' in filename.lower()` 或 `'invoice' in filename.lower()`
- 处理中文文件名：文件扩展名统一转小写后判断

---

## 🔧 改动3：检查遗漏 → 修正逻辑

**文件：** [todo_service.py](file:///workspace/invoice_helper/services/todo_service.py#L284-L311)

**修正后的逻辑：**
```python
current_month = datetime.now().strftime('%Y-%m')  # 如 2026-06

# 所有客户
cursor.execute('SELECT id, display_name FROM customers')
all_customers = cursor.fetchall()

# 本月已有已开票完成待办的客户
cursor.execute(
    '''
    SELECT DISTINCT customer_id FROM todos
    WHERE business_month = ? AND invoice_status = 'done'
    ''',
    (current_month,)
)
customers_with_invoice = [row['customer_id'] for row in cursor.fetchall()]

# 没被覆盖的客户就是遗漏
missing = [c for c in all_customers if c['id'] not in customers_with_invoice]
```

**关键点：** 增加 `invoice_status = 'done'`（已开票完成）的限定条件
- 只有"本月创建了待办且发票检测到→已完成开票"才叫"没遗漏"
- 如果只创建了待办但还是 pending → 算遗漏（还没开票）

---

## 🔧 改动4：「刷新状态」→ 同步升级

**文件：** [todo_service.py](file:///workspace/invoice_helper/services/todo_service.py#L213-L252)

把 `check_invoices_exist()` 调用改为新的 `detect_invoice_files()`

- 刷新状态仍按每条待办记录的 business_month 查找发票（业务月份不变）
- 扫描路径由 `find_month_folder()` 智能识别实际文件夹名
- 检测规则用新的 `detect_invoice_files()`（支持 zip 内部扫描）

---

## 🔧 改动5：首页筛选栏简化

**文件：** [index.html](file:///workspace/invoice_helper/templates/index.html)

**改动：**
- 移除筛选栏中的"业务月份"筛选框
- 保留"发送状态"和"客户"两个筛选条件
- 首页加载待办列表时，**默认只取当月待办**（business_month = 当前月）

**同步修改前端 JS** [app.js](file:///workspace/invoice_helper/static/js/app.js)

---

## 🔧 改动6：版本升级

- version.json：1.1.2 → **1.1.3**

---

## 完整文件改动清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `services/file_service.py` | ✏️ 大幅重写 | 新增 `find_month_folder()` 智能识别月份文件夹名；新增 `detect_invoice_files()` 含 zip 内部扫描；新增 `_is_invoice_file()` 和 `_scan_zip_for_invoice()` 辅助函数；废弃旧的 `check_invoices_exist()` |
| `services/todo_service.py` | ✏️ 重写函数 | `get_missing_current_month` 增加 `invoice_status='done'` 限定；`refresh_invoice_status` 改为调用新的 `detect_invoice_files()` |
| `templates/index.html` | ✏️ 简化UI | 移除"业务月份"筛选框 |
| `static/js/app.js` | ✏️ 适配 | 首页默认按当月取待办 |
| `version.json` | ✏️ 版本升级 | 1.1.2 → 1.1.3 |

---

## 验证清单

- [ ] **月份文件夹识别**：客户目录下有 `202606` → 正确识别
- [ ] **月份文件夹识别**：客户目录下有 `202604-202606` → 正确识别为 2026-06
- [ ] **月份文件夹识别**：客户目录下有 `202606月` → 正确识别
- [ ] **月份文件夹识别**：客户目录下没有匹配当前月的文件夹 → 返回 None，判定无发票
- [ ] **发票检测**：月目录放 `24117000000001234567.pdf` → 刷新状态 → 变为已开票
- [ ] **发票检测**：月目录放 `合同.pdf` → 刷新状态 → **不误判**（没有20位数字也不含"发票"）
- [ ] **发票检测**：月目录放 `随便.xml` → 刷新状态 → ✅ 直接判定为发票
- [ ] **发票检测**：放 zip 含 xml 的压缩包 `发票.zip`（内部含 `24117000000001234567.xml`） → 刷新状态 → 识别为发票
- [ ] **发票检测**：放 zip 是表格的压缩包 `数据.zip`（内部含 `销售表.xlsx`） → 刷新状态 → **不误判**
- [ ] **检查遗漏**：A客户本月有待办且已开票 → 检查遗漏 → 不显示A
- [ ] **检查遗漏**：B客户本月有待办 pending 未开票 → 检查遗漏 → 显示B
- [ ] **检查遗漏**：C客户本月无待办 → 检查遗漏 → 显示C
- [ ] **首页筛选**：只有发送状态、客户两个筛选框
- [ ] **历史记录页**：保留月份筛选
- [ ] **导航栏**：显示 v1.1.3

---

## 风险说明

⚠️ **潜在风险：**
1. **zipfile 读取中文文件名**：Python 的 zipfile 在 Windows 下对中文文件名编码可能有兼容性问题（GBK/CP437 编码），需在代码中做编码兜底处理
2. **月份文件夹匹配顺序**：如果客户目录同时有 `202606` 和 `202605-202606` → 当前逻辑返回第一个命中的即可（两个都能扫描到发票，不影响功能判定）

✅ **无破坏性变更：**
- 数据库 schema 不变
- 不删除已有数据
- 不改变 API 返回格式
- 纯逻辑升级，不影响已有记录

