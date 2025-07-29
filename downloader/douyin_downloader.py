import asyncio
import os
from typing import List, Optional, Dict, Any, Tuple
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright, BrowserType

import config
from tools import utils
from tools.cdp_browser import CDPBrowserManager
from media_platform.douyin.login import DouYinLogin # 直接导入DouYinLogin，避免循环依赖
from proxy.proxy_ip_pool import create_ip_pool, IpInfoModel
from downloader.video_downloader import VideoDownloader
from constant.platform_map import PLATFORM_MODULE_MAP # 导入平台模块映射

class DouyinDownloader:
    context_page: Page
    browser_context: BrowserContext
    cdp_manager: Optional[CDPBrowserManager]

    def __init__(self):
        self.video_downloader = VideoDownloader()
        self.index_url = "https://www.douyin.com"
        self.cdp_manager = None

    async def start(self, url: str, platform: str) -> dict: # 添加 platform 参数
        """
        启动抖音下载器，包括浏览器启动、登录和视频下载。
        :param url: 抖音分享链接或视频详情页链接。
        :param platform: 平台名称 (e.g., 'dy')
        :return: 包含下载状态和文件路径的字典。
        """
        utils.logger.info(f"[DouyinDownloader] 开始处理抖音视频下载: {url}")

        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(
                config.IP_PROXY_POOL_COUNT, enable_validate_ip=True
            )
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(
                ip_proxy_info
            )

        try:
            async with async_playwright() as playwright:
                # 根据配置选择启动模式
                if config.ENABLE_CDP_MODE:
                    utils.logger.info("[DouyinDownloader] 使用CDP模式启动浏览器进行登录")
                    self.browser_context = await self.launch_browser_with_cdp(
                        playwright,
                        playwright_proxy_format,
                        None,
                        headless=config.CDP_HEADLESS,
                    )
                else:
                    utils.logger.info("[DouyinDownloader] 使用标准模式启动浏览器进行登录")
                    chromium = playwright.chromium
                    self.browser_context = await self.launch_browser(
                        chromium,
                        playwright_proxy_format,
                        user_agent=None,
                        headless=config.HEADLESS,
                    )
                
                # 添加反检测脚本
                await self.browser_context.add_init_script(path="libs/stealth.min.js")
                self.context_page = await self.browser_context.new_page()
                
                # 导航到抖音首页
                utils.logger.info(f"[DouyinDownloader] 导航到抖音首页: {self.index_url}")
                await self.context_page.goto(self.index_url)
                # 移除 wait_for_loadstate，依赖 DouYinLogin 内部的等待机制

                # 检查登录状态并执行登录流程
                # 这里直接使用DouYinLogin，因为DouyinDownloader是抖音专用的
                login_obj = DouYinLogin(
                    login_type=config.LOGIN_TYPE,
                    login_phone="",
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES,
                )
                
                utils.logger.info("[DouyinDownloader] 检查初始登录状态...")
                if not await login_obj.check_login_state():
                    utils.logger.info("[DouyinDownloader] 未检测到有效登录状态，开始登录流程...")
                    await login_obj.begin()
                    # 登录后再次检查状态
                    if not await login_obj.check_login_state():
                        utils.logger.error("[DouyinDownloader] 登录失败或登录状态无效，无法获取有效cookies。")
                        return {"status": "error", "message": "Login failed or invalid login state."}
                else:
                    utils.logger.info("[DouyinDownloader] 已检测到有效登录状态，跳过登录流程。")

                # 获取最终的cookies
                cookies_list = await self.browser_context.cookies()
                utils.logger.info("[DouyinDownloader] 已获取到有效的抖音cookies。")
                
                # 直接调用视频下载器进行下载，使用转换后的平台名称
                platform_module_name = PLATFORM_MODULE_MAP.get(platform, "douyin") # 获取正确的平台模块名称
                download_result = await self.video_downloader.download_video(url, platform_module_name, cookies_list)
                return download_result

        except Exception as e:
            utils.logger.error(f"[DouyinDownloader] 抖音视频下载失败: {e}")
            return {"status": "error", "message": f"Douyin video download failed: {str(e)}"}
        finally:
            await self.close() # 确保浏览器上下文被关闭

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """
        启动浏览器并创建浏览器上下文。
        """
        if config.SAVE_LOGIN_STATE:
            user_data_dir = os.path.join(
                os.getcwd(), "browser_data", config.USER_DATA_DIR % config.PLATFORM
            )
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent,
            )
            return browser_context
        else:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}, user_agent=user_agent
            )
            return browser_context

    async def launch_browser_with_cdp(
        self,
        playwright: Playwright,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """
        使用CDP模式启动浏览器。
        """
        try:
            self.cdp_manager = CDPBrowserManager()
            browser_context = await self.cdp_manager.launch_and_connect(
                playwright=playwright,
                playwright_proxy=playwright_proxy,
                user_agent=user_agent,
                headless=headless,
            )

            # 添加反检测脚本
            await self.cdp_manager.add_stealth_script()

            # 显示浏览器信息
            browser_info = await self.cdp_manager.get_browser_info()
            utils.logger.info(f"[DouyinDownloader] CDP浏览器信息: {browser_info}")

            return browser_context

        except Exception as e:
            utils.logger.error(f"[DouyinDownloader] CDP模式启动失败，回退到标准模式: {e}")
            # 回退到标准模式
            chromium = playwright.chromium
            return await self.launch_browser(
                chromium, playwright_proxy, user_agent, headless
            )

    async def close(self) -> None:
        """
        关闭浏览器上下文。
        """
        if self.cdp_manager:
            await self.cdp_manager.cleanup()
            self.cdp_manager = None
        else:
            if self.browser_context:
                await self.browser_context.close()
        utils.logger.info("[DouyinDownloader.close] 浏览器上下文已关闭。")

    @staticmethod
    def format_proxy_info(
        ip_proxy_info: IpInfoModel,
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        格式化代理信息，用于Playwright和httpx。
        """
        playwright_proxy = {
            "server": f"{ip_proxy_info.protocol}{ip_proxy_info.ip}:{ip_proxy_info.port}",
            "username": ip_proxy_info.user,
            "password": ip_proxy_info.password,
        }
        httpx_proxy = {
            f"{ip_proxy_info.protocol}": f"http://{ip_proxy_info.user}:{ip_proxy_info.password}@{ip_proxy_info.ip}:{ip_proxy_info.port}"
        }
        return playwright_proxy, httpx_proxy
