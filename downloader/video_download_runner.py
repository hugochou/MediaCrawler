import asyncio
import os
from typing import Optional, List, Dict, Any, Tuple
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright, Cookie

import config
from tools import utils
from tools.cdp_browser import CDPBrowserManager
from constant.platform_map import PLATFORM_MODULE_MAP, PLATFORM_CLASS_NAME_MAP # 导入平台模块映射和类名映射
import importlib # 导入 importlib 用于动态导入

class VideoDownloadRunner:
    def __init__(self):
        pass

    async def _get_downloader_class(self, platform: str):
        """
        根据平台名称动态获取对应的下载器类。
        """
        module_name = PLATFORM_MODULE_MAP.get(platform)
        class_base_name = PLATFORM_CLASS_NAME_MAP.get(platform)

        if not module_name or not class_base_name:
            utils.logger.error(f"[VideoDownloadRunner] 不支持的下载平台或配置缺失: {platform}")
            raise ValueError(f"Unsupported download platform or missing configuration: {platform}")

        full_module_path = f"downloader.{module_name}_downloader"
        downloader_class_name = f"{class_base_name}Downloader"

        try:
            module = importlib.import_module(full_module_path)
            downloader_class = getattr(module, downloader_class_name)
            return downloader_class
        except (ImportError, AttributeError) as e:
            utils.logger.error(f"[VideoDownloadRunner] 无法动态加载 {platform} 下载器类 {downloader_class_name} 从 {full_module_path}: {e}")
            raise ImportError(f"Failed to load downloader for {platform}: {str(e)}")

    async def run_download(self, platform: str, url: str) -> dict:
        """
        根据平台动态创建并运行对应的视频下载器。
        :param platform: 平台名称 (e.g., 'douyin', 'bili')
        :param url: 视频分享链接或详情页链接
        :return: 包含下载状态和文件路径的字典
        """
        utils.logger.info(f"[VideoDownloadRunner] 开始为平台 {platform} 下载视频: {url}")
        
        try:
            # 1. 根据平台获取对应的下载器类
            downloader_class = await self._get_downloader_class(platform)

            # 2. 实例化下载器并调用其start方法来启动下载流程（包括登录和获取cookies）
            downloader_obj = downloader_class()
            download_result = await downloader_obj.start(url, platform) # 调用下载器的start方法，并传递 platform
            utils.logger.info(f"[VideoDownloadRunner] {platform} 视频下载完成，结果: {download_result}")
            return download_result
        except Exception as e:
            utils.logger.error(f"[VideoDownloadRunner] 调用 {platform} 下载器失败: {e}")
            return {"status": "error", "message": f"Failed to call {platform} downloader: {str(e)}"}
