import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))


DEFAULT_OUTPUT_DIR = ROOT_DIR / "backend" / "data" / "offline_jobs"
DEFAULT_COMBINED_PATH = ROOT_DIR / "backend" / "data" / "offline_jobs.jsonl"

job_dict = {
    "Java": "100101",
    "C/C++": "100102",
    "Python": "100109",
    "Golang": "100116",
    "Node.js": "100114",
    "图像算法": "101306",
    "自然语言处理算法": "100117",
    "大模型算法": "101310",
    "数据挖掘": "100104",
    "规控算法": "101311",
    "SLAM算法": "101312",
    "推荐算法": "100118",
    "搜索算法": "100115",
}


def get_job_url(except_job: dict, city="100010000", jobType="1901") -> str:
    """
    根据用户提供的求职信息，生成职位搜索URL
    Args:
        except_job (dict): 包含求职信息的字典，格式为:
            {
                "job": str,         # 职位名称，如"大模型算法工程师"
            }
        city (str): 城市编码，默认全国
        position (str): 职位编码，默认大模型算法岗位
        jobType (str): 工作类型编码，默认全职
    Returns:
        str: 生成的职位搜索URL
    """

    # 从except_job字典中提取各字段，默认为"不限"
    job = except_job.get("job", "")

    position = job_dict.get(job)

    # 构建基础URL
    url = f"https://www.zhipin.com/web/geek/jobs?city={city}&position={position}&jobType={jobType}"

    return url


