# frontend/module_editor.py
"""
通用的简历模块编辑器组件
通过配置驱动的方式渲染不同类型的简历模块
"""

import time
from typing import Dict

import streamlit as st
from api_client import modify_resume_module, re_evaluate_module
from module_config import ModuleConfig, get_module_config


def render_ai_buttons(module_key: str, config: ModuleConfig, editing_data: Dict, module_suggestions: Dict):
    """渲染AI优化和评估按钮"""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown("**当前内容：**")

    with col2:
        if config.ai_modifiable and st.button("🤖 AI优化/生成", key=f"ai_{module_key}", use_container_width=True):
            with st.spinner("AI正在处理..."):
                feedback = module_suggestions.get(module_key, "")
                current_data = editing_data.get(module_key, "" if config.module_type in ["text", "textarea"] else [])

                success, message, modified, operation_log, operation_type = modify_resume_module(
                    module_key,
                    current_data,
                    feedback,
                )

                if success:
                    st.session_state.ai_modified_results[module_key] = modified
                    st.session_state.ai_operation_logs[module_key] = operation_log
                    st.success(f"{config.title}已{operation_type}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(message)

    with col3:
        if config.ai_evaluable and st.button("📊 AI评估", key=f"eval_{module_key}", use_container_width=True):
            with st.spinner("AI正在评估..."):
                current_data = editing_data.get(module_key, "" if config.module_type in ["text", "textarea"] else [])
                eval_success, eval_msg, new_suggestion = re_evaluate_module(
                    module_key,
                    current_data,
                )

                if eval_success:
                    module_suggestions[module_key] = new_suggestion
                    st.session_state.module_suggestions = module_suggestions
                    st.success("评估完成")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(eval_msg)


def render_ai_suggestion(module_key: str, module_suggestions: Dict):
    """显示AI评估建议"""
    if module_suggestions.get(module_key):
        st.info(f"💡 AI建议：{module_suggestions[module_key]}")


def render_ai_operation_log(module_key: str):
    """显示AI操作日志"""
    if module_key in st.session_state.ai_operation_logs:
        st.info(f"ℹ️ {st.session_state.ai_operation_logs[module_key]}")


def render_textarea_module(module_key: str, config: ModuleConfig, editing_data: Dict):
    """渲染文本域类型的模块（如自我评价、技术能力）"""
    current_value = editing_data.get(module_key, "")

    new_value = st.text_area(
        f"{config.title}内容",
        value=current_value,
        height=150 if module_key == "skills" else 100,
        key=f"edit_{module_key}",
    )

    # 显示AI修改结果 - 使用markdown格式显示
    if module_key in st.session_state.ai_modified_results:
        st.markdown("**🤖 AI生成/优化结果：**")
        modified_content = st.session_state.ai_modified_results[module_key]

        # 使用markdown显示，保留换行和格式
        if isinstance(modified_content, str):
            # 将内容放在引用框中显示
            st.markdown(f"> {modified_content.replace(chr(10), chr(10) + '> ')}")
        else:
            st.text(str(modified_content))

    if st.button(f"💾 保存{config.title}", key=f"save_{module_key}"):
        editing_data[module_key] = new_value
        st.session_state.editing_resume_data[module_key] = new_value
        st.success(f"{config.title}已保存")
        time.sleep(0.5)
        st.rerun()


def render_list_module(module_key: str, config: ModuleConfig, editing_data: Dict):
    """渲染简单列表类型的模块（如荣誉证书）"""
    current_list = editing_data.get(module_key, [])
    list_text = "\n".join(current_list) if isinstance(current_list, list) else ""

    new_value = st.text_area(
        f"{config.title} (每条用换行分隔)",
        value=list_text,
        height=100,
        key=f"edit_{module_key}",
    )

    # 显示AI修改结果 - 使用markdown格式显示
    if module_key in st.session_state.ai_modified_results:
        st.markdown("**🤖 AI生成/优化结果：**")
        modified_content = st.session_state.ai_modified_results[module_key]

        # 如果是列表，使用markdown列表格式显示
        if isinstance(modified_content, list):
            for item in modified_content:
                st.markdown(f"- {item}")
        elif isinstance(modified_content, str):
            # 如果是字符串，按行分割并显示为列表
            for line in modified_content.split("\n"):
                if line.strip():
                    st.markdown(f"- {line.strip()}")
        else:
            st.text(str(modified_content))

    if st.button(f"💾 保存{config.title}", key=f"save_{module_key}"):
        editing_data[module_key] = [a.strip() for a in new_value.split("\n") if a.strip()]
        st.session_state.editing_resume_data[module_key] = editing_data[module_key]
        st.success(f"{config.title}已保存")
        time.sleep(0.5)
        st.rerun()


def render_structured_list_item(module_key: str, config: ModuleConfig, item: Dict, index: int, editing_data: Dict):
    """渲染结构化列表中的单个项目"""
    with st.container():
        # 标题和删除按钮
        col_title, col_delete = st.columns([5, 1])
        with col_title:
            st.markdown(f"**{config.title} {index + 1}**")
        with col_delete:
            if st.button("🗑️ 删除", key=f"delete_{module_key}_{index}", use_container_width=True):
                editing_data[module_key].pop(index)
                st.session_state.editing_resume_data[module_key] = editing_data[module_key]
                st.rerun()

        # 根据字段配置渲染输入框
        updated_item = {}
        col1_fields = [f for f in config.fields if f.get("col") == 1]
        col2_fields = [f for f in config.fields if f.get("col") == 2]
        full_width_fields = [f for f in config.fields if f.get("col") is None]

        # 渲染两列布局的字段
        if col1_fields or col2_fields:
            col1, col2 = st.columns(2)

            with col1:
                for field in col1_fields:
                    value = st.text_input(
                        field["label"],
                        value=item.get(field["name"], ""),
                        key=f"edit_{module_key}_{field['name']}_{index}",
                    )
                    updated_item[field["name"]] = value

            with col2:
                for field in col2_fields:
                    value = st.text_input(
                        field["label"],
                        value=item.get(field["name"], ""),
                        key=f"edit_{module_key}_{field['name']}_{index}",
                    )
                    updated_item[field["name"]] = value

        # 渲染全宽字段
        for field in full_width_fields:
            if field["type"] == "textarea":
                # 处理列表类型的字段（如points, description）
                if field.get("is_list"):
                    current_value = "\n".join(item.get(field["name"], []))
                    value = st.text_area(
                        field["label"],
                        value=current_value,
                        height=120,
                        key=f"edit_{module_key}_{field['name']}_{index}",
                    )
                    updated_item[field["name"]] = [p.strip() for p in value.split("\n") if p.strip()]
                else:
                    value = st.text_area(
                        field["label"],
                        value=item.get(field["name"], ""),
                        height=120,
                        key=f"edit_{module_key}_{field['name']}_{index}",
                    )
                    updated_item[field["name"]] = value
            else:
                value = st.text_input(
                    field["label"],
                    value=item.get(field["name"], ""),
                    key=f"edit_{module_key}_{field['name']}_{index}",
                )
                updated_item[field["name"]] = value

        # 更新数据
        editing_data[module_key][index] = updated_item
        st.markdown("---")


def render_structured_list_ai_result(module_key: str, config: ModuleConfig):
    """渲染结构化列表的AI修改结果"""
    if module_key not in st.session_state.ai_modified_results:
        return

    st.markdown("**🤖 AI生成/优化结果：**")
    modified_data = st.session_state.ai_modified_results[module_key]

    if not isinstance(modified_data, list):
        st.text(str(modified_data))
        return

    for idx, item in enumerate(modified_data):
        # 根据模块类型显示不同的标题
        if module_key == "education":
            title = item.get("school", "未命名学校")
        elif module_key in ["workExperience", "internshipExperience"]:
            title = item.get("company", "未命名公司")
        elif module_key == "projects":
            title = item.get("name", "未命名项目")
        else:
            title = f"{config.title} {idx + 1}"

        st.markdown(f"**{config.title} {idx + 1}：{title}**")

        # 显示所有字段
        for field in config.fields:
            field_name = field["name"]
            field_label = field["label"].split("(")[0].strip()  # 移除括号说明

            if field.get("is_list"):
                # 列表类型字段
                if item.get(field_name):
                    st.markdown(f"- **{field_label}**：")
                    for desc in item.get(field_name, []):
                        st.markdown(f"  - {desc}")
            else:
                # 普通字段
                value = item.get(field_name, "")
                if value:
                    st.markdown(f"- **{field_label}**：{value}")

        st.markdown("---")


def render_structured_list_module(module_key: str, config: ModuleConfig, editing_data: Dict):
    """渲染结构化列表类型的模块（如教育背景、工作经历等）"""
    current_list = editing_data.get(module_key, [])

    # 渲染每个列表项
    for i, item in enumerate(current_list):
        render_structured_list_item(module_key, config, item, i, editing_data)

    # 如果列表为空，显示提示
    if not current_list:
        st.info(f"📝 当前没有{config.title}，点击下方按钮添加")

    # 添加新项按钮
    if st.button(f"➕ 添加{config.title}", key=f"add_{module_key}", use_container_width=True):
        # 创建空白项
        new_item = {}
        for field in config.fields:
            if field.get("is_list"):
                new_item[field["name"]] = []
            else:
                new_item[field["name"]] = ""

        if module_key not in editing_data:
            editing_data[module_key] = []
        editing_data[module_key].append(new_item)
        st.session_state.editing_resume_data[module_key] = editing_data[module_key]
        st.rerun()

    # 显示AI修改结果
    render_structured_list_ai_result(module_key, config)

    # 保存按钮
    if st.button(f"💾 保存{config.title}", key=f"save_{module_key}"):
        st.session_state.editing_resume_data[module_key] = editing_data.get(module_key, [])
        st.success(f"{config.title}已保存")
        time.sleep(0.5)
        st.rerun()


def render_module_editor(module_key: str, editing_data: Dict, module_suggestions: Dict, expanded: bool = False):
    """
    渲染单个简历模块的编辑器

    Args:
        module_key: 模块的key（如 'personalSummary', 'education'）
        editing_data: 正在编辑的简历数据
        module_suggestions: AI评估建议
        expanded: 是否默认展开
    """
    config = get_module_config(module_key)
    if not config:
        st.error(f"未找到模块配置: {module_key}")
        return

    with st.expander(f"{config.icon} {config.title}", expanded=expanded):
        # 渲染AI按钮
        render_ai_buttons(module_key, config, editing_data, module_suggestions)

        # 显示AI建议
        render_ai_suggestion(module_key, module_suggestions)

        # 根据模块类型渲染不同的编辑器
        if config.module_type == "textarea":
            render_textarea_module(module_key, config, editing_data)
        elif config.module_type == "list":
            render_list_module(module_key, config, editing_data)
        elif config.module_type == "structured_list":
            render_structured_list_module(module_key, config, editing_data)
        else:
            st.error(f"不支持的模块类型: {config.module_type}")

        # 显示AI操作日志
        render_ai_operation_log(module_key)


def render_basic_info_editor(editing_data: Dict):
    """渲染基本信息编辑器（特殊处理，不支持AI修改）"""
    with st.expander("📝 个人基本信息", expanded=False):
        basic_info = editing_data.get("basicInfo", {})

        # 照片上传部分
        st.markdown("##### 📷 个人照片（可选）")
        current_photo = editing_data.get("photo")

        # 显示当前照片状态和操作按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            if current_photo:
                st.success("✅ 已上传照片")
                if hasattr(current_photo, 'name'):
                    st.caption(f"文件名: {current_photo.name}")
            else:
                st.info("未上传照片")

        with col2:
            # 如果有照片，显示删除按钮
            if current_photo:
                if st.button("🗑️ 删除照片", key="remove_photo", use_container_width=True):
                    editing_data["photo"] = None
                    st.session_state.editing_resume_data["photo"] = None
                    st.success("照片已删除")
                    time.sleep(0.5)
                    st.rerun()

        uploaded_photo = st.file_uploader(
            "上传或更换照片",
            type=["jpg", "jpeg", "png"],
            key="edit_photo_upload",
            help="支持 JPG、JPEG、PNG 格式"
        )

        if uploaded_photo:
            st.image(uploaded_photo, width=150, caption="照片预览")

        st.markdown("---")

        # 基本信息
        st.markdown("##### 基本信息")
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("姓名 *", value=basic_info.get("name", ""), key="edit_name")
        with col2:
            position = st.text_input(
                "目标职位 *",
                value=basic_info.get("position", ""),
                key="edit_position",
            )

        st.markdown("##### 其他信息（可选）")
        col1, col2, col3 = st.columns(3)

        with col1:
            gender = st.text_input(
                "性别",
                value=basic_info.get("gender", ""),
                key="edit_gender",
                placeholder="例如：男/女"
            )
            phone = st.text_input(
                "电话",
                value=basic_info.get("phone", ""),
                key="edit_phone",
                placeholder="例如：138-0000-0000"
            )

        with col2:
            age = st.text_input(
                "年龄",
                value=basic_info.get("age", ""),
                key="edit_age",
                placeholder="例如：25"
            )
            email = st.text_input(
                "邮箱",
                value=basic_info.get("email", ""),
                key="edit_email",
                placeholder="例如：example@email.com"
            )

        with col3:
            hometown = st.text_input(
                "籍贯",
                value=basic_info.get("hometown", ""),
                key="edit_hometown",
                placeholder="例如：北京"
            )

        if st.button("💾 保存基本信息", key="save_basic"):
            # 保存基本信息（包含所有字段）
            editing_data["basicInfo"] = {
                "name": name,
                "position": position,
                "gender": gender if gender else "",
                "age": age if age else "",
                "hometown": hometown if hometown else "",
                "phone": phone if phone else "",
                "email": email if email else "",
            }

            # 保存照片（如果有上传新照片）
            if uploaded_photo:
                editing_data["photo"] = uploaded_photo
                st.session_state.editing_resume_data["photo"] = uploaded_photo

            st.session_state.editing_resume_data["basicInfo"] = editing_data["basicInfo"]
            st.success("基本信息已保存")
            time.sleep(0.5)
            st.rerun()
