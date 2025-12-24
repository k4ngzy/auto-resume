"""
LaTeX Resume Generator
根据用户选择的模板和简历数据生成LaTeX代码
"""


def escape_latex(text):
    """转义LaTeX特殊字符"""
    if not text:
        return ""

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }

    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def generate_classic_header(basic_info, has_photo=False):
    """生成经典模板的头部"""
    name = escape_latex(basic_info.get("name", ""))
    gender = escape_latex(basic_info.get("gender", ""))
    age = escape_latex(basic_info.get("age", ""))
    hometown = escape_latex(basic_info.get("hometown", ""))
    phone = escape_latex(basic_info.get("phone", ""))
    email = escape_latex(basic_info.get("email", ""))
    position = escape_latex(basic_info.get("position", ""))

    if has_photo:
        # 构建第二行和第三行的内容
        line2_parts = [p for p in [gender, age, hometown] if p]
        line3_parts = [p for p in [phone, email, position] if p]

        line2 = " \\dotSep ".join(line2_parts) if line2_parts else ""
        line3 = " \\dotSep ".join(line3_parts) if line3_parts else ""

        return f"""\\begin{{tblr}}{{
    width = \\linewidth,
    colspec = {{Q[l,2.25cm]X[c]Q[r,2.25cm]}},
    columns = {{colsep=2pt}},
    row{{1}} = {{ht=4.5em, font=\\Huge\\scshape}},
    row{{3}} = {{ht=2em, abovesep=0pt}},
  }}
  & {name} & \\SetCell[r=3]{{f}} \\includegraphics[width=0.8in]{{images/avatar}} \\\\
  & {line2} & \\\\
  & {line3} & \\\\
\\end{{tblr}}"""
    else:
        # 不含图片的版本
        line1_parts = [p for p in [gender, age, hometown] if p]
        line2_parts = [p for p in [phone, email, position] if p]

        line1 = "{{{}}}{{{}}}{{{}}}{{}}".format(
            line1_parts[0] if len(line1_parts) > 0 else "",
            line1_parts[1] if len(line1_parts) > 1 else "",
            line1_parts[2] if len(line1_parts) > 2 else "",
        )
        line2 = "{{{}}}{{{}}}{{{}}}{{}}".format(
            line2_parts[0] if len(line2_parts) > 0 else "",
            line2_parts[1] if len(line2_parts) > 1 else "",
            line2_parts[2] if len(line2_parts) > 2 else "",
        )

        return f"""\\name{{{name}}}
\\contactInfo{line1}
\\contactInfo{line2}"""


def generate_modern_header(basic_info, has_photo=False):
    """生成现代模板的头部"""
    name = escape_latex(basic_info.get("name", ""))
    gender = escape_latex(basic_info.get("gender", ""))
    age = escape_latex(basic_info.get("age", ""))
    hometown = escape_latex(basic_info.get("hometown", ""))
    phone = escape_latex(basic_info.get("phone", ""))
    email = escape_latex(basic_info.get("email", ""))
    position = escape_latex(basic_info.get("position", ""))

    if has_photo:
        # 构建第二行和第三行的内容
        line2_parts = []
        if gender:
            line2_parts.append(gender)
        if age:
            line2_parts.append(f"\\calendar{{{age}}}")
        if hometown:
            line2_parts.append(f"\\hometown{{{hometown}}}")

        line3_parts = []
        if phone:
            line3_parts.append(f"\\phone{{{phone}}}")
        if email:
            line3_parts.append(f"\\email{{{email}}}")
        if position:
            line3_parts.append(f"\\position{{{position}}}")

        line2 = "\\dotSep ".join(line2_parts) if line2_parts else ""
        line3 = "\\dotSep ".join(line3_parts) if line3_parts else ""

        return f"""\\begin{{tblr}}{{
    width = \\linewidth,
    colspec = {{Q[l,2.25cm]X[c]Q[r,2.25cm]}},
    % rows = {{abovesep=0pt, belowsep=0pt}},
    columns = {{colsep=2pt}},
    row{{1}} = {{ht=4.5em, font=\\Huge\\scshape}},
    row{{3}} = {{ht=2em, abovesep=0pt}},
  }}
  & {name} & \\SetCell[r=3]{{f}} \\includegraphics[width=0.8in]{{images/avatar}} \\\\
  & {line2} & \\\\
  & {line3}\\\\
\\end{{tblr}}"""
    else:
        # 不含图片的版本
        line1_parts = []
        if gender:
            line1_parts.append(gender)
        if age:
            line1_parts.append(f"\\calendar{{{age}}}")
        if hometown:
            line1_parts.append(f"\\hometown{{{hometown}}}")

        line2_parts = []
        if phone:
            line2_parts.append(f"\\phone{{{phone}}}")
        if email:
            line2_parts.append(f"\\email{{{email}}}")
        if position:
            line2_parts.append(f"\\position{{{position}}}")

        line1 = "\\dotSep\n  ".join(line1_parts) if line1_parts else ""
        line2 = "\\dotSep\n  ".join(line2_parts) if line2_parts else ""

        return f"""\\name{{{name}}}

\\basicInfo{{
  {line1}
}}

\\basicInfo{{
  {line2}
}}"""


