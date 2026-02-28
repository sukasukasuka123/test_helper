# 实验室面试管理工具

基于 PySide6 开发的桌面应用，用于实验室面试的全流程标准化管理，支持题库导入、随机抽题、评分记录、数据分析，以及 AI 智能助手（基于通义千问）。

## 技术栈

- **UI 框架**: PySide6 (Qt for Python)
- **数据库**: SQLite3（WAL 模式，单例连接管理）
- **文件解析**: openpyxl（Excel）、csv（CSV）
- **AI Agent**: LangChain + 通义千问（DashScope）
- **Python 版本**: 3.11+

## 项目结构

```
.
├── main.py                       # 程序入口，初始化所有服务和 UI
├── interview.db                  # SQLite 数据库文件（运行时生成）
├── .env                          # 环境变量（API Key 等，需自行创建）
├── UI/
│   ├── base_panel.py             # 基础面板组件（PanelFrame）
│   ├── import_panel.py           # 题库导入面板
│   ├── interviewee_panel.py      # 面试者信息面板
│   ├── question_select_panel.py  # 题库选择面板
│   ├── question_runner_panel.py  # 抽题与评分面板
│   ├── question_widget.py        # 单题显示与评分组件
│   ├── stats_panel.py            # 面试结束与记录保存面板
│   ├── session_controller.py     # 面试会话状态机
│   ├── analysis_panel.py         # 雷达图分析面板
│   ├── export_panel.py           # 数据导出面板
│   └── agent_panel.py            # AI 助手聊天界面
└── service/
    ├── db.py                     # 数据库管理（单例模式）
    ├── schema.py                 # 数据库表结构初始化
    ├── importer.py               # 题库导入服务（CSV/Excel）
    ├── interviewee.py            # 面试者管理（创建、去重哈希）
    ├── meta.py                   # 题库元数据（题型、难度枚举）
    ├── selector.py               # 题目选择器（确定性随机抽题）
    ├── stats.py                  # 面试记录缓冲与批量写入
    ├── analyzer.py               # 面试者数据分析（加权雷达图数据）
    ├── exporter.py               # 面试记录导出（Excel）
    ├── agent_core.py             # Agent 核心（LangChain + Agentic Loop）
    └── agent_tools.py            # Agent 工具集（10 个工具）
```

## 数据库设计

### interviewee（面试者表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| name | TEXT NOT NULL | 姓名 |
| email | TEXT | 邮箱 |
| phone | TEXT | 电话 |
| raw_info | TEXT NOT NULL | 原始信息 JSON |
| info_hash | TEXT NOT NULL | SHA256 哈希（去重用） |
| created_at | TEXT NOT NULL | 创建时间 |

### question_bank（题库表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| q_type | TEXT NOT NULL | 题目类型 |
| difficulty | TEXT NOT NULL | 难度等级 |
| content | TEXT NOT NULL | 题目内容 |
| answer | TEXT NOT NULL | 参考答案 |

### interview_record（面试记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| interviewee_id | INTEGER NOT NULL | 面试者 ID |
| question_id | INTEGER NOT NULL | 题目 ID |
| score | INTEGER | 评分（0–10） |
| answer_snapshot | TEXT NOT NULL | 答题快照 JSON（含题目内容、备注） |
| month | TEXT NOT NULL | 月份（YYYY-MM） |
| created_at | TEXT NOT NULL | 创建时间 |

### registration_index（报名表索引表，由 Agent 工具创建）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| name | TEXT | 姓名（从文件名提取） |
| student_id | TEXT | 学号（从文件名提取） |
| file_path | TEXT NOT NULL UNIQUE | 文件绝对路径 |
| file_name | TEXT | 文件名 |
| created_at | DATETIME | 录入时间 |

## 安装与运行

### 安装依赖

```bash
pip install PySide6 openpyxl langchain langchain-openai python-dotenv
# 可选（用于 Agent 读取报名表附件）：
pip install pdfplumber python-docx
```

### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 通义千问 API Key（AI 助手功能必须）
DASHSCOPE_API_KEY=your_api_key_here

# SMTP 邮件发送配置（可选，Agent 发送报告时使用）
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_AUID=your_smtp_auth_code
SMTP_FROM=your_email@163.com

# IMAP 邮件收取配置（可选，Agent 下载附件时使用）
IMAP_HOST=imap.163.com
IMAP_PORT=993
IMAP_USER=your_email@163.com
IMAP_PASS=your_imap_auth_code
```

### 运行程序

```bash
python main.py
```

### 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller main.spec
```

生成的可执行文件位于 `dist/` 目录。

## 使用流程

