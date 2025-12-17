# frontend/api_client.py
"""
API client module for communicating with the backend FastAPI server.
All API calls are centralized here for better maintainability.
"""

import json

import requests
import streamlit as st

# API 配置
API_BASE_URL = "http://localhost:8000"


def extract_resume(uploaded_file):
    """上传简历并提取信息"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"session_id": st.session_state.session_id}

        response = requests.post(
            f"{API_BASE_URL}/api/extract_resume",
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()
        st.session_state.resume_data = result["resume_data"]
        return True, result["message"], result["resume_data"]
    except Exception as e:
        return False, f"错误: {str(e)}", None


def save_resume_data(resume_data: dict):
    """保存简历数据"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/save_resume_data",
            json={
                "session_id": st.session_state.session_id,
                "resume_data": resume_data,
            },
        )
        response.raise_for_status()
        data = response.json()
        st.session_state.resume_data = resume_data
        st.session_state.current_step = data["step"]
        return True, data["message"]
    except Exception as e:
        return False, f"错误: {str(e)}"


def search_jobs(except_job: dict):
    """搜索岗位"""
    try:
        data = {
            "session_id": st.session_state.session_id,
            "except_job": json.dumps(except_job),
        }

        response = requests.post(
            f"{API_BASE_URL}/api/search_jobs_new",
            data=data,
        )
        response.raise_for_status()
        result = response.json()
        st.session_state.jobs = result["jobs"]
        st.session_state.current_step = result["step"]
        return True, "职位列表已生成", result["jobs"]
    except Exception as e:
        return False, f"错误: {str(e)}", []


def comprehensive_evaluation(selected_job_indices: list):
    """综合评估所有选中的岗位"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/comprehensive_evaluation",
            json={
                "session_id": st.session_state.session_id,
                "job_indices": selected_job_indices,
            },
        )
        response.raise_for_status()
        data = response.json()
        return True, "综合评估完成", data["evaluation_report"]
    except Exception as e:
        return False, f"错误: {str(e)}", None


def modify_resume_module(module_name: str, module_data: dict, evaluation_feedback: str):
    """AI优化/生成简历的特定模块"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/modify_resume_module",
            json={
                "session_id": st.session_state.session_id,
                "module_name": module_name,
                "module_data": module_data,
                "evaluation_feedback": evaluation_feedback,
            },
        )
        response.raise_for_status()
        data = response.json()
        return (
            True,
            data["message"],
            data["modified_module"],
            data.get("operation_log", ""),
            data.get("operation_type", "优化"),
        )
    except Exception as e:
        return False, f"错误: {str(e)}", None, "", ""


def re_evaluate_module(module_name: str, module_data: dict):
    """重新评估修改后的模块"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/re_evaluate_module",
            json={
                "session_id": st.session_state.session_id,
                "module_name": module_name,
                "module_data": module_data,
                "evaluation_feedback": "",  # 重新评估不需要旧的反馈
            },
        )
        response.raise_for_status()
        data = response.json()
        return True, data["message"], data["suggestion"]
    except Exception as e:
        return False, f"错误: {str(e)}", None


def generate_pdf(template_type: str, photo_file=None, module_order=None):
    """生成PDF简历"""
    try:
        # 准备请求数据
        data = {
            "session_id": st.session_state.session_id,
            "template_type": template_type,
        }

        # 添加模块顺序（如果有）
        if module_order:
            import json

            data["module_order"] = json.dumps(module_order)

        # 准备文件（如果有照片）
        files = {}
        if photo_file is not None:
            files["photo"] = (photo_file.name, photo_file.getvalue(), photo_file.type)

        # 发送请求
        response = requests.post(
            f"{API_BASE_URL}/api/generate_pdf",
            data=data,
            files=files if files else None,
        )
        response.raise_for_status()
        result = response.json()
        return True, result["message"], result["pdf_path"]
    except Exception as e:
        return False, f"错误: {str(e)}", None