def generate_education_section(education_list, template_type="classic"):
    """生成教育背景部分"""
    if not education_list:
        return ""

    if template_type == "classic":
        section = "\\section{教育背景}\n"
        for edu in education_list:
            school = escape_latex(edu.get("school", ""))
            major = escape_latex(edu.get("major", ""))
            degree = escape_latex(edu.get("degree", ""))
            date = escape_latex(edu.get("date", ""))
            gpa = escape_latex(edu.get("gpa", ""))
            courses = escape_latex(edu.get("courses", ""))

            section += f"\\datedsubsection{{\\textbf{{{school}}},{major},\\textit{{{degree}}}}}{{{date}}}\n"
            if gpa:
                section += f" \\ GPA: {gpa}\n"
            if courses:
                section += f" \\ 相关课程: {courses}\n"
        return section
    else:  # modern
        section = "\\sectionTitle{教育背景}{\\faiconsixbf{graduation-cap}}\n"
        for edu in education_list:
            school = escape_latex(edu.get("school", ""))
            major = escape_latex(edu.get("major", ""))
            degree = escape_latex(edu.get("degree", ""))
            date = escape_latex(edu.get("date", ""))
            gpa = escape_latex(edu.get("gpa", ""))
            courses = escape_latex(edu.get("courses", ""))

            section += (
                f"\\datedsubsection{{\\texthl{{{school}}} / \\textit{{{major}}} / \\textit{{{degree}}}}}{{{date}}}\n"
            )
            if gpa:
                section += f"\\normalline{{GPA: {gpa}}}\n"
            if courses:
                section += f"\\normalline{{相关课程: {courses}}}\n"
            section += "\\vspace{-3pt}\n"
        return section


def generate_work_section(work_list, template_type="classic", section_title="工作经历"):
    """生成工作经历部分"""
    if not work_list:
        return ""

    if template_type == "classic":
        section = f"\\section{{{section_title}}}\n"
        for work in work_list:
            company = escape_latex(work.get("company", ""))
            position = escape_latex(work.get("position", ""))
            date = escape_latex(work.get("date", ""))
            points = work.get("points", [])

            section += f"\\datedsubsection{{\\textbf{{{company} | {position}}}}}{{{date}}}\n"
            if points:
                section += "\\begin{itemize}\n"
                for point in points:
                    section += f"  \\item {escape_latex(point)}\n"
                section += "\\end{itemize}\n"
        return section
    else:  # modern
        section = f"\\sectionTitle{{{section_title}}}{{\\faiconsixbf{{building-user}}}}\n"
        for work in work_list:
            company = escape_latex(work.get("company", ""))
            position = escape_latex(work.get("position", ""))
            date = escape_latex(work.get("date", ""))
            points = work.get("points", [])

            section += f"\\datedsubsection{{\\textbf{{{company}}} {position}}}{{{date}}}\n"
            if points:
                section += "\\begin{itemize}\n"
                for point in points:
                    section += f"  \\item {escape_latex(point)}\n"
                section += "\\end{itemize}\n"
        return section