### 第一步：导入题库

在左侧「准备区」→「题库导入」面板中，点击「从 CSV 导入题库」，选择题库文件（支持 `.csv`、`.xlsx`、`.xls`）。

**题库文件格式**（必须包含以下列）：

| 列名 | 说明 |
|------|------|
| type | 题目类型（如：算法、数据结构） |
| difficulty | 难度等级（如：简单、中等、困难） |
| content | 题目内容 |
| answer | 参考答案 |

示例：

```csv
type,difficulty,content,answer
算法,中等,请解释快速排序的基本原理,快速排序采用分治策略...
数据结构,简单,什么是栈？请说明其特点,栈是一种后进先出(LIFO)的数据结构...
```

### 第二步：创建面试者

在「准备区」→「面试者信息」面板中填写姓名（必填）、邮箱、电话，点击「创建面试者」。系统生成面试者 ID，并解锁后续操作。

### 第三步：选择题库

切换至右侧「题库选择」面板，选择题目类型和难度，点击「加载题池」。

### 第四步：开始面试

在「抽题区」点击「下一题」，系统随机抽取一道题目展示。根据面试者表现填写评分（0–10）和备注，再次点击「下一题」自动保存并抽取下一题。

### 第五步：结束面试

完成所有题目后，点击「面试记录」面板中的「结束面试并保存」，所有缓冲记录批量写入数据库。

## 核心机制

### 会话状态机

`InterviewSessionController` 管理面试流程，防止操作顺序错误：

```
INIT → INTERVIEWEE_CREATED → POOL_LOADED → QUESTION_ACTIVE → FINISHED
```

### 确定性随机抽题

基于题型和难度的 SHA256 哈希生成固定随机种子，同一题池每次抽题顺序一致，保证可复现性；题目抽出后从池中移除，避免重复。

### 缓冲批量写入

评分记录先缓存在内存中，点击「结束面试并保存」时一次性批量写入，提高数据库性能。

### 面试者去重

面试者信息通过 SHA256 + SALT 生成哈希，原始信息以 JSON 存储，支持后续扩展字段。

## AI 助手

左侧「AI 助手」标签页提供与 AI Agent 的聊天界面，Agent 基于 LangChain + 通义千问，内置 10 个工具：

| # | 工具名 | 功能 |
|---|--------|------|
| 1 | lookup_interviewees_by_name | 按姓名（模糊）查找面试者 ID |
| 2 | get_question_statistics | 获取题库统计信息 |
| 3 | analyze_interviewees | 分析面试者答题表现（支持批量） |
| 4 | generate_reports | 生成详细面试报告（支持批量） |
| 5 | recommend_questions | 按薄弱项推荐题目（支持批量） |
| 6 | send_report_email | 将报告发送至面试者邮箱 |
| 7 | get_email_attachments | 从邮箱下载附件到本地目录 |
| 8 | write_registration_index | 扫描附件目录，建立报名表索引 |
| 9 | read_registration_doc | 读取报名表内容（含注入安全检测） |
| 10 | read_registration_index | 查询数据库中的报名表索引 |

**示例对话：**

```
你: 分析张三的面试表现
助手: [调用 lookup_interviewees_by_name 查找张三]
      [调用 analyze_interviewees 分析结果]
      张三 (ID:3) 共答题 5 道，均分 7.4，综合评级：良好...

你: 把报告发给他
助手: [调用 generate_reports 生成报告]
      [调用 send_report_email 发送邮件]
      ✅ [张三] 报告已发送至 zhangsan@example.com
```

Agent 支持连续工具调用（最多 10 轮），自动将工具结果反馈给模型直至任务完成。

**安全提示：** `read_registration_doc` 工具内置提示词注入检测，可识别报名表中的恶意内容（角色扮演指令、系统提示覆盖等），并标记风险等级（LOW / MEDIUM / HIGH）。

## 数据分析

「数据分析」标签页中可选择面试者，查看：

- 基本信息（姓名、邮箱、答题总数、平均分等）
- 各题目类型加权得分雷达图（难度系数：简单 0.2、中等 0.5、困难 0.3）

「数据导出」功能可将所有面试记录导出为 Excel 文件，包含面试者信息、题目详情、评分和备注。

## 已知问题

- 大题库导入时 UI 可能短暂卡顿（单线程阻塞）
- 仅在 Windows 环境测试，Linux/Mac 兼容性未验证
- 缺少单元测试覆盖
- Agent 工具调用为同步阻塞，发送时 UI 无响应提示

## 联系方式

如有问题或建议，请提交 Issue。

---

**最后更新**: 2026-02-28