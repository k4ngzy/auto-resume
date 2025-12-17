# frontend/module_config.py
"""
简历模块编辑器配置
定义每个简历模块的元数据和渲染规则
"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass


@dataclass
class ModuleConfig:
    """模块配置类"""
    key: str  # 数据字段名
    title: str  # 显示标题
    icon: str  # 图标
    module_type: str  # 模块类型: 'text', 'textarea', 'list', 'structured_list'
    ai_modifiable: bool = True  # 是否支持AI修改
    ai_evaluable: bool = True  # 是否支持AI评估

    # 对于structured_list类型，定义字段配置
    fields: Optional[List[Dict[str, Any]]] = None

    # 自定义渲染函数（可选）
    custom_renderer: Optional[Callable] = None

    # 显示AI修改结果的自定义函数（可选）
    custom_ai_result_renderer: Optional[Callable] = None


# 定义所有简历模块的配置
RESUME_MODULES = {
    "personalSummary": ModuleConfig(
        key="personalSummary",
        title="自我评价",
        icon="🔍",
        module_type="textarea",
        ai_modifiable=True,
        ai_evaluable=True,
    ),

    "education": ModuleConfig(
        key="education",
        title="教育背景",
        icon="🎓",
        module_type="structured_list",
        ai_modifiable=True,
        ai_evaluable=True,
        fields=[
            {"name": "school", "label": "学校", "type": "text", "col": 1},
            {"name": "major", "label": "专业", "type": "text", "col": 1},
            {"name": "degree", "label": "学位", "type": "text", "col": 1},
            {"name": "date", "label": "时间", "type": "text", "col": 2},
            {"name": "gpa", "label": "GPA", "type": "text", "col": 2},
            {"name": "courses", "label": "相关课程", "type": "text", "col": None},
        ],
    ),

    "skills": ModuleConfig(
        key="skills",
        title="技术能力",
        icon="💻",
        module_type="textarea",
        ai_modifiable=True,
        ai_evaluable=True,
    ),

    "workExperience": ModuleConfig(
        key="workExperience",
        title="工作经历",
        icon="💼",
        module_type="structured_list",
        ai_modifiable=True,
        ai_evaluable=True,
        fields=[
            {"name": "company", "label": "公司", "type": "text", "col": 1},
            {"name": "position", "label": "职位", "type": "text", "col": 1},
            {"name": "date", "label": "时间", "type": "text", "col": 2},
            {"name": "points", "label": "工作内容 (每条用换行分隔)", "type": "textarea", "col": None, "is_list": True},
        ],
    ),

    "internshipExperience": ModuleConfig(
        key="internshipExperience",
        title="实习经历",
        icon="🎓",
        module_type="structured_list",
        ai_modifiable=True,
        ai_evaluable=True,
        fields=[
            {"name": "company", "label": "公司", "type": "text", "col": 1},
            {"name": "position", "label": "职位", "type": "text", "col": 1},
            {"name": "date", "label": "时间", "type": "text", "col": 2},
            {"name": "points", "label": "实习内容 (每条用换行分隔)", "type": "textarea", "col": None, "is_list": True},
        ],
    ),

    "projects": ModuleConfig(
        key="projects",
        title="项目经历",
        icon="🚀",
        module_type="structured_list",
        ai_modifiable=True,
        ai_evaluable=True,
        fields=[
            {"name": "name", "label": "项目名称", "type": "text", "col": 1},
            {"name": "date", "label": "时间", "type": "text", "col": 2},
            {"name": "role", "label": "角色", "type": "text", "col": None},
            {"name": "description", "label": "项目描述 (每条用换行分隔)", "type": "textarea", "col": None, "is_list": True},
        ],
    ),

    "awards": ModuleConfig(
        key="awards",
        title="荣誉证书",
        icon="🏆",
        module_type="list",
        ai_modifiable=True,
        ai_evaluable=True,
    ),
}


def get_module_config(module_key: str) -> Optional[ModuleConfig]:
    """获取模块配置"""
    return RESUME_MODULES.get(module_key)


def get_all_module_keys() -> List[str]:
    """获取所有模块的key"""
    return list(RESUME_MODULES.keys())


# 默认的模块顺序
DEFAULT_MODULE_ORDER = [
    "personalSummary",
    "education",
    "skills",
    "workExperience",
    "internshipExperience",
    "projects",
    "awards",
]


def get_default_module_order() -> List[str]:
    """获取默认的模块顺序"""
    return DEFAULT_MODULE_ORDER.copy()
