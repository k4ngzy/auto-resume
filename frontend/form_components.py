# frontend/form_components.py
"""
通用表单组件
基于 module_config.py 的配置渲染表单
"""

import streamlit as st
from typing import Dict, Any, List
from module_config import RESUME_MODULES, ModuleConfig


def render_checkbox_section(resume_data: Dict[str, Any]) -> Dict[str, bool]:
    """渲染模块选择复选框"""
    st.markdown("### ⚙️ 选择要包含的简历部分")
    col1, col2, col3 = st.columns(3)

    include_flags = {}

    # 定义复选框的分组
    checkbox_groups = [
        ["personalSummary", "education", "workExperience"],
        ["skills", "internshipExperience"],
        ["projects", "awards"]
    ]

    cols = [col1, col2, col3]

    for col_idx, group in enumerate(checkbox_groups):
        with cols[col_idx]:
            for module_key in group:
                config = RESUME_MODULES.get(module_key)
                if not config:
                    continue

                # 判断是否有数据
                data = resume_data.get(module_key)
                if config.module_type in ["structured_list", "list"]:
                    has_data = len(data) > 0 if isinstance(data, list) else False
                elif config.module_type in ["text", "textarea"]:
                    has_data = bool(data.strip()) if isinstance(data, str) else False
                else:
                    has_data = False

                include_flags[module_key] = st.checkbox(
                    f"{config.icon} {config.title}",
                    value=has_data,
                    key=f"include_{module_key}"
                )

    return include_flags


def render_basic_info_form(resume_data: Dict[str, Any]):
    """渲染基本信息表单"""
    st.markdown("### 📋 基本信息")

    basic_info = resume_data.get("basicInfo", {})

    col1, col2 = st.columns(2)
    with col1:
        basic_info["name"] = st.text_input("姓名", value=basic_info.get("name", ""), key="basic_name")
        basic_info["gender"] = st.text_input("性别", value=basic_info.get("gender", ""), key="basic_gender")
        basic_info["phone"] = st.text_input("电话", value=basic_info.get("phone", ""), key="basic_phone")
        basic_info["hometown"] = st.text_input("籍贯", value=basic_info.get("hometown", ""), key="basic_hometown")

    with col2:
        basic_info["position"] = st.text_input("求职意向", value=basic_info.get("position", ""), key="basic_position")
        basic_info["age"] = st.text_input("年龄", value=basic_info.get("age", ""), key="basic_age")
        basic_info["email"] = st.text_input("邮箱", value=basic_info.get("email", ""), key="basic_email")

    resume_data["basicInfo"] = basic_info


def render_textarea_field(resume_data: Dict[str, Any], module_key: str, config: ModuleConfig):
    """渲染文本域类型字段"""
    st.markdown(f"### {config.icon} {config.title}")

    current_value = resume_data.get(module_key, "")
    resume_data[module_key] = st.text_area(
        f"{config.title}内容",
        value=current_value,
        height=150,
        key=f"form_{module_key}"
    )


def render_list_field(resume_data: Dict[str, Any], module_key: str, config: ModuleConfig):
    """渲染简单列表类型字段（如荣誉证书）"""
    st.markdown(f"### {config.icon} {config.title}")

    items = resume_data.get(module_key, [])
    if not isinstance(items, list):
        items = []
        resume_data[module_key] = items

    # 显示现有项目
    for idx, item in enumerate(items):
        col1, col2 = st.columns([5, 1])
        with col1:
            items[idx] = st.text_input(
                f"{config.title} {idx + 1}",
                value=item,
                key=f"{module_key}_{idx}"
            )
        with col2:
            if st.button("删除", key=f"del_{module_key}_{idx}"):
                items.pop(idx)
                st.rerun()

    # 添加新项目
    if st.button(f"➕ 添加{config.title}", key=f"add_{module_key}"):
        items.append("")
        st.rerun()


def render_structured_list_field(resume_data: Dict[str, Any], module_key: str, config: ModuleConfig):
    """渲染结构化列表类型字段（如教育背景、工作经历等）"""
    st.markdown(f"### {config.icon} {config.title}")

    items = resume_data.get(module_key, [])
    if not isinstance(items, list):
        items = []
        resume_data[module_key] = items

    # 显示现有项目
    for idx, item in enumerate(items):
        with st.expander(f"{config.title} {idx + 1}", expanded=True):
            render_structured_item_fields(item, config.fields, module_key, idx)

            if st.button("🗑️ 删除此项", key=f"del_{module_key}_{idx}"):
                items.pop(idx)
                st.rerun()

    # 添加新项目
    if st.button(f"➕ 添加{config.title}", key=f"add_{module_key}"):
        # 创建空项目
        new_item = {}
        for field in config.fields:
            if field.get("is_list"):
                new_item[field["name"]] = []
            else:
                new_item[field["name"]] = ""
        items.append(new_item)
        st.rerun()


