"""
Agent 工具集（LangChain 版本，使用 @tool 装饰器，函数接收普通类型参数）
所有工具均用 @tool 注解定义，并保留 Pydantic 输入模型用于描述和验证
支持：姓名模糊匹配、批量处理、发送邮件
"""
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv  # 新增：加载 .env 文件
load_dotenv()  # 加载项目根目录的 .env 文件

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError


# ─────────────────────────────────────────────
# Pydantic 参数 Schema（用于描述和验证）
# ─────────────────────────────────────────────

class LookupNameInput(BaseModel):
    """姓名查找工具输入参数"""
    name: str = Field(default="", description="面试者姓名，支持模糊匹配；传空字符串可列出所有人")


class AnalyzeInput(BaseModel):
    """面试者分析工具输入参数"""
    interviewee_ids: List[int] = Field(..., description="面试者 ID 列表，可传多个")


class ReportInput(BaseModel):
    """报告生成工具输入参数"""
    interviewee_ids: List[int] = Field(..., description="面试者 ID 列表")


class RecommendInput(BaseModel):
    """题目推荐工具输入参数"""
    interviewee_ids: List[int] = Field(..., description="面试者 ID 列表")
    num_questions: int = Field(default=3, description="每人推荐题目数量", ge=1, le=20)


class EmailRecipient(BaseModel):
    """邮件收件人信息"""
    interviewee_id: int = Field(..., description="面试者 ID（用于查询邮箱）")
    report_content: str = Field(..., description="邮件正文（通常是报告文本）")
    subject: Optional[str] = Field(default="您的面试报告", description="邮件主题")


class SendEmailInput(BaseModel):
    """发送邮件工具输入参数"""
    recipients: List[EmailRecipient] = Field(..., description="收件人列表，支持批量发送")


# ─────────────────────────────────────────────
# 1. 姓名查找工具
# ─────────────────────────────────────────────

def _create_lookup_tool(db):
    """工厂函数：创建姓名查找工具"""

    @tool(args_schema=LookupNameInput)
    def lookup_interviewees_by_name(name: str) -> str:
        """按姓名（支持模糊匹配）查找面试者，返回匹配的 ID 列表及基本信息。当用户提到人名时，必须先调用此工具获取 interviewee_id。"""
        # name 参数已从输入中提取，可能是字符串或空字符串
        name_val = name.strip() if name else ""
        if name_val:
            rows = db.fetchall(
                "SELECT id, name, email, phone FROM interviewee WHERE name LIKE ?",
                (f"%{name_val}%",)
            )
        else:
            rows = db.fetchall("SELECT id, name, email, phone FROM interviewee")

        if not rows:
            return f"未找到姓名包含「{name_val}」的面试者" if name_val else "暂无面试者记录"

        result = f"查找结果（共 {len(rows)} 人）:\n"
        for iid, iname, email, phone in rows:
            result += f"  - ID:{iid}  姓名:{iname}  邮箱:{email or '未填写'}  电话:{phone or '未填写'}\n"
        return result

    return lookup_interviewees_by_name


# ─────────────────────────────────────────────
# 2. 题库统计工具（无参数）
# ─────────────────────────────────────────────

def _create_question_stats_tool(db):
    """工厂函数：创建题库统计工具"""

    @tool
    def get_question_statistics() -> str:
        """获取题库统计信息，包括各类型、各难度的题目数量分布"""
        total = db.fetchall("SELECT COUNT(*) FROM question_bank")[0][0]

        type_stats = db.fetchall("""
            SELECT q_type, COUNT(*) as count
            FROM question_bank
            GROUP BY q_type
            ORDER BY count DESC
        """)
        diff_stats = db.fetchall("""
            SELECT difficulty, COUNT(*) as count
            FROM question_bank
            GROUP BY difficulty
            ORDER BY count DESC
        """)

        result = f"题库统计\n总题数: {total} 道\n\n类型分布:\n"
        for q_type, count in type_stats:
            result += f"  {q_type}: {count} 道\n"
        result += "\n难度分布:\n"
        for difficulty, count in diff_stats:
            result += f"  {difficulty}: {count} 道\n"
        return result

    return get_question_statistics


# ─────────────────────────────────────────────
# 3. 面试者分析工具（支持批量）
# ─────────────────────────────────────────────

