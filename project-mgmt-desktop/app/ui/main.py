"""Streamlit UI for the project management desktop application."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from app.database import init_db, seed_demo_data
from app.services import alerts, finance, progress, reports


def _project_selector() -> int | None:
    projects = progress.list_projects()
    if not projects:
        st.info("暂无项目，请先在侧边栏新建项目。")
        return None
    labels = {
        p["id"]: f"{p['name']}（{p['planned_start']} ~ {p['planned_end']}）"
        for p in projects
    }
    selected = st.selectbox(
        "选择项目",
        options=list(labels.keys()),
        format_func=lambda pid: labels[pid],
    )
    return int(selected)


def _sidebar_new_project() -> None:
    st.sidebar.header("新建项目")
    with st.sidebar.form("new_project"):
        name = st.text_input("项目名称", value="新建工程项目")
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("计划开始", value=date.today())
        with col2:
            end = st.date_input("计划结束", value=date(2026, 12, 31))
        budget = st.number_input(
            "总预算（元）", min_value=0.0, value=100000.0, step=1000.0
        )
        submitted = st.form_submit_button("创建项目")
        if submitted and name.strip():
            pid = progress.add_project(
                name.strip(),
                start.isoformat(),
                end.isoformat(),
                budget,
            )
            alerts.upsert_rule(pid, "progress_behind", 15)
            alerts.upsert_rule(pid, "budget_overrun", 10)
            st.sidebar.success(f"已创建项目：{name}")
            st.rerun()


def _tab_dashboard(project_id: int) -> None:
    project = progress.get_project(project_id)
    assert project is not None
    actual = progress.weighted_progress(project_id)
    expected = progress.schedule_progress(project)
    spent = finance.total_spent(project_id)
    budget = float(project["budget"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("加权进度", f"{actual:.1f}%")
    c2.metric("计划进度", f"{expected:.1f}%", delta=f"{actual - expected:.1f}%")
    c3.metric("累计支出", f"{spent:,.0f} 元")
    c4.metric("预算余额", f"{budget - spent:,.0f} 元")

    st.subheader("实时预警")
    active_alerts = alerts.evaluate_alerts(project_id)
    if active_alerts:
        for alert in active_alerts:
            if alert["level"] == "critical":
                st.error(f"**{alert['type']}** — {alert['message']}")
            else:
                st.warning(f"**{alert['type']}** — {alert['message']}")
    else:
        st.success("当前无预警，项目运行正常。")


def _tab_progress(project_id: int) -> None:
    st.subheader("工程进度管控")
    tasks = progress.list_tasks(project_id)
    if tasks:
        df = pd.DataFrame(tasks)[
            ["id", "name", "weight", "progress", "planned_end"]
        ]
        df.columns = ["ID", "任务", "权重", "完成度%", "计划完成日"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.form("add_task"):
        st.markdown("**添加任务**")
        name = st.text_input("任务名称")
        weight = st.number_input("权重", min_value=1.0, value=10.0)
        prog = st.slider("初始完成度", 0.0, 100.0, 0.0)
        planned_end = st.date_input("计划完成日", value=date.today())
        if st.form_submit_button("添加") and name.strip():
            progress.add_task(
                project_id,
                name.strip(),
                weight,
                prog,
                planned_end.isoformat(),
            )
            st.rerun()

    st.markdown("**更新任务进度**")
    if tasks:
        task_map = {t["id"]: t["name"] for t in tasks}
        task_id = st.selectbox(
            "选择任务",
            options=list(task_map.keys()),
            format_func=lambda tid: task_map[tid],
            key="progress_task_select",
        )
        new_prog = st.slider(
            "新完成度",
            0.0,
            100.0,
            float(next(t["progress"] for t in tasks if t["id"] == task_id)),
            key="progress_slider",
        )
        if st.button("保存进度"):
            progress.update_task_progress(int(task_id), new_prog)
            st.rerun()


def _tab_finance(project_id: int) -> None:
    st.subheader("财务数据匹配")
    match_rows = finance.match_summary(project_id)
    if match_rows:
        df = pd.DataFrame(match_rows)
        df.columns = ["科目", "预算", "实际", "差异", "匹配率%"]
        st.dataframe(
            df.style.format(
                {
                    "预算": "{:,.0f}",
                    "实际": "{:,.0f}",
                    "差异": "{:+,.0f}",
                    "匹配率%": "{:.1f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    col_a, col_b = st.columns(2)
    with col_a:
        with st.form("add_budget"):
            st.markdown("**添加预算科目**")
            category = st.text_input("科目名称")
            amount = st.number_input("预算金额", min_value=0.0, step=1000.0)
            if st.form_submit_button("添加科目") and category.strip():
                finance.add_budget_item(project_id, category.strip(), amount)
                st.rerun()

    budget_items = finance.list_budget_items(project_id)
    item_options = {None: "（不匹配科目）"}
    item_options.update({b["id"]: b["category"] for b in budget_items})

    with col_b:
        with st.form("add_expense"):
            st.markdown("**登记支出**")
            desc = st.text_input("摘要")
            amount = st.number_input("金额", min_value=0.0, step=100.0, key="exp_amt")
            exp_date = st.date_input("支出日期", value=date.today())
            item_id = st.selectbox(
                "匹配预算科目",
                options=list(item_options.keys()),
                format_func=lambda k: item_options[k],
            )
            vendor = st.text_input("供应商/对方")
            if st.form_submit_button("登记支出") and desc.strip():
                finance.add_expense(
                    project_id,
                    desc.strip(),
                    amount,
                    exp_date.isoformat(),
                    item_id,
                    vendor or None,
                )
                st.rerun()

    st.markdown("**支出明细**")
    expenses = finance.list_expenses(project_id)
    if expenses:
        exp_df = pd.DataFrame(expenses)[
            ["expense_date", "description", "amount", "budget_category", "vendor"]
        ]
        exp_df.columns = ["日期", "摘要", "金额", "匹配科目", "供应商"]
        st.dataframe(exp_df, use_container_width=True, hide_index=True)


def _tab_alerts(project_id: int) -> None:
    st.subheader("预警规则配置")
    rules = alerts.list_rules(project_id)
    progress_threshold = 15.0
    budget_threshold = 10.0
    for rule in rules:
        if rule["rule_type"] == "progress_behind":
            progress_threshold = float(rule["threshold"])
        elif rule["rule_type"] == "budget_overrun":
            budget_threshold = float(rule["threshold"])

    with st.form("alert_rules"):
        p_th = st.number_input(
            "进度落后阈值（百分点）",
            min_value=1.0,
            max_value=50.0,
            value=progress_threshold,
            help="实际进度低于计划进度超过该值时触发进度预警",
        )
        b_th = st.number_input(
            "预算超支节奏阈值（百分点）",
            min_value=1.0,
            max_value=50.0,
            value=budget_threshold,
            help="支出占预算比例高于计划消耗节奏超过该值时触发预算预警",
        )
        if st.form_submit_button("保存规则"):
            alerts.upsert_rule(project_id, "progress_behind", p_th)
            alerts.upsert_rule(project_id, "budget_overrun", b_th)
            st.success("预警规则已更新")
            st.rerun()

    st.subheader("当前预警列表")
    active = alerts.evaluate_alerts(project_id)
    if active:
        for alert in active:
            icon = "🔴" if alert["level"] == "critical" else "🟡"
            st.write(f"{icon} **{alert['type']}**: {alert['message']}")
    else:
        st.success("无活跃预警")


def _tab_reports(project_id: int) -> None:
    st.subheader("月度报表")
    today = date.today()
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("年份", min_value=2020, max_value=2100, value=today.year)
    with col2:
        month = st.number_input("月份", min_value=1, max_value=12, value=today.month)

    report = reports.monthly_report(project_id, int(year), int(month))
    text = reports.format_report_text(report)
    st.text_area("报表预览", text, height=420)

    st.download_button(
        "下载月度报表 (.txt)",
        data=text,
        file_name=f"monthly_report_{year}_{month:02d}.txt",
        mime="text/plain",
    )


def run_app() -> None:
    st.set_page_config(
        page_title="工程财务管控系统",
        page_icon="📊",
        layout="wide",
    )
    init_db()
    seed_demo_data()

    st.title("工程财务管控系统")
    st.caption("工程进度管控 · 财务数据匹配 · 进度/预算预警 · 月度报表")

    _sidebar_new_project()
    project_id = _project_selector()
    if project_id is None:
        return

    tabs = st.tabs(["总览", "进度管控", "财务匹配", "预警中心", "月度报表"])
    with tabs[0]:
        _tab_dashboard(project_id)
    with tabs[1]:
        _tab_progress(project_id)
    with tabs[2]:
        _tab_finance(project_id)
    with tabs[3]:
        _tab_alerts(project_id)
    with tabs[4]:
        _tab_reports(project_id)
