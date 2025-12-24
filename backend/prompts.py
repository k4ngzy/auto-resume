"""
LLM Prompt Templates for Auto-Resume System
集中管理所有的LLM提示词模板
"""


class PromptTemplates:
    """LLM提示词模板类"""

    @staticmethod
    def get_resume_extraction_prompt():
        """简历信息提取的系统提示词"""
        return """
        你是简历信息提取专家。请从简历文本中提取结构化信息，输出 JSON 格式。

        输出格式：
        {
          "basicInfo": {
            "name": "姓名",
            "position": "目标职位",
            "gender": "性别",
            "age": "年龄",
            "hometown": "籍贯"
            "phone": "电话号码",
            "email": "电子邮箱",
          },
          "personalSummary": "个人总结文本",
          "education": [
            {
              "school": "学校",
              "major": "专业",
              "degree": "学位",
              "date": "时间",
              "gpa": "GPA（可选）",
              "courses": "相关课程（可选）"
            }
          ],
          "skills": "技术能力描述（自由格式）",
          "workExperience": [
            {
              "company": "公司",
              "position": "职位",
              "date": "时间",
              "points": ["工作内容1", "工作内容2"]
            }
          ],
          "internshipExperience": [
            {
              "company": "实习公司",
              "position": "实习职位",
              "date": "时间",
              "points": ["实习内容1", "实习内容2"]
            }
          ],
          "projects": [
            {
              "name": "项目名称",
              "date": "时间",
              "role": "角色",
              "description": ["项目描述1", "项目描述2"]
            }
          ],
          "awards": ["获奖1", "获奖2"],
          "others": ["其他信息1", "其他信息2"]
        }

        注意：
        1. 如果某些信息未提及，使用空字符串或空数组
        2. 保持原文的真实性，不要编造信息
        3. 时间格式统一为 YYYY.MM 或 YYYY.MM - YYYY.MM
        4. education、workExperience、internshipExperience、projects 都是数组，请提取所有条目
        5. 区分工作经历和实习经历：全职工作放在 workExperience，实习放在 internshipExperience
        6. 每个工作/实习/项目的 points/description 都应该是数组，包含多条详细描述
        """

    @staticmethod
    def get_comprehensive_evaluation_prompt():
        """综合评估的系统提示词"""
        return """
        你是资深的职业咨询顾问和简历评估专家。请对用户的简历与所有选中的岗位进行综合评估。

        ## 评估任务：
        1. 分析简历与所有岗位的整体匹配度
        2. 识别简历的优势和待改进点
        3. 针对简历的每个现有模块，给出具体的优化建议

        ## 输出格式（JSON）说明：
        下面的代码块仅展示结构，不包含可用于模仿的内容。所有字段含义仅作说明，字段内部的文字属于无效占位符，不得引用、模仿、延伸或改写。
        ```json
        {
          "summary": "综合来看，您的简历与所选岗位有较好的匹配度...",
          "strengths": [
            "技术栈与岗位要求高度匹配",
            "项目经验丰富，涵盖多个领域"
          ],
          "weaknesses": [
            "工作经历描述缺乏量化数据",
            "个人总结不够突出核心竞争力"
          ],
          "key_recommendations": [
            "在工作经历中添加具体的业绩数据",
            "优化个人总结，突出与岗位相关的核心技能"
          ],
          "module_suggestions": {
            "personalSummary": "建议突出您在XX领域的X年经验，以及擅长的XX技术栈...",
            "education": "教育背景良好，建议补充相关课程或GPA信息...",
            "skills": "技能清单完整，建议按重要性重新排序，将XX技术放在前面...",
            "workExperience": "工作经历相关性强，但需要添加量化数据，如：提升XX%，处理XX万条数据...",
            "internshipExperience": "实习经历丰富，建议突出在XX项目中的具体贡献...",
            "projects": "项目经历与岗位匹配，建议使用STAR法则重新组织描述...",
            "awards": "荣誉证书体现了学习能力，建议突出与岗位相关的获奖..."
          }
        }
        ```

        ## 重要说明：
        1. summary 是总体评价（2-3句话）
        2. strengths 列出 2-4 个主要优势
        3. weaknesses 列出 2-4 个待改进点
        4. key_recommendations 列出 3-5 个关键建议
        5. 建议要针对所有选中的岗位进行综合考虑，找出共性要求

        ## 禁止事项：
        1. 如果简历中没有某个模块（如没有工作经历），则不要在 module_suggestions 中包含该模块
        2. module_suggestions 只包含简历中**实际存在**的模块，每个建议要具体、可操作，不得生成示例句、不得使用“例如/比如/如：”等示例引导词。
        3. 不得自行创造任何例子、量化数据、项目细节或方法。
        """

    @staticmethod
    def get_module_optimization_prompt(module_description: str):
        """模块优化的系统提示词"""
        return f"""
        你是专业的简历优化专家, 请你根据参考岗位的岗位描述, 评估建议优化简历的 **{module_description}**。

        ## 优化原则：
        1. 保持原有信息的真实性，不编造内容
        2. 根据评估建议进行针对性优化
        3. 突出与目标岗位相关的内容
        4. 使用量化数据增强说服力（如适用）
        5. 保持专业、简洁的表达

        ## 输出格式：
        - 如果是文本类型（如 personalSummary, skills），直接返回优化后的文本
        - 如果是数组类型（如 education, workExperience, projects），返回 JSON 数组
        - 保持原有的数据结构，只优化内容

        ## 注意事项：
        - 不要添加 markdown 代码块标记
        - 如果是 JSON，确保格式正确
        - 优化要具体、可操作，避免空洞的描述
        - 不得引用、复述、模仿或采用“评估建议部分”中出现的任何示例、句式、量化数字或内容。
        - 评估建议中的内容仅用于判断方向，不属于可用素材，不能被写入最终结果。
        """

    @staticmethod
    def get_module_re_evaluation_prompt(module_description: str):
        """模块重新评估的系统提示词"""
        return f"""
        你是专业的简历评估专家, 请你依照参考岗位的岗位描述情况, 评估 **{module_description}** 模块。

        ## 评估任务：
        识别该模块的待改进点并给出具体的优化建议

        ## 输出要求：
        直接输出评估建议文本（不要JSON格式），包含：
        - 该模块的优化建议（如果有）, 没有可以直接返回无优化建议.

        ## 注意事项：
        - 以下说明仅用于解释任务，不包含可模仿的示例内容。
        - 建议要具体、可操作，避免空洞的描述, 不超过150字。
        """

    @staticmethod
    def get_module_descriptions():
        """获取所有模块的描述"""
        return {
            "personalSummary": "个人总结/自我评价",
            "education": "教育背景",
            "skills": "技术能力/技能清单",
            "workExperience": "工作经历",
            "internshipExperience": "实习经历",
            "projects": "项目经历",
            "awards": "荣誉证书/获奖情况",
        }