def generate_internship_section(internship_list, template_type="classic"):
    """生成实习经历部分"""
    if not internship_list:
        return ""

    return generate_work_section(internship_list, template_type, section_title="实习经历")


def generate_project_section(project_list, template_type="classic"):
    """生成项目经历部分"""
    if not project_list:
        return ""

    if template_type == "classic":
        section = "\\section{项目经历}\n"
        for proj in project_list:
            name = escape_latex(proj.get("name", ""))
            date = escape_latex(proj.get("date", ""))
            role = escape_latex(proj.get("role", ""))
            description = proj.get("description", [])

            role_text = f",角色: {role}" if role else ""
            section += f"\\datedsubsection{{\\textbf{{{name}}}{role_text}}}{{{date}}}\n"
            if description:
                section += "\\begin{itemize}\n"
                for desc in description:
                    section += f"  \\item {escape_latex(desc)}\n"
                section += "\\end{itemize}\n"
        return section
    else:  # modern
        section = "\\sectionTitle{项目经历}{\\faiconsixbf{users}}\n"
        for proj in project_list:
            name = escape_latex(proj.get("name", ""))
            date = escape_latex(proj.get("date", ""))
            role = escape_latex(proj.get("role", ""))
            description = proj.get("description", [])

            section += f"\\datedsubsection{{\\textbf{{{name}}}}}{{{date}}}\n"
            if role:
                section += f"\\role{{{role}}}{{}}\n"
            if description:
                section += "\\begin{itemize}\n"
                for desc in description:
                    section += f"  \\item {escape_latex(desc)}\n"
                section += "\\end{itemize}\n"
        return section


def generate_skills_section(skills_text, template_type="classic"):
    """生成技能特长部分"""
    if not skills_text or not skills_text.strip():
        return ""

    # 智能检测是否需要分条
    if "\n" in skills_text:
        lines = [line.strip() for line in skills_text.split("\n") if line.strip()]
        if len(lines) > 1:
            # 多行，使用列表格式
            if template_type == "classic":
                section = "\\section{技术特长}\n\\begin{itemize}[parsep=0.2ex]\n"
                for line in lines:
                    section += f"  \\item {escape_latex(line)}\n"
                section += "\\end{itemize}\n"
                return section
            else:  # modern
                section = "\\sectionTitle{技能特长}{\\faiconsixbf{gears}}\n\\begin{onehalfspacing}\n"
                for line in lines:
                    section += f"\\normalline{{{escape_latex(line)}}}\n"
                section += "\\end{onehalfspacing}\n"
                return section

    # 单行，使用原有格式
    skills = escape_latex(skills_text)

    if template_type == "classic":
        return f"""\\section{{技术特长}}
\\begin{{itemize}}[parsep=0.2ex]
  \\item {skills}
\\end{{itemize}}
"""
    else:  # modern
        return f"""\\sectionTitle{{技能特长}}{{\\faiconsixbf{{gears}}}}
\\begin{{onehalfspacing}}
\\normalline{{{skills}}}
\\end{{onehalfspacing}}
"""


def generate_awards_section(awards_list, template_type="classic"):
    """生成荣誉证书部分"""
    if not awards_list:
        return ""

    if template_type == "classic":
        section = "\\section{荣誉证书}\n\\begin{itemize}[parsep=0.2ex]\n"
        for award in awards_list:
            section += f"  \\item {escape_latex(award)}\n"
        section += "\\end{itemize}\n"
        return section
    else:  # modern
        section = "\\sectionTitle{荣誉证书}{\\faiconsixbf{award}}\n\\begin{onehalfspacing}\n"
        for award in awards_list:
            section += f"\\datedline{{{escape_latex(award)}}}{{}}\n"
        section += "\\end{onehalfspacing}\n"
        return section


