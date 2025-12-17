# frontend/module_order_manager.py
"""
简历模块顺序管理组件
允许用户自定义简历模块的显示顺序
"""

from typing import List

import streamlit as st
from module_config import get_default_module_order, get_module_config


def render_module_order_manager():
    """
    渲染模块顺序管理界面
    返回当前的模块顺序列表
    """
    # 初始化模块顺序（如果还没有）
    if "module_order" not in st.session_state:
        st.session_state.module_order = get_default_module_order()

    st.markdown("### 📋 自定义模块顺序")
    st.info("💡 提示：调整简历模块的显示顺序，个人基本信息始终在首位")

    # 显示当前顺序
    module_order = st.session_state.module_order

    # 创建一个容器来显示所有模块
    for idx, module_key in enumerate(module_order):
        config = get_module_config(module_key)
        if not config:
            continue

        # 创建一行显示模块信息和操作按钮
        col1, col2, col3, col4 = st.columns([1, 4, 1, 1])

        with col1:
            st.markdown(f"**{idx + 1}**")

        with col2:
            st.markdown(f"{config.icon} **{config.title}**")

        with col3:
            # 上移按钮（第一个模块不能上移）
            if idx > 0:
                if st.button("⬆️", key=f"up_{module_key}", help="上移"):
                    # 交换位置
                    module_order[idx], module_order[idx - 1] = module_order[idx - 1], module_order[idx]
                    st.session_state.module_order = module_order
                    st.rerun()
            else:
                st.markdown("")  # 占位

        with col4:
            # 下移按钮（最后一个模块不能下移）
            if idx < len(module_order) - 1:
                if st.button("⬇️", key=f"down_{module_key}", help="下移"):
                    # 交换位置
                    module_order[idx], module_order[idx + 1] = module_order[idx + 1], module_order[idx]
                    st.session_state.module_order = module_order
                    st.rerun()
            else:
                st.markdown("")  # 占位

    # 重置按钮
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 恢复默认顺序", use_container_width=True):
            st.session_state.module_order = get_default_module_order()
            st.success("已恢复默认顺序")
            st.rerun()

    with col2:
        if st.button("✅ 确认顺序", use_container_width=True, type="primary"):
            st.success("模块顺序已确认")
            return True

    return False


def get_current_module_order() -> List[str]:
    """
    获取当前的模块顺序
    如果用户没有自定义，返回默认顺序
    """
    if "module_order" not in st.session_state:
        st.session_state.module_order = get_default_module_order()
    return st.session_state.module_order


def render_modules_in_order(editing_data, module_suggestions, render_func):
    """
    按照用户自定义的顺序渲染所有模块

    Args:
        editing_data: 编辑中的简历数据
        module_suggestions: AI评估建议
        render_func: 渲染单个模块的函数（通常是 render_module_editor）
    """
    module_order = get_current_module_order()

    for module_key in module_order:
        render_func(module_key, editing_data, module_suggestions)