def _create_analysis_tool(db):
    """工厂函数：创建面试者分析工具"""

    def _analyze_one(interviewee_id: int) -> str:
        info = db.fetchall(
            "SELECT name, email, created_at FROM interviewee WHERE id=?",
            (interviewee_id,)
        )
        if not info:
            return f"未找到面试者 ID={interviewee_id}"

        name, email, created_at = info[0]
        records = db.fetchall(
            "SELECT score, answer_snapshot FROM interview_record WHERE interviewee_id=?",
            (interviewee_id,)
        )

        if not records:
            return f"[{name}] 尚无答题记录"

        scores = [r[0] for r in records]
        avg_score = round(sum(scores) / len(scores), 2)

        type_scores: Dict[str, List] = {}
        for score, snap_json in records:
            snap = json.loads(snap_json)
            q_type = snap.get("type", "未知")
            type_scores.setdefault(q_type, []).append(score)

        rating = (
            "优秀" if avg_score >= 8 else
            "良好" if avg_score >= 6 else
            "及格" if avg_score >= 4 else "待提高"
        )

        result = (
            f"【{name}】(ID:{interviewee_id})\n"
            f"  邮箱: {email or '未填写'}  注册: {created_at}\n"
            f"  题数: {len(scores)}  总分: {sum(scores)}  均分: {avg_score}  "
            f"最高: {max(scores)}  最低: {min(scores)}\n"
            f"  各类型均分:\n"
        )
        for q_type, sc_list in type_scores.items():
            result += f"    {q_type}: {round(sum(sc_list) / len(sc_list), 2)} 分 ({len(sc_list)} 题)\n"
        result += f"  综合评级: {rating}\n"
        return result

    @tool(args_schema=AnalyzeInput)
    def analyze_interviewees(interviewee_ids: List[int]) -> str:
        """分析一个或多个面试者的答题表现（总分、均分、各类型得分、综合评级）。interviewee_ids 传入 ID 数组，支持批量分析。"""
        results = [_analyze_one(iid) for iid in interviewee_ids]
        return "\n\n" + ("=" * 60 + "\n").join(results)

    return analyze_interviewees


# ─────────────────────────────────────────────
# 4. 报告生成工具（支持批量）
# ─────────────────────────────────────────────

def _create_report_tool(db):
    """工厂函数：创建报告生成工具"""

    def _generate_one(interviewee_id: int) -> str:
        info = db.fetchall(
            "SELECT name, email, phone FROM interviewee WHERE id=?",
            (interviewee_id,)
        )
        if not info:
            return f"未找到面试者 ID={interviewee_id}"

        name, email, phone = info[0]
        records = db.fetchall("""
            SELECT question_id, score, answer_snapshot, created_at
            FROM interview_record
            WHERE interviewee_id = ?
            ORDER BY created_at
        """, (interviewee_id,))

        if not records:
            return f"[{name}] 无答题记录，无法生成报告"

        sep = "=" * 60
        report = f"{sep}\n{'面试报告':^56}\n{sep}\n"
        report += f"姓名: {name}  邮箱: {email or '未填写'}  电话: {phone or '未填写'}\n\n"
        report += "答题明细\n" + "-" * 60 + "\n"

        for idx, (q_id, score, snap_json, ans_time) in enumerate(records, 1):
            snap = json.loads(snap_json)
            report += (
                f"\n题目 {idx}  类型:{snap.get('type', '未知')}  "
                f"难度:{snap.get('difficulty', '未知')}  得分:{score}\n"
                f"  内容: {snap.get('content', '')[:60]}...\n"
                f"  时间: {ans_time}\n"
            )
            if snap.get("remark"):
                report += f"  备注: {snap['remark']}\n"

        scores = [r[1] for r in records]
        report += (
            f"\n{sep}\n统计分析\n"
            f"  题数:{len(scores)}  总分:{sum(scores)}  "
            f"均分:{round(sum(scores) / len(scores), 2)}  "
            f"最高:{max(scores)}  最低:{min(scores)}\n{sep}\n"
        )
        return report

    @tool(args_schema=ReportInput)
    def generate_reports(interviewee_ids: List[int]) -> str:
        """为一个或多个面试者生成详细面试报告（答题明细 + 统计分析）。返回报告文本，可配合 send_report_email 工具发送给面试者。"""
        reports = [_generate_one(iid) for iid in interviewee_ids]
        return "\n\n".join(reports)

    return generate_reports


# ─────────────────────────────────────────────
# 5. 题目推荐工具（支持批量）
# ─────────────────────────────────────────────

