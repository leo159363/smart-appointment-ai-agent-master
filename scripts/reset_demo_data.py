"""Reset local demo data for the tutoring training scenario.

This script is intended for local development only. It keeps the existing
SQLite schema unchanged, backs up the database file, clears demo rows, and
loads tutoring-oriented knowledge and teacher examples.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "smart_appointment.db"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.text_embedding import embed_input  # noqa: E402


KNOWLEDGE_ITEMS = [
    {
        "content": "我们的咨询时间为每天 9:00-22:00，正式上课时间可根据学生和老师时间灵活排课。工作日晚上、周末白天、寒暑假时段都可以预约课程顾问沟通。",
        "category": "咨询/上课时间",
        "keywords": ["咨询时间", "上课时间", "排课", "周末", "寒暑假"],
    },
    {
        "content": "我们提供小学、初中、高中数学、英语、语文作文、物理、化学等一对一课程，也支持基础补弱、考前短期提分、作文专项、英语听说和学习习惯督促。",
        "category": "课程体系",
        "keywords": ["课程体系", "一对一", "数学", "英语", "语文作文", "物理", "化学", "基础补弱"],
    },
    {
        "content": "老师均具备学科教学经验，可根据学生基础、目标分数和学习习惯匹配授课风格。常见风格包括耐心细致型、应试提分型、互动鼓励型、严格督促型、基础补弱型和拔高竞赛型。",
        "category": "老师介绍",
        "keywords": ["老师介绍", "教学经验", "教学风格", "耐心细致", "应试提分", "基础补弱", "拔高竞赛"],
    },
    {
        "content": "支持线下校区上课和线上直播课，具体方式可在试听课前确认。线下课程会根据校区距离和老师课表安排，上门授课需单独确认覆盖范围和时间。",
        "category": "校区/线上课",
        "keywords": ["校区", "线上课", "直播课", "线下课", "上门授课", "上课地点"],
    },
    {
        "content": "试听课后会根据学生表现生成学习建议，并推荐正式课排课方案。正式课程会围绕学生薄弱点、目标分数、阶段测评和错题复盘持续调整。",
        "category": "课程介绍",
        "keywords": ["试听课", "正式课", "学习建议", "薄弱点", "目标分数", "错题复盘"],
    },
    {
        "content": "教学质量通过课堂反馈、阶段测评、错题复盘和家长回访进行跟踪。课程顾问会结合老师反馈和学生作业情况，建议是否调整频次、老师或学习计划。",
        "category": "教学质量",
        "keywords": ["教学质量", "课堂反馈", "阶段测评", "错题复盘", "家长回访", "学习计划"],
    },
    {
        "content": "试听课可提前预约；正式课程需要确认学生时间、老师时间和课程包。改约、请假和补课通常需要提前联系课程顾问，排课时会避免与老师已有课表冲突。",
        "category": "试听/排课规则",
        "keywords": ["试听课", "正式排课", "改约", "请假", "补课", "排课冲突", "课程顾问"],
    },
    {
        "content": "支持单次试听、10课时包、20课时包等方案，具体收费以课程类型和年级为准。退费需要核对剩余课时、已上课时、赠送课时、课程有效期和合同约定。",
        "category": "课时包/课程包",
        "keywords": ["课时包", "课程包", "收费", "价格", "退费", "剩余课时", "合同"],
    },
]

TEACHERS = [
    {
        "name": "张伟",
        "gender": "男",
        "strength": "初中数学老师，8年教龄，耐心细致型，擅长基础巩固、几何压轴题拆解和错题复盘，讲解清晰，适合基础中等或基础薄弱的学生",
    },
    {
        "name": "王强",
        "gender": "男",
        "strength": "高中物理老师，10年教龄，应试提分型，擅长力学、电学模型归纳和高频题型训练，适合高中阶段冲刺提分的学生",
    },
    {
        "name": "李娜",
        "gender": "女",
        "strength": "英语老师，6年教龄，耐心细致型，擅长语法、阅读理解、写作提升和初中英语听说训练，适合英语基础不稳、开口不自信的学生",
    },
    {
        "name": "赵敏",
        "gender": "女",
        "strength": "语文作文老师，9年教龄，互动鼓励型，擅长素材积累、结构训练、阅读理解和表达优化，适合作文不会写、语言组织弱的学生",
    },
    {
        "name": "刘洋",
        "gender": "男",
        "strength": "小学数学老师，5年教龄，互动鼓励型，擅长学习习惯培养、计算能力训练和数学兴趣启发，适合低年级注意力不稳定的学生",
    },
    {
        "name": "孙丽",
        "gender": "女",
        "strength": "英语口语/听力老师，7年教龄，互动鼓励型，擅长线上陪练、听力精听、口语表达和长期提升，适合英语听说困难的学生",
    },
    {
        "name": "周杰",
        "gender": "男",
        "strength": "初中化学老师，6年教龄，基础补弱型，擅长概念梳理、实验题分析和中考化学题型训练，适合化学刚入门或概念混淆的学生",
    },
    {
        "name": "吴婷",
        "gender": "女",
        "strength": "学习规划老师，8年教龄，严格督促与耐心沟通结合，擅长阶段测评、错题复盘、时间管理和学习计划制定",
    },
    {
        "name": "郑斌",
        "gender": "男",
        "strength": "高三数学老师，12年教龄，应试提分型，擅长短期提分、函数导数、数列和高频题型训练，适合高三冲刺和考前查漏补缺",
    },
    {
        "name": "何静",
        "gender": "女",
        "strength": "班主任/教务老师，6年教龄，擅长课后跟进、家长沟通、排课协调和阶段反馈，适合需要持续督促和课程协调的学生",
    },
]


def build_embeddings() -> list[list[float]]:
    embeddings = []
    for item in KNOWLEDGE_ITEMS:
        text = f"{item['content']} {' '.join(item['keywords'])}"
        embeddings.append(embed_input(text))
    return embeddings


def reset_sqlite_data(embeddings: list[list[float]]) -> Path:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"{DB_PATH.name}.bak_{timestamp}")
    shutil.copy2(DB_PATH, backup_path)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            for table in [
                "user_recommendations",
                "user_preferences",
                "user_behaviors",
                "technician_schedules",
                "knowledge_documents",
                "technicians",
            ]:
                conn.execute(f"DELETE FROM {table}")

            has_sequence = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            ).fetchone()
            if has_sequence:
                conn.execute(
                    "DELETE FROM sqlite_sequence WHERE name IN (?, ?, ?, ?, ?, ?)",
                    (
                        "user_recommendations",
                        "user_preferences",
                        "user_behaviors",
                        "technician_schedules",
                        "knowledge_documents",
                        "technicians",
                    ),
                )

            for item, embedding in zip(KNOWLEDGE_ITEMS, embeddings):
                conn.execute(
                    """
                    INSERT INTO knowledge_documents
                        (content, category, keywords, embedding, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        item["content"],
                        item["category"],
                        json.dumps(item["keywords"], ensure_ascii=False),
                        json.dumps(embedding),
                        now,
                        now,
                    ),
                )

            for teacher in TEACHERS:
                conn.execute(
                    "INSERT INTO technicians (name, gender, strength) VALUES (?, ?, ?)",
                    (teacher["name"], teacher["gender"], teacher["strength"]),
                )
    finally:
        conn.close()

    return backup_path


def main() -> None:
    embeddings = build_embeddings()
    backup_path = reset_sqlite_data(embeddings)
    print(f"backup={backup_path.name}")
    print(f"knowledge_count={len(KNOWLEDGE_ITEMS)}")
    print(f"teacher_count={len(TEACHERS)}")


if __name__ == "__main__":
    main()