def generate_summary_section(summary_text, template_type="classic"):
    """生成自我评价部分"""
    if not summary_text or not summary_text.strip():
        return ""

    # 智能检测是否需要分条
    if "\n" in summary_text:
        lines = [line.strip() for line in summary_text.split("\n") if line.strip()]
        if len(lines) > 1:
            # 多行，使用列表格式
            if template_type == "classic":
                section = "\\section{自我评价}\n\\begin{itemize}[parsep=0.2ex]\n"
                for line in lines:
                    section += f"  \\item {escape_latex(line)}\n"
                section += "\\end{itemize}\n"
                return section
            else:  # modern
                section = "\\sectionTitle{自我评价}{\\faiconsixbf{comment}}\n\\begin{onehalfspacing}\n"
                for line in lines:
                    section += f"\\normalline{{{escape_latex(line)}}}\n"
                section += "\\end{onehalfspacing}\n"
                return section

    # 单行，使用原有格式
    summary = escape_latex(summary_text)

    if template_type == "classic":
        return f"""\\section{{自我评价}}
\\begin{{itemize}}[parsep=0.2ex]
  \\item {summary}
\\end{{itemize}}
"""
    else:  # modern
        return f"""\\sectionTitle{{自我评价}}{{\\faiconsixbf{{comment}}}}
\\begin{{onehalfspacing}}
\\normalline{{{summary}}}
\\end{{onehalfspacing}}
"""


def generate_latex_resume(resume_data, template_type="classic", has_photo=False, module_order=None):
    """
    生成完整的LaTeX简历

    Args:
        resume_data: 简历数据字典
        template_type: 模板类型 ("classic" 或 "modern")
        has_photo: 是否包含照片
        module_order: 自定义模块顺序列表，如 ["education", "skills", "workExperience", ...]
                     如果为None，使用默认顺序

    Returns:
        LaTeX代码字符串
    """
    # 文档头部
    if template_type == "classic":
        preamble = """% !TEX TS-program = xelatex
% !TEX encoding = UTF-8 Unicode
% !Mode:: "TeX:UTF-8"

\\documentclass{resume}
\\usepackage{zh_CN-Adobefonts_external}
\\usepackage{linespacing_fix}
\\usepackage{cite}
\\usepackage{graphicx}
\\usepackage{tabularray}

\\begin{document}
\\pagenumbering{gobble}

"""
    else:  # modern
        preamble = """% !TEX TS-program = xelatex
% !TEX encoding = UTF-8 Unicode
% !Mode:: "TeX:UTF-8"

\\documentclass{resume}
\\usepackage{stys/zh_CN-Adobefonts_external}
\\usepackage{stys/linespacing_fix}
\\usepackage{bookmark}
\\usepackage{cite}
\\usepackage{graphicx}
\\usepackage{tabularray}

\\begin{document}
\\pagenumbering{gobble}

\\settitlelinestyle{default}

"""

    # 生成各个部分
    basic_info = resume_data.get("basicInfo", {})

    if template_type == "classic":
        header = generate_classic_header(basic_info, has_photo)
    else:
        header = generate_modern_header(basic_info, has_photo)

    # 创建模块生成器映射
    module_generators = {
        "education": lambda: generate_education_section(resume_data.get("education", []), template_type),
        "workExperience": lambda: generate_work_section(resume_data.get("workExperience", []), template_type),
        "internshipExperience": lambda: generate_internship_section(
            resume_data.get("internshipExperience", []), template_type
        ),
        "projects": lambda: generate_project_section(resume_data.get("projects", []), template_type),
        "skills": lambda: generate_skills_section(resume_data.get("skills", ""), template_type),
        "awards": lambda: generate_awards_section(resume_data.get("awards", []), template_type),
        "personalSummary": lambda: generate_summary_section(resume_data.get("personalSummary", ""), template_type),
    }

    # 如果没有指定顺序，使用默认顺序
    if module_order is None:
        module_order = [
            "education",
            "workExperience",
            "internshipExperience",
            "projects",
            "skills",
            "awards",
            "personalSummary",
        ]

    # 组合所有部分
    latex_content = preamble + header + "\n\n"

    # 按照用户自定义的顺序添加各个模块
    for module_key in module_order:
        if module_key in module_generators:
            section = module_generators[module_key]()
            if section:
                latex_content += section + "\n"

    latex_content += "\\end{document}\n"

    return latex_content