def _create_recommend_tool(db):
    """工厂函数：创建题目推荐工具"""

    def _recommend_one(interviewee_id: int, num_questions: int) -> str:
        info = db.fetchall(
            "SELECT name FROM interviewee WHERE id=?", (interviewee_id,)
        )
        if not info:
            return f"未找到面试者 ID={interviewee_id}"

        name = info[0][0]
        records = db.fetchall(
            "SELECT score, answer_snapshot FROM interview_record WHERE interviewee_id=?",
            (interviewee_id,)
        )

        if records:
            type_scores: Dict[str, List] = {}
            for score, snap_json in records:
                snap = json.loads(snap_json)
                q_type = snap.get("type", "未知")
                type_scores.setdefault(q_type, []).append(score)

            type_avg = {t: sum(sc) / len(sc) for t, sc in type_scores.items()}
            weak_type = min(type_avg, key=type_avg.get)
            weak_avg = type_avg[weak_type]

            recs = db.fetchall(
                "SELECT id, q_type, difficulty, content FROM question_bank WHERE q_type=? LIMIT ?",
                (weak_type, num_questions)
            )
            header = f"[{name}] 薄弱项「{weak_type}」(均分 {weak_avg:.2f})，推荐练习:\n"
        else:
            recs = db.fetchall(
                "SELECT id, q_type, difficulty, content FROM question_bank ORDER BY RANDOM() LIMIT ?",
                (num_questions,)
            )
            header = f"[{name}] 首次面试，随机推荐 {num_questions} 题:\n"

        if not recs:
            return f"[{name}] 题库暂无可推荐题目"

        result = header + "-" * 40 + "\n"
        for idx, (q_id, q_type, diff, content) in enumerate(recs, 1):
            result += f"  {idx}. [ID:{q_id}] {q_type} / {diff}\n     {content[:80]}...\n"
        return result

    @tool(args_schema=RecommendInput)
    def recommend_questions(interviewee_ids: List[int], num_questions: int = 3) -> str:
        """根据面试者历史表现，推荐合适题目（针对薄弱类型）。支持批量推荐。"""
        results = [_recommend_one(iid, num_questions) for iid in interviewee_ids]
        return "\n\n".join(results)

    return recommend_questions


# ─────────────────────────────────────────────
# 6. 发送邮件工具
# ─────────────────────────────────────────────

def _create_email_tool(db):
    """工厂函数：创建邮件发送工具"""

    # SMTP 配置（从环境变量读取）
    smtp_config = {
        "host": os.getenv("SMTP_HOST", "smtp.163.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_AUID", ""),
        "from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))
    }

    def _send_one(iid: int, subject: str, content: str) -> str:
        info = db.fetchall(
            "SELECT name, email FROM interviewee WHERE id=?", (iid,)
        )
        if not info:
            return f"❌ ID={iid} 未找到面试者"

        name, email = info[0]
        if not email:
            return f"❌ [{name}] 邮箱未填写，跳过发送"

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_config["from"]
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(content, "plain", "utf-8"))

            with smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"], timeout=15) as server:
                if smtp_config["user"]:
                    server.login(smtp_config["user"], smtp_config["pass"])
                server.sendmail(smtp_config["from"], email, msg.as_string())

            return f"✅ [{name}] 报告已发送至 {email}"
        except Exception as e:
            return f"❌ [{name}]({email}) 发送失败: {str(e)}"

    @tool(args_schema=SendEmailInput)
    def send_report_email(recipients: Union[List[Dict], List[EmailRecipient]]) -> str:
        """将面试报告通过邮件发送给指定面试者。recipients 为列表，每项包含 interviewee_id（用于获取邮箱）和 report_content（邮件正文）。支持批量发送。"""
        results = []
        for item in recipients:
            # 支持字典或 EmailRecipient 对象
            if isinstance(item, dict):
                try:
                    recipient = EmailRecipient.model_validate(item)
                except ValidationError as e:
                    results.append(f"❌ 收件人数据格式错误: {e}")
                    continue
            elif isinstance(item, EmailRecipient):
                recipient = item
            else:
                results.append(f"❌ 不支持的收件人类型: {type(item)}")
                continue

            results.append(_send_one(recipient.interviewee_id, recipient.subject, recipient.report_content))
        return "\n".join(results)

    return send_report_email


# ─────────────────────────────────────────────
# 工具注册入口
# ─────────────────────────────────────────────

def get_default_tools(db) -> List[tool]:
    """
    获取所有默认工具的 LangChain Tool 列表（使用 @tool 装饰器创建）

    用法：
        tools = get_default_tools(db)
        agent.register_tools(tools)
    """
    return [
        _create_lookup_tool(db),
        _create_question_stats_tool(db),
        _create_analysis_tool(db),
        _create_report_tool(db),
        _create_recommend_tool(db),
        _create_email_tool(db),
    ]


def register_default_tools(agent, db):
    """
    向后兼容函数：直接注册到 Agent 实例
    （内部调用 get_default_tools + agent.register_tools）
    """
    tools = get_default_tools(db)
    agent.register_tools(tools)
    print(f"[AgentTools] 已注册 {len(tools)} 个 LangChain 工具")