def render_structured_item_fields(item: Dict[str, Any], fields: List[Dict[str, Any]], module_key: str, idx: int):
    """渲染结构化项目的字段"""
    # 按列分组字段
    col_fields = {1: [], 2: [], None: []}
    for field in fields:
        col_fields[field.get("col")].append(field)

    # 渲染第一列和第二列
    if col_fields[1] or col_fields[2]:
        col1, col2 = st.columns(2)

        with col1:
            for field in col_fields[1]:
                render_single_field(item, field, module_key, idx)

        with col2:
            for field in col_fields[2]:
                render_single_field(item, field, module_key, idx)

    # 渲染全宽字段
    for field in col_fields[None]:
        render_single_field(item, field, module_key, idx)


def render_single_field(item: Dict[str, Any], field: Dict[str, Any], module_key: str, idx: int):
    """渲染单个字段"""
    field_name = field["name"]
    field_label = field["label"]
    field_type = field["type"]
    is_list = field.get("is_list", False)

    key = f"{module_key}_{idx}_{field_name}"

    if field_type == "text":
        item[field_name] = st.text_input(
            field_label,
            value=item.get(field_name, ""),
            key=key
        )
    elif field_type == "textarea":
        if is_list:
            # 列表类型的文本域（如工作内容）
            current_list = item.get(field_name, [])
            if isinstance(current_list, list):
                text_value = "\n".join(current_list)
            else:
                text_value = current_list

            new_text = st.text_area(
                field_label,
                value=text_value,
                height=150,
                key=key
            )
            # 转换回列表
            item[field_name] = [line.strip() for line in new_text.split("\n") if line.strip()]
        else:
            item[field_name] = st.text_area(
                field_label,
                value=item.get(field_name, ""),
                height=100,
                key=key
            )


def render_module_form(resume_data: Dict[str, Any], module_key: str, include_flags: Dict[str, bool]):
    """根据模块类型渲染对应的表单"""
    # 检查是否包含此模块
    if not include_flags.get(module_key, False):
        return

    config = RESUME_MODULES.get(module_key)
    if not config:
        return

    if config.module_type == "textarea":
        render_textarea_field(resume_data, module_key, config)
    elif config.module_type == "list":
        render_list_field(resume_data, module_key, config)
    elif config.module_type == "structured_list":
        render_structured_list_field(resume_data, module_key, config)


def render_all_module_forms(resume_data: Dict[str, Any], include_flags: Dict[str, bool]):
    """渲染所有模块表单"""
    # 按照默认顺序渲染
    module_order = [
        "personalSummary",
        "education",
        "skills",
        "workExperience",
        "internshipExperience",
        "projects",
        "awards"
    ]

    for module_key in module_order:
        render_module_form(resume_data, module_key, include_flags)


