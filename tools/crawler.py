import asyncio
import csv
import os
import time

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from tqdm import tqdm


async def get_job_details(url: str, max_count: int = 50, max_retries: int = 3) -> str:
    """
    抓取职位搜索页面中的职位详情（使用Playwright异步实现，支持已登录状态）
    """

    login_data_dir = "./user_data"
    os.makedirs("data", exist_ok=True)
    output_path = f"data/job_details_{int(time.time())}.csv"

    # 初始化CSV文件
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        csv_writer = csv.DictWriter(
            f,
            fieldnames=[
                "公司名称",
                "职位名称",
                "工作地点",
                "薪资范围",
                "工作经验",
                "学历要求",
                "职位标签",
                "所需技能",
                "公司规模",
                "公司阶段",
                "所属行业",
                "岗位描述",
            ],
        )
        csv_writer.writeheader()

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=login_data_dir,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        browser_page = await browser.new_page()

        captured_responses = []

        # 异步响应拦截器
        async def handle_response(response):
            if "job/detail.json" in response.url:
                try:
                    await _parse_response(response, captured_responses)
                except Exception as e:
                    print(f"解析响应失败: {e}")

        def sync_handle_response(response):
            asyncio.create_task(handle_response(response))

        browser_page.on("response", sync_handle_response)

        # 禁用自动化特征
        await browser_page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
        """)

        # 页面加载重试逻辑
        for attempt in range(max_retries):
            try:
                await browser_page.goto("https://www.baidu.com", timeout=60000)
                await browser_page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await browser_page.wait_for_selector(".job-info", timeout=30000)
                await browser_page.wait_for_timeout(1000)
                break
            except PlaywrightTimeoutError:
                if attempt == max_retries - 1:
                    raise Exception(f"经过{max_retries}次尝试后仍无法加载页面")
                print(f"页面加载超时，正在进行第{attempt + 2}次重试...")
                await browser_page.reload(timeout=60000)

        # 滚动加载更多岗位
        last_height = await browser_page.evaluate("document.body.scrollHeight")
        for _ in range(3):
            await browser_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await browser_page.wait_for_timeout(800)
            new_height = await browser_page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 获取岗位卡片
        cards = await browser_page.locator(".job-info").all()
        print(f"发现 {len(cards)} 个岗位卡片")

        count = 0
        max_jobs = min(len(cards), max_count)
        pbar = None
        jobs_buffer = []  # 🔥 使用缓冲区收集数据

        try:
            if max_jobs > 0:
                pbar = tqdm(total=max_jobs, desc="抓取岗位中")

            # 🔥 不使用 aiofiles，先收集所有数据
            for card in cards:
                if count >= max_jobs:
                    break

                try:
                    captured_responses.clear()
                    await card.scroll_into_view_if_needed()
                    await card.click()

                    # 等待响应捕获
                    wait_time = 0
                    max_wait = 3
                    while len(captured_responses) == 0 and wait_time < max_wait:
                        await browser_page.wait_for_timeout(200)
                        wait_time += 0.2

                    if len(captured_responses) == 0:
                        if pbar:
                            pbar.write("未捕获到职位详情响应，跳过该职位")
                        else:
                            print("未捕获到职位详情响应，跳过该职位")
                        continue

                    # 解析职位数据
                    json_data = captured_responses[0]
                    zp_data = json_data.get("zpData", {})
                    job_info = zp_data.get("jobInfo", {})
                    brand_com_info = zp_data.get("brandComInfo", {})

                    job_data = {
                        "公司名称": brand_com_info.get("brandName", ""),
                        "职位名称": job_info.get("jobName", ""),
                        "工作地点": job_info.get("address", ""),
                        "薪资范围": job_info.get("salaryDesc", ""),
                        "工作经验": job_info.get("jobExperience", "无要求"),
                        "学历要求": job_info.get("degreeName", ""),
                        "职位标签": job_info.get("experienceName", ""),
                        "所需技能": ",".join(job_info.get("showSkills", [])),
                        "公司规模": brand_com_info.get("scaleName", ""),
                        "公司阶段": brand_com_info.get("stageName", ""),
                        "所属行业": brand_com_info.get("industryName", ""),
                        "岗位描述": job_info.get("postDescription", "").strip(),
                    }

                    # 🔥 添加到缓冲区
                    jobs_buffer.append(job_data)
                    count += 1

                    if pbar:
                        pbar.update(1)
                        pbar.write(f"✅ 已抓取: {job_data['职位名称']} - {job_data['公司名称']}")

                    await browser_page.wait_for_timeout(500)

                except Exception as e:
                    error_msg = f"处理职位时出错: {str(e)}"
                    if pbar:
                        pbar.write(error_msg)
                    else:
                        print(error_msg)

            # 🔥 关键修复：抓取完成后，一次性同步写入所有数据
            if jobs_buffer:
                with open(output_path, "a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=jobs_buffer[0].keys())
                    writer.writerows(jobs_buffer)
                print(f"💾 已写入 {len(jobs_buffer)} 条职位数据")
            else:
                print("⚠️ 未抓取到任何职位数据")

        finally:
            # 关闭进度条
            if pbar is not None:
                try:
                    pbar.close()  # 🔥 也不要 await
                except Exception:
                    pass
            # 确保浏览器关闭
            await browser.close()

    print(f"✅ 已获取职位数据,保存路径: {output_path}")
    return output_path


# 异步解析响应的辅助函数
async def _parse_response(response, captured_responses):
    try:
        data = await response.json()
        captured_responses.append(data)
    except Exception as e:
        print(f"解析响应失败: {e}")


if __name__ == "__main__":
    test_url = "https://www.zhipin.com/web/geek/jobs?city=100010000&position=101310"
    try:
        result = asyncio.run(get_job_details(test_url, max_count=3))
    except Exception as e:
        print(f"抓取过程中出错: {e}")
