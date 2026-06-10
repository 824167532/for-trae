# 版本升级说明

本文档说明如何为「开票待办助手」升级版本号并发布新版本。

---

## 版本号规则

遵循 **语义化版本 2.0.0** (Semantic Versioning) 规范：

**格式**: `主版本号.次版本号.修订号` (MAJOR.MINOR.PATCH)

- **主版本号 (MAJOR)**: 当你做了不兼容的 API 或架构修改时递增
  - 例如：大规模重构、数据库表结构变化导致不兼容
  - 例如：1.0.0 → 2.0.0

- **次版本号 (MINOR)**: 当你做了向下兼容的功能性新增时递增
  - 例如：新增功能模块、增加新的API、优化已有功能
  - 例如：1.0.0 → 1.1.0

- **修订号 (PATCH)**: 当你做了向下兼容的问题修正时递增
  - 例如：修复Bug、修复拼写错误、小幅度性能优化
  - 例如：1.0.0 → 1.0.1

**示例**:
| 变更类型 | 当前版本 | 升级后版本 |
|---------|---------|-----------|
| 修复Bug | 1.0.0 | 1.0.1 |
| 新增功能 | 1.0.0 | 1.1.0 |
| 重大重构 | 1.0.0 | 2.0.0 |

---

## 升级版本号的操作步骤

### 方法一：手动修改（简单推荐）

**只有一个文件需要修改** → `version.json`

#### 1. 修改 version.json

打开项目根目录下的 `version.json` 文件，修改以下字段：

```json
{
  "version": "1.0.0",           ← 这里改为新版本号
  "version_name": "开票待办助手 v1.0.0",  ← 这里的版本号同步更新
  "release_date": "2026-06-10", ← 改为今天的日期
  "codename": "首版发布",       ← 可以更新版本代号（可选）
  "description": "描述说明",     ← 可以更新描述（可选）
  "release_notes": [            ← 添加本次更新的说明
    "✨ 新增: xxxxx功能",
    "🐛 修复: xxxxx问题",
    "🎨 优化: xxxxx体验"
  ]
}
```

**注意**:
- `version` 字段是程序读取的唯一真源，必须准确
- `version_name`、`release_date` 也建议同步更新
- `release_notes` 强烈建议更新，方便记录版本历史

#### 2. 运行打包脚本

```bash
python3 build_release.py
```

或 Windows 下：
```
python build_release.py
```

#### 3. 查看生成的发布包

打包成功后，文件会生成在：
- **Linux/macOS**: `/workspace/releases/invoice_helper_v{版本号}.zip`
- **Windows**: 项目目录的上层 `releases/` 文件夹中

---

### 方法二：命令行快速修改

在 Linux/macOS 终端执行：

```bash
# 假设要升级到 1.0.1
cd /workspace/invoice_helper

# 使用 sed 命令替换版本号
sed -i 's/"version": "1.0.0"/"version": "1.0.1"/g' version.json
sed -i 's/开票待办助手 v1.0.0/开票待办助手 v1.0.1/g' version.json

# 然后运行打包
python3 build_release.py
```

---

## release_notes 书写建议

建议使用以下表情符号前缀，让更新日志更清晰：

| 表情符号 | 含义 | 示例 |
|--------|-----|-----|
| 🎉 | 重大发布/里程碑 | 🎉 首次发布 |
| ✨ | 新增功能 | ✨ 新增客户批量导入功能 |
| 🐛 | 修复Bug | 🐛 修复macOS下文件夹打开失败问题 |
| 🎨 | UI/设计优化 | 🎨 优化玻璃拟态样式效果 |
| ⚡ | 性能优化 | ⚡ 优化待办列表加载速度 |
| 📝 | 文档更新 | 📝 更新README说明 |
| ♻️ | 代码重构 | ♻️ 重构文件服务模块 |
| 🖥️ | 平台兼容性 | 🖥️ 优化Windows 11兼容性 |
| 🔒 | 安全修复 | 🔒 修复XX安全问题 |

**示例**:
```json
"release_notes": [
  "✨ 新增: Excel导入时支持自定义列映射",
  "🐛 修复: 待办列表筛选状态重置问题",
  "🎨 优化: 设置页面布局更清晰",
  "⚡ 优化: 截图保存速度提升30%"
]
```

---

## 版本发布检查清单

每次发布新版本前，请确认以下事项：

- [ ] `version.json` 中的版本号已更新
- [ ] `version_name` 与版本号一致
- [ ] `release_date` 已更新为当前日期
- [ ] `release_notes` 已添加本次更新说明
- [ ] 项目能正常启动 (`python3 app.py` 无报错)
- [ ] 基本功能测试通过（创建待办、截图粘贴等）
- [ ] README.md 中的「版本历史」章节已添加新版本说明
- [ ] 运行 `build_release.py` 打包成功
- [ ] 验证 zip 文件完整（可解压并正常运行）

---

## 版本历史维护建议

建议在 README.md 的「版本历史」章节保持最近 3-5 个版本的更新记录。更早的版本可以省略，只保留重大版本的记录。

---

## 常见问题

### Q: 为什么版本号只需要修改 version.json？

A: 因为程序代码中通过 `version_utils.py` 从 `version.json` 读取版本号，实现了「单一真源」。启动信息、API 接口都从这里读取，所以只改一个地方即可。

### Q: 发布包会自动清理旧数据文件吗？

A: 不会。打包脚本会排除 `data/` 目录（仅保留一个空目录占位符），确保用户的数据库文件不会被覆盖。用户升级时只需解压新包，旧的 `data/invoice_helper.db` 可以继续使用或复制过去。

### Q: 打包脚本在哪里？

A: 项目根目录下的 `build_release.py`。运行后会在项目同级目录创建 `releases/` 文件夹，并生成类似 `invoice_helper_v1.0.0.zip` 的发布包。

### Q: 发布包放在哪里？

A: 打包脚本的输出：
- 实际存放路径: `../releases/`（相对于项目目录的 releases 文件夹）
- 文件名格式: `invoice_helper_v{版本号}.zip`

例如项目在 `/workspace/invoice_helper/`，则发布包在 `/workspace/releases/` 目录中。

---

## 版本升级示例

假设当前版本是 `1.0.0`，修复了一个小Bug：

### Step 1. 修改 version.json

```json
{
  "version": "1.0.1",
  "version_name": "开票待办助手 v1.0.1",
  "release_date": "2026-06-15",
  "codename": "Bug修复版",
  "description": "修复了截图文件名重复时的提示问题",
  "release_notes": [
    "🐛 修复: 截图文件名重复时未正确提示",
    "🎨 优化: 待办卡片悬停效果"
  ]
}
```

### Step 2. 更新 README.md

在「版本历史」章节添加：

```
### v1.0.1 (2026-06-15)
- 🐛 修复: 截图文件名重复时未正确提示
- 🎨 优化: 待办卡片悬停效果
```

### Step 3. 运行打包

```bash
cd /workspace/invoice_helper
python3 build_release.py
```

### Step 4. 查看结果

```
🎉 发布包构建完成!
  文件名: invoice_helper_v1.0.1.zip
  文件大小: 0.04 MB
  版本: 1.0.1
```

完成！🎉