def render_form_with_count(resume_data: Dict[str, Any], include_flags: Dict[str, bool], count_values: Dict[str, int]) -> Dict[str, Any]:
    """
    渲染带数量控制的表单
    返回收集到的表单数据
    """
    result = {}

    # 1. 自我评价
    if include_flags.get("personalSummary", False):
        with st.expander("🔍 自我评价", expanded=True):
            result["personalSummary"] = st.text_area(
                "请简要描述您的专业背景、核心技能和求职意向",
                value=resume_data.get("personalSummary", ""),
                height=100,
                key="form_personalSummary"
            )
    else:
        result["personalSummary"] = ""

    # 2. 教育背景
    education = []
    if include_flags.get("education", False) and count_values.get("education", 0) > 0:
        with st.expander("🎓 教育背景", expanded=True):
            for i in range(count_values["education"]):
                existing_edu = resume_data.get("education", [])[i] if i < len(resume_data.get("education", [])) else {}
                with st.expander(f"教育经历 {i + 1}", expanded=(i == 0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        school = st.text_input(f"学校 {i + 1}", value=existing_edu.get("school", ""), key=f"school_{i}")
                        major = st.text_input(f"专业 {i + 1}", value=existing_edu.get("major", ""), key=f"major_{i}")
                        degree = st.text_input(f"学位 {i + 1}", value=existing_edu.get("degree", ""), key=f"degree_{i}")
                    with col2:
                        edu_date = st.text_input(f"时间 {i + 1}", value=existing_edu.get("date", ""), key=f"edu_date_{i}")
                        gpa = st.text_input(f"GPA {i + 1}", value=existing_edu.get("gpa", ""), key=f"gpa_{i}")
                    courses = st.text_input(f"相关课程 {i + 1}", value=existing_edu.get("courses", ""), key=f"courses_{i}")
                    education.append({
                        "school": school,
                        "major": major,
                        "degree": degree,
                        "date": edu_date,
                        "gpa": gpa,
                        "courses": courses,
                    })
    result["education"] = education

    # 3. 技术能力
    if include_flags.get("skills", False):
        with st.expander("💻 技术能力", expanded=True):
            result["skills"] = st.text_area(
                "请填写您的技术能力（可以自由组织格式）",
                value=resume_data.get("skills", ""),
                height=150,
                placeholder="例如：\nPython, Java, C++\nDjango, Flask, Spring Boot\nMySQL, Redis, Docker",
                key="form_skills"
            )
    else:
        result["skills"] = ""

    # 4. 工作经历
    work_experience = []
    if include_flags.get("workExperience", False) and count_values.get("workExperience", 0) > 0:
        with st.expander("💼 工作经历", expanded=True):
            for i in range(count_values["workExperience"]):
                existing_work = resume_data.get("workExperience", [])[i] if i < len(resume_data.get("workExperience", [])) else {}
                with st.expander(f"工作经历 {i + 1}", expanded=(i == 0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        company = st.text_input(f"公司/机构 {i + 1}", value=existing_work.get("company", ""), key=f"company_{i}")
                        job_title = st.text_input(f"职位 {i + 1}", value=existing_work.get("position", ""), key=f"job_title_{i}")
                    with col2:
                        work_date = st.text_input(f"工作时间 {i + 1}", value=existing_work.get("date", ""), key=f"work_date_{i}")

                    work_points_text = "\n".join(existing_work.get("points", []))
                    work_points = st.text_area(
                        f"工作内容 {i + 1} (每条用换行分隔)",
                        value=work_points_text,
                        height=120,
                        key=f"work_points_{i}",
                    )
                    work_experience.append({
                        "company": company,
                        "position": job_title,
                        "date": work_date,
                        "points": [p.strip() for p in work_points.split("\n") if p.strip()],
                    })
    result["workExperience"] = work_experience

    # 5. 实习经历
    internship_experience = []
    if include_flags.get("internshipExperience", False) and count_values.get("internshipExperience", 0) > 0:
        with st.expander("🎓 实习经历", expanded=True):
            for i in range(count_values["internshipExperience"]):
                existing_internship = resume_data.get("internshipExperience", [])[i] if i < len(resume_data.get("internshipExperience", [])) else {}
                with st.expander(f"实习经历 {i + 1}", expanded=(i == 0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        intern_company = st.text_input(f"实习公司 {i + 1}", value=existing_internship.get("company", ""), key=f"intern_company_{i}")
                        intern_position = st.text_input(f"实习职位 {i + 1}", value=existing_internship.get("position", ""), key=f"intern_position_{i}")
                    with col2:
                        intern_date = st.text_input(f"实习时间 {i + 1}", value=existing_internship.get("date", ""), key=f"intern_date_{i}")

                    intern_points_text = "\n".join(existing_internship.get("points", []))
                    intern_points = st.text_area(
                        f"实习内容 {i + 1} (每条用换行分隔)",
                        value=intern_points_text,
                        height=120,
                        key=f"intern_points_{i}",
                    )
                    internship_experience.append({
                        "company": intern_company,
                        "position": intern_position,
                        "date": intern_date,
                        "points": [p.strip() for p in intern_points.split("\n") if p.strip()],
                    })
    result["internshipExperience"] = internship_experience

    # 6. 项目经历
    projects = []
    if include_flags.get("projects", False) and count_values.get("projects", 0) > 0:
        with st.expander("🚀 项目经历", expanded=True):
            for i in range(count_values["projects"]):
                existing_proj = resume_data.get("projects", [])[i] if i < len(resume_data.get("projects", [])) else {}
                with st.expander(f"项目经历 {i + 1}", expanded=(i == 0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        project_name = st.text_input(f"项目名称 {i + 1}", value=existing_proj.get("name", ""), key=f"project_name_{i}")
                    with col2:
                        project_date = st.text_input(f"项目时间 {i + 1}", value=existing_proj.get("date", ""), key=f"project_date_{i}")
                    role = st.text_input(f"项目角色 {i + 1}", value=existing_proj.get("role", ""), key=f"role_{i}")

                    project_desc_text = "\n".join(existing_proj.get("description", []))
                    project_desc = st.text_area(
                        f"项目描述 {i + 1} (每条用换行分隔)",
                        value=project_desc_text,
                        height=120,
                        key=f"project_desc_{i}",
                    )
                    projects.append({
                        "name": project_name,
                        "date": project_date,
                        "role": role,
                        "description": [d.strip() for d in project_desc.split("\n") if d.strip()],
                    })
    result["projects"] = projects

    # 7. 荣誉证书
    if include_flags.get("awards", False):
        with st.expander("🏆 荣誉证书", expanded=True):
            awards_text = "\n".join(resume_data.get("awards", []))
            awards = st.text_area(
                "请列出您的主要获奖和发表论文情况 (每条用换行分隔)",
                value=awards_text,
                height=100,
                key="form_awards"
            )
            result["awards"] = [a.strip() for a in awards.split("\n") if a.strip()] if awards else []
    else:
        result["awards"] = []

    return result
