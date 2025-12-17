# frontend/app.py
import time

import streamlit as st

# 导入 API 客户端函数
from api_client import (
    comprehensive_evaluation,
    extract_resume,
    save_resume_data,
    search_jobs,
)

# 导入模块编辑器组件
from module_editor import render_basic_info_editor, render_module_editor
from module_order_manager import get_current_module_order, render_module_order_manager

# 配置页面
st.set_page_config(
    page_title="AI简历优化助手",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 初始化 session state
# 唯一会话 ID
if "session_id" not in st.session_state:
    import uuid

    st.session_state.session_id = str(uuid.uuid4())
# 当前步骤
if "current_step" not in st.session_state:
    st.session_state.current_step = "template_selection"
# 选中的模板
if "selected_template" not in st.session_state:
    st.session_state.selected_template = None
# 简历数据
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
# 职位搜索条件
if "except_job" not in st.session_state:
    st.session_state.except_job = None
# 职位列表
if "jobs" not in st.session_state:
    st.session_state.jobs = []
# 选中的职位（多选）
if "selected_jobs" not in st.session_state:
    st.session_state.selected_jobs = []
# 综合评估报告
if "evaluation_report" not in st.session_state:
    st.session_state.evaluation_report = None
# 模块修改建议
if "module_suggestions" not in st.session_state:
    st.session_state.module_suggestions = {}
# 编辑中的简历数据（用于AI修改后的临时存储）
if "editing_resume_data" not in st.session_state:
    st.session_state.editing_resume_data = None
# AI修改结果（用于显示对比）
if "ai_modified_results" not in st.session_state:
    st.session_state.ai_modified_results = {}
# AI操作说明（记录AI做了什么）
if "ai_operation_logs" not in st.session_state:
    st.session_state.ai_operation_logs = {}
# 简历是否已保存
if "resume_saved" not in st.session_state:
    st.session_state.resume_saved = False
# 岗位搜索是否完成
if "jobs_loaded" not in st.session_state:
    st.session_state.jobs_loaded = False
# 当前展示的页码（从0开始）
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
# 候选池（用户选中的岗位索引列表）
if "candidate_pool" not in st.session_state:
    st.session_state.candidate_pool = []


# ==================== UI ====================

# 顶部标题
st.title("🤖 AI简历优化助手")
st.markdown("---")

# 侧边栏 - 流程指示
with st.sidebar:
    st.header("📋 流程步骤")

    steps = [
        ("1️⃣", "模板选择", "template_selection"),
        ("2️⃣", "简历信息输入", "form"),
        ("3️⃣", "意向岗位搜索", "job_search"),
        ("4️⃣", "匹配度分析", "analysis"),
    ]

    for emoji, name, step in steps:
        if st.session_state.current_step == step:
            st.markdown(f"**{emoji} {name}** ⬅️")
        else:
            st.markdown(f"{emoji} {name}")

    st.markdown("---")

    # 进度信息
    if st.session_state.session_id:
        st.info(f"会话ID: {st.session_state.session_id[:8]}...")

        # 显示进度
        if st.session_state.resume_saved:
            st.success("✅ 简历已保存")
        if st.session_state.jobs_loaded:
            st.success(f"✅ 已加载 {len(st.session_state.jobs)} 个岗位")
        if st.session_state.selected_jobs:
            st.success(f"✅ 已选择 {len(st.session_state.selected_jobs)} 个岗位")

        st.markdown("---")

        if st.button("🔄 重新开始"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ==================== 主要内容 ====================
# Step 1: 模板选择
if st.session_state.current_step == "template_selection":
    st.header("🎨 Step 1: 选择简历模板")

    st.markdown("请选择您喜欢的简历模板风格")

    # 显示两个模板的预览
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📘 经典模板")
        st.image("./images/classic.png", width="stretch")
        if st.button(
            "选择经典模板",
            width="stretch",
            type="primary" if st.session_state.selected_template == "classic" else "secondary",
        ):
            st.session_state.selected_template = "classic"
            st.success("✅ 已选择经典模板")

    with col2:
        st.markdown("### 📗 现代模板")
        st.image("./images/modern.png", width="stretch")
        if st.button(
            "选择现代模板",
            width="stretch",
            type="primary" if st.session_state.selected_template == "modern" else "secondary",
        ):
            st.session_state.selected_template = "modern"
            st.success("✅ 已选择现代模板")

    st.markdown("---")

    # 显示当前选择
    if st.session_state.selected_template:
        template_name = "经典模板" if st.session_state.selected_template == "classic" else "现代模板"
        st.info(f"当前选择: {template_name}")

        if st.button("📝 继续填写简历", width="stretch", type="primary"):
            st.session_state.current_step = "form"
            st.rerun()
    else:
        st.warning("请先选择一个模板")

# Step 2: 简历信息填写
elif st.session_state.current_step == "form":
    st.header("📝 Step 2: 简历信息填写")

    # 提供两种方式：上传简历或手动填写
    tab1, tab2 = st.tabs(["📄 上传简历自动填写", "✍️ 手动填写"])

    with tab1:
        st.markdown("上传你的简历，AI将自动提取信息并填入表单")
        uploaded_file = st.file_uploader(
            "上传简历 (支持 .txt、.docx、.pdf 格式)",
            type=["txt", "docx", "pdf"],
            key="resume_upload",
        )

        if st.button("🤖 提取信息", width="stretch") and uploaded_file:
            with st.spinner("正在提取简历信息，请稍候..."):
                success, message, resume_data = extract_resume(uploaded_file)

                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.markdown(
            "请填写你的简历信息，如果已上传简历，信息会自动填充，填充后请手动勾选已经识别到的简历模块（如教育背景、工作经历、项目经历等），以确保这些模块会被包含在最终简历中"
        )

        # 初始化 resume_data
        if st.session_state.resume_data is None:
            st.session_state.resume_data = {
                "basicInfo": {
                    "name": "",
                    "position": "",
                    "gender": "",
                    "age": "",
                    "hometown": "",
                    "phone": "",
                    "email": "",
                },
                "photo": None,
                "personalSummary": "",
                "education": [],
                "skills": "",
                "workExperience": [],
                "internshipExperience": [],
                "projects": [],
                "awards": [],
            }

        resume_data = st.session_state.resume_data

        # 使用通用组件渲染复选框
        from form_components import render_checkbox_section

        include_flags = render_checkbox_section(resume_data)

        st.markdown("---")

        # 经历数量控制（保留原有逻辑，因为这是特殊功能）
        st.markdown("### 📊 设置经历数量")
        col1, col2, col3, col4 = st.columns(4)

        list_modules = ["education", "workExperience", "internshipExperience", "projects"]
        count_values = {}

        for idx, module_key in enumerate(list_modules):
            with [col1, col2, col3, col4][idx]:
                from module_config import RESUME_MODULES

                config = RESUME_MODULES[module_key]
                count_values[module_key] = st.number_input(
                    f"{config.icon} {config.title}",
                    min_value=0 if not include_flags.get(module_key) else 1,
                    max_value=5,
                    value=max(
                        1 if include_flags.get(module_key) else 0,
                        len(resume_data.get(module_key, [])),
                    ),
                    key=f"{module_key}_count_control",
                    disabled=not include_flags.get(module_key),
                )

        st.markdown("---")

        with st.form("resume_form"):
            # 1. 个人照片（特殊功能，保留）
            with st.expander("📷 个人照片（可选）", expanded=False):
                st.markdown("上传您的个人照片，将显示在简历右上角")
                current_photo = resume_data.get("photo")
                if current_photo:
                    st.info("✅ 已有照片，可以重新上传以替换")

                uploaded_photo = st.file_uploader(
                    "选择照片文件",
                    type=["jpg", "jpeg", "png"],
                    key="photo_upload",
                    help="支持 JPG、JPEG、PNG 格式。如需取消上传，点击文件名旁的 ✕ 按钮",
                )
                if uploaded_photo:
                    st.image(uploaded_photo, width=150, caption="预览")
                    st.caption("💡 提示：保存后可在编辑页面删除照片")

            # 2. 基本信息
            with st.expander("📝 个人基本信息", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("姓名 *", value=resume_data["basicInfo"].get("name", ""))
                with col2:
                    position = st.text_input("目标职位 *", value=resume_data["basicInfo"].get("position", ""))

                st.markdown("##### 其他信息（可选）")
                col1, col2, col3 = st.columns(3)
                with col1:
                    gender = st.text_input(
                        "性别", value=resume_data["basicInfo"].get("gender", ""), placeholder="例如：男/女"
                    )
                    phone = st.text_input(
                        "电话", value=resume_data["basicInfo"].get("phone", ""), placeholder="例如：138-0000-0000"
                    )
                with col2:
                    age = st.text_input("年龄", value=resume_data["basicInfo"].get("age", ""), placeholder="例如：25")
                    email = st.text_input(
                        "邮箱", value=resume_data["basicInfo"].get("email", ""), placeholder="例如：example@email.com"
                    )
                with col3:
                    hometown = st.text_input(
                        "籍贯", value=resume_data["basicInfo"].get("hometown", ""), placeholder="例如：北京"
                    )
                    st.write("")

            # 3-9. 使用通用组件渲染各模块表单
            from form_components import render_form_with_count

            form_data = render_form_with_count(resume_data, include_flags, count_values)

            # 提交按钮
            submitted = st.form_submit_button("💾 保存并继续", width="stretch")

            if submitted:
                if not name or not position:
                    st.error("请填写所有必填字段（姓名、目标职位）")
                    st.stop()

                # 构建简历数据
                new_resume_data = {
                    "basicInfo": {
                        "name": name,
                        "position": position,
                        "gender": gender if gender else "",
                        "age": age if age else "",
                        "hometown": hometown if hometown else "",
                        "phone": phone if phone else "",
                        "email": email if email else "",
                    },
                    "photo": uploaded_photo,
                    **form_data,
                }

                with st.spinner("正在保存简历数据..."):
                    resume_data_to_save = new_resume_data.copy()
                    photo_to_save = resume_data_to_save.pop("photo", None)

                    success, message = save_resume_data(resume_data_to_save)

                    if success:
                        st.session_state.resume_data = new_resume_data
                        st.session_state.resume_saved = True
                        st.session_state.current_step = "job_search"
                        st.success("简历已保存！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

# Step 3: 搜索岗位
elif st.session_state.current_step == "job_search":
    st.header("🔍 Step 3: 搜索意向岗位")

    st.markdown("请选择你想要搜索的职位类型")

    with st.form("job_search_form"):
        # 职位选项列表（从 tools/mappings.py 的 job_dict 中获取）
        job_options = [
            "Java",
            "C/C++",
            "Python",
            "Golang",
            "Node.js",
            "图像算法",
            "自然语言处理算法",
            "大模型算法",
            "数据挖掘",
            "规控算法",
            "SLAM算法",
            "推荐算法",
            "搜索算法",
        ]

        job = st.selectbox(
            "🎯 选择目标职位",
            options=job_options,
            index=job_options.index("Python") if "Python" in job_options else 0,
            help="请选择你想要检索的职位类型",
        )

        submitted = st.form_submit_button("🎯 开始检索职位", width="stretch")

        if submitted:
            except_job = {
                "job": job,
            }

            st.session_state.except_job = except_job

            with st.spinner("正在检索职位数据，请稍候..."):
                success, message, jobs = search_jobs(except_job)

                if success:
                    st.session_state.jobs = jobs
                    st.session_state.jobs_loaded = True
                    st.success(message)
                    st.info(f"为你找到 {len(jobs)} 个匹配职位")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

    # 显示职位列表（如果已搜索）
    if st.session_state.jobs_loaded and st.session_state.jobs:
        st.markdown("---")

        # 候选池展示
        if st.session_state.candidate_pool:
            st.subheader("🎯 候选池")
            st.info(f"已添加 {len(st.session_state.candidate_pool)} 个岗位到候选池")

            # 显示候选池中的岗位
            for job_idx in st.session_state.candidate_pool:
                # 找到对应的岗位信息
                job = next((j for j in st.session_state.jobs if j["index"] == job_idx), None)
                if job:
                    with st.container():
                        col1, col2 = st.columns([5, 1])

                        with col1:
                            st.markdown(f"**{job['name']}** @ {job['company']} | 💰 {job['salary']}")

                        with col2:
                            if st.button(
                                "❌ 移除",
                                key=f"remove_candidate_{job_idx}",
                                width="stretch",
                            ):
                                st.session_state.candidate_pool.remove(job_idx)
                                st.rerun()

            st.markdown("---")

        # 分页展示职位列表
        st.subheader("💼 职位列表")

        # 计算分页参数
        page_size = 10
        total_jobs = len(st.session_state.jobs)
        total_pages = (total_jobs + page_size - 1) // page_size
        current_page = st.session_state.current_page

        # 确保页码在有效范围内
        if current_page >= total_pages:
            current_page = 0
            st.session_state.current_page = 0

        # 计算当前页的起始和结束索引
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_jobs)

        # 显示分页信息和刷新按钮
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.info(f"显示第 {start_idx + 1}-{end_idx} 个岗位，共 {total_jobs} 个")
        with col2:
            if current_page < total_pages - 1:
                if st.button("🔄 加载下一页", width="stretch"):
                    st.session_state.current_page += 1
                    st.rerun()
            else:
                st.warning("已经是最后一页了")
        with col3:
            if current_page > 0:
                if st.button("⬅️ 上一页", width="stretch"):
                    st.session_state.current_page -= 1
                    st.rerun()

        st.markdown("---")

        # 显示当前页的职位
        current_page_jobs = st.session_state.jobs[start_idx:end_idx]

        for job in current_page_jobs:
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### {job['name']}")
                    st.markdown(f"**{job['company']}** | 💰 {job['salary']} | 📍 {job['location']}")
                    st.markdown(f"📚 {job['experience']} | 🎓 {job['education']}")

                    with st.expander("查看岗位描述"):
                        st.markdown(job["description"])

                with col2:
                    st.write("")
                    st.write("")
                    # 添加到候选池的按钮
                    job_idx = job["index"]
                    is_in_pool = job_idx in st.session_state.candidate_pool

                    if is_in_pool:
                        st.success("✅ 已添加")
                    else:
                        if st.button(
                            "➕ 添加到候选池",
                            key=f"add_to_pool_{job_idx}",
                            width="stretch",
                        ):
                            st.session_state.candidate_pool.append(job_idx)
                            st.rerun()

        st.markdown("---")

        # 继续按钮
        if st.session_state.candidate_pool:
            st.success(f"✅ 候选池中有 {len(st.session_state.candidate_pool)} 个岗位")

            if st.button("📊 开始匹配度分析", width="stretch", type="primary"):
                # 将候选池的岗位复制到 selected_jobs
                st.session_state.selected_jobs = st.session_state.candidate_pool.copy()
                st.session_state.current_step = "analysis"
                st.rerun()
        else:
            st.warning("请至少添加一个岗位到候选池")

# Step 4: 综合评估与简历编辑
elif st.session_state.current_step == "analysis":
    st.header("📊 Step 4: 综合评估与简历优化")

    if not st.session_state.selected_jobs:
        st.warning("未选择任何岗位")
        if st.button("返回"):
            st.session_state.current_step = "job_search"
            st.rerun()
    else:
        # 初始化编辑中的简历数据
        if st.session_state.editing_resume_data is None:
            st.session_state.editing_resume_data = st.session_state.resume_data.copy()

        # 如果还没有综合评估报告，显示开始评估按钮
        if not st.session_state.evaluation_report:
            st.info(f"准备对 {len(st.session_state.selected_jobs)} 个岗位进行综合评估")

            # 显示选中的岗位
            with st.expander("📋 已选择的岗位", expanded=True):
                for job_idx in st.session_state.selected_jobs:
                    job = st.session_state.jobs[job_idx]
                    st.markdown(f"- **{job['name']}** @ {job['company']} | {job['salary']}")

            if st.button("🚀 开始综合评估", width="stretch", type="primary"):
                with st.spinner("正在进行综合评估，请稍候..."):
                    success, message, report = comprehensive_evaluation(st.session_state.selected_jobs)

                    if success:
                        st.session_state.evaluation_report = report
                        st.session_state.module_suggestions = report.get("module_suggestions", {})
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

        # 显示综合评估报告和简历编辑界面
        else:
            report = st.session_state.evaluation_report

            # 顶部操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔙 返回岗位选择", width="stretch"):
                    st.session_state.current_step = "job_search"
                    st.session_state.evaluation_report = None
                    st.session_state.module_suggestions = {}
                    st.session_state.editing_resume_data = None
                    st.rerun()
            with col2:
                if st.button("🔄 重新评估", width="stretch"):
                    st.session_state.evaluation_report = None
                    st.session_state.module_suggestions = {}
                    st.rerun()
            with col3:
                # 下载PDF按钮
                if st.button("📥 生成PDF简历", width="stretch", type="primary"):
                    with st.spinner("正在保存简历数据..."):
                        # 导入API客户端
                        from api_client import generate_pdf

                        # 先同步前端编辑的数据到后端
                        resume_data_to_save = st.session_state.editing_resume_data.copy()
                        photo_to_save = resume_data_to_save.pop("photo", None)

                        # 调用save_resume_data同步数据
                        save_success, save_message = save_resume_data(resume_data_to_save)

                        if not save_success:
                            st.error(f"❌ 保存失败: {save_message}")
                            st.stop()

                    with st.spinner("正在生成PDF简历，请稍候..."):
                        # 获取模板类型和照片
                        template_type = st.session_state.selected_template
                        photo_file = photo_to_save

                        # 获取用户自定义的模块顺序
                        from module_order_manager import get_current_module_order

                        module_order = get_current_module_order()

                        # 生成PDF
                        success, message, pdf_path = generate_pdf(template_type, photo_file, module_order)

                        if success:
                            st.success(f"✅ {message}")

                            # 读取PDF文件并提供下载
                            try:
                                with open(pdf_path, "rb") as pdf_file:
                                    pdf_bytes = pdf_file.read()

                                # 获取文件名
                                import os

                                pdf_filename = os.path.basename(pdf_path)

                                # 提供下载按钮
                                st.download_button(
                                    label="💾 点击下载PDF",
                                    data=pdf_bytes,
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    width="stretch",
                                )
                            except Exception as e:
                                st.error(f"❌ 读取PDF文件失败: {str(e)}")
                                st.info(f"PDF文件路径: {pdf_path}")
                        else:
                            st.error(f"❌ {message}")

            st.markdown("---")

            # 显示综合评估报告
            st.markdown("### 📋 综合评估报告")

            with st.expander("📊 查看完整评估报告", expanded=True):
                # 总体评分
                if "overall_score" in report:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.metric("综合匹配度", f"{report['overall_score']}/100")

                # 总体评价
                if "summary" in report:
                    st.markdown("#### 📝 总体评价")
                    st.info(report["summary"])

                # 优势分析
                if "strengths" in report and report["strengths"]:
                    st.markdown("#### ✅ 优势")
                    for strength in report["strengths"]:
                        st.markdown(f"- {strength}")

                # 待改进点
                if "weaknesses" in report and report["weaknesses"]:
                    st.markdown("#### ⚠️ 待改进点")
                    for weakness in report["weaknesses"]:
                        st.markdown(f"- {weakness}")

                # 关键建议
                if "key_recommendations" in report and report["key_recommendations"]:
                    st.markdown("#### 💡 关键建议")
                    for rec in report["key_recommendations"]:
                        st.markdown(f"- {rec}")

            st.markdown("---")
            st.markdown("### ✏️ 简历编辑与优化")
            st.info(
                "💡 提示：您可以手动编辑简历内容，或点击「🤖 AI修改」按钮让AI根据评估建议自动优化该模块，当修改完成后, 请点击下面的保存按钮保存修改"
            )

            editing_data = st.session_state.editing_resume_data
            module_suggestions = st.session_state.module_suggestions

            # 模块顺序管理
            with st.expander("⚙️ 自定义模块顺序", expanded=False):
                render_module_order_manager()

            st.markdown("---")

            # 1. 基本信息（不可AI修改，只能手动编辑，始终在首位）
            render_basic_info_editor(editing_data)

            # 2-8. 按照用户自定义的顺序渲染其他模块
            module_order = get_current_module_order()
            for module_key in module_order:
                render_module_editor(module_key, editing_data, module_suggestions)


# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ by Auto-Resume Agent | Powered by LangGraph</div>",
    unsafe_allow_html=True,
)