def get_job_details(
    url: str,
    max_count: int = 200,
    max_retries: int = 3,
    min_description_length: int = 200,
    output_dir: str = "jobs/101310",
) -> str:
    """
    抓取职位搜索页面中的职位详情（使用Playwright同步实现，支持已登录状态）

    Args:
        url: 职位搜索页面URL
        max_count: 需要抓取的职位数量
        max_retries: 页面加载重试次数
        min_description_length: 岗位描述最小字数，小于此字数的岗位将被过滤
        output_dir: 输出目录
    """

    login_data_dir = os.getenv("JOB_CRAWL_USER_DATA_DIR", "./user_data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/job_details_{int(time.time())}.csv"

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

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch_persistent_context(
            user_data_dir=login_data_dir,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        browser_page = browser.new_page()

        captured_responses = []

        # 响应拦截器
        def handle_response(response):
            if "job/detail.json" in response.url:
                try:
                    _parse_response(response, captured_responses)
                except Exception as e:
                    print(f"解析响应失败: {e}")

        browser_page.on("response", handle_response)

        # 禁用自动化特征
        browser_page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
        """)

        # 页面加载重试逻辑
        for attempt in range(max_retries):
            try:
                browser_page.goto("https://www.baidu.com", timeout=60000)
                browser_page.goto(url, timeout=60000, wait_until="domcontentloaded")
                browser_page.wait_for_selector(".job-info", timeout=30000)
                browser_page.wait_for_timeout(1000)
                break
            except PlaywrightTimeoutError:
                if attempt == max_retries - 1:
                    raise Exception(f"经过{max_retries}次尝试后仍无法加载页面")
                print(f"页面加载超时，正在进行第{attempt + 2}次重试...")
                browser_page.reload(timeout=60000)

        count = 0
        valid_count = 0  # 有效岗位计数（满足字数要求）
        filtered_count = 0  # 被过滤的岗位计数
        filtered_english_count = 0  # 英文JD过滤计数
        page_num = 1
        pbar = None
        jobs_buffer = []

        try:
            pbar = tqdm(total=max_count, desc="抓取岗位中")

            # 循环翻页直到抓取到足够的岗位
            while valid_count < max_count:
                # 先滚动15次加载足够的岗位（按照原来crawler.py的逻辑）
                pbar.write(f"📄 第{page_num}页：正在滚动加载岗位...")
                last_height = browser_page.evaluate("document.body.scrollHeight")
                for scroll_count in range(5):  # 滚动5次
                    browser_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    browser_page.wait_for_timeout(800)
                    new_height = browser_page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        pbar.write(f"   已滚动{scroll_count + 1}次，页面高度不再变化")
                        break
                    last_height = new_height
                else:
                    pbar.write("   已完成5次滚动")

                # 获取岗位卡片
                cards = browser_page.locator(".job-info").all()

                if len(cards) == 0:
                    pbar.write(f"⚠️ 第{page_num}页没有找到岗位卡片，可能已到最后一页")
                    break

                pbar.write(f"📄 第{page_num}页发现 {len(cards)} 个岗位卡片")

                # 处理当前页的岗位
                for card in cards:
                    if valid_count >= max_count:
                        break

                    try:
                        captured_responses.clear()
                        card.scroll_into_view_if_needed()
                        card.click()

                        # 等待响应捕获
                        wait_time = 0
                        max_wait = 3
                        while len(captured_responses) == 0 and wait_time < max_wait:
                            browser_page.wait_for_timeout(200)
                            wait_time += 0.2

                        if len(captured_responses) == 0:
                            pbar.write("⚠️ 未捕获到职位详情响应，跳过该职位")
                            continue

                        # 解析职位数据
                        json_data = captured_responses[0]
                        zp_data = json_data.get("zpData", {})
                        job_info = zp_data.get("jobInfo", {})
                        brand_com_info = zp_data.get("brandComInfo", {})

                        job_description = job_info.get("postDescription", "").strip()

                        # 过滤1：岗位描述字数小于指定长度的跳过
                        if len(job_description) < min_description_length:
                            filtered_count += 1
                            pbar.write(
                                f"⏭️  过滤(字数): {job_info.get('jobName', '')} - {brand_com_info.get('brandName', '')} "
                                f"(描述仅{len(job_description)}字，小于{min_description_length}字)"
                            )
                            browser_page.wait_for_timeout(300)
                            continue

                        # 过滤2：英文JD（判断英文字符占比）
                        english_chars = sum(1 for c in job_description if c.isascii() and c.isalpha())
                        total_chars = len(job_description)
                        english_ratio = english_chars / total_chars if total_chars > 0 else 0

                        # 如果英文字符占比超过30%，认为是英文JD
                        if english_ratio > 0.3:
                            filtered_english_count += 1
                            pbar.write(
                                f"⏭️  过滤(英文): {job_info.get('jobName', '')} - {brand_com_info.get('brandName', '')} "
                                f"(英文占比{english_ratio:.1%})"
                            )
                            browser_page.wait_for_timeout(300)
                            continue

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
                            "岗位描述": job_description,
                        }

                        # 添加到缓冲区
                        jobs_buffer.append(job_data)
                        valid_count += 1
                        count += 1

                        pbar.update(1)
                        pbar.write(
                            f"✅ [{valid_count}/{max_count}] {job_data['职位名称']} - {job_data['公司名称']} "
                            f"(描述{len(job_description)}字)"
                        )

                        browser_page.wait_for_timeout(500)

                    except Exception as e:
                        pbar.write(f"❌ 处理职位时出错: {str(e)}")

                # 如果已经抓取到足够的岗位，退出循环
                if valid_count >= max_count:
                    break

                # 尝试翻页
                try:
                    # 查找下一页按钮
                    next_button = browser_page.locator(".options-pages a.next")

                    # 检查下一页按钮是否存在且可点击
                    if next_button.count() > 0:
                        # 检查是否被禁用
                        is_disabled = next_button.get_attribute("class")
                        if is_disabled and "disabled" in is_disabled:
                            pbar.write("📄 已到最后一页，无法继续翻页")
                            break

                        pbar.write(f"📄 正在翻到第{page_num + 1}页...")
                        next_button.click()
                        browser_page.wait_for_timeout(2000)
                        page_num += 1
                    else:
                        pbar.write("📄 未找到下一页按钮，可能已到最后一页")
                        break

                except Exception as e:
                    pbar.write(f"⚠️ 翻页失败: {str(e)}")
                    break

            # 写入所有数据
            if jobs_buffer:
                with open(output_path, "a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=jobs_buffer[0].keys())
                    writer.writerows(jobs_buffer)
                print(f"\n💾 已写入 {len(jobs_buffer)} 条职位数据")
                print(f"📊 统计: 有效岗位 {valid_count} 个，过滤岗位 {filtered_count + filtered_english_count} 个")
                print(f"   - 字数不足过滤: {filtered_count} 个")
                print(f"   - 英文JD过滤: {filtered_english_count} 个")
            else:
                print("\n⚠️ 未抓取到任何职位数据")

        finally:
            # 关闭进度条
            if pbar is not None:
                try:
                    pbar.close()
                except Exception:
                    pass
            # 确保浏览器关闭
            browser.close()

    print(f"✅ 已获取职位数据，保存路径: {output_path}")
    return output_path


# 解析响应的辅助函数
def _parse_response(response, captured_responses):
    try:
        data = response.json()
        captured_responses.append(data)
    except Exception as e:
        print(f"解析响应失败: {e}")


def parse_job_names(raw_jobs: str) -> list[str]:
    if not raw_jobs:
        return list(job_dict.keys())

    names = [name.strip() for name in raw_jobs.split(",") if name.strip()]
    unknown = [name for name in names if name not in job_dict]
    if unknown:
        raise ValueError(f"Unknown job names: {', '.join(unknown)}")

    return names


def append_csv_to_jsonl(csv_path: Path, combined_file, job_name: str, job_code: str) -> int:
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["job_category"] = job_name
            row["job_code"] = job_code
            combined_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


async def crawl_jobs(
    job_names: list[str],
    output_dir: Path,
    combined_path: Path,
    max_count: int,
    min_description_length: int,
    city: str,
    job_type: str,
    append: bool,
) -> None:
    mode = "a" if append else "w"
    with open(combined_path, mode, encoding="utf-8") as combined_file:
        for job_name in job_names:
            job_code = job_dict[job_name]
            print(f"\n=== Crawling {job_name} ({job_code}) ===")

            url = get_job_url({"job": job_name}, city=city, jobType=job_type)
            job_output_dir = output_dir / job_code

            try:
                csv_path = await get_job_details(
                    url=url,
                    max_count=max_count,
                    min_description_length=min_description_length,
                    output_dir=str(job_output_dir),
                )
            except Exception as exc:
                print(f"Failed to crawl {job_name}: {exc}")
                continue

            if not csv_path or not Path(csv_path).exists():
                print(f"No output generated for {job_name}")
                continue

            appended = append_csv_to_jsonl(Path(csv_path), combined_file, job_name, job_code)
            print(f"Added {appended} rows to {combined_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline crawl jobs and build a JSONL dataset.")
    parser.add_argument("--jobs", help="Comma-separated job names from tools/mappings.py")
    parser.add_argument("--max-count", type=int, default=50)
    parser.add_argument("--min-description-length", type=int, default=200)
    parser.add_argument("--city", default="100010000")
    parser.add_argument("--job-type", default="1901")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--combined-path", default=str(DEFAULT_COMBINED_PATH))
    parser.add_argument("--append", action="store_true", help="Append to combined JSONL instead of overwrite")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    os.environ.setdefault("JOB_CRAWL_USER_DATA_DIR", str(ROOT_DIR / "backend" / "user_data"))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_path = Path(args.combined_path)
    combined_path.parent.mkdir(parents=True, exist_ok=True)

    job_names = parse_job_names(args.jobs)

    crawl_jobs(
        job_names=job_names,
        output_dir=output_dir,
        combined_path=combined_path,
        max_count=args.max_count,
        min_description_length=args.min_description_length,
        city=args.city,
        job_type=args.job_type,
        append=args.append,
    )


if __name__ == "__main__":
    main()
