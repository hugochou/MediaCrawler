# mediacrawler_runner.py
# 此文件用于封装 MediaCrawler 的核心运行逻辑，使其可通过函数调用，并动态传递参数。

import asyncio
import sys
import os
from typing import Optional, List, Dict, Any, Tuple

# 导入 MediaCrawler 的核心组件
# 确保此脚本在 MediaCrawler 项目根目录中运行，以便正确导入相对路径的模块
import config # 导入 config 模块 (包含 base_config)
from base.base_crawler import AbstractCrawler
from media_platform.douyin.client import DOUYINClient
import db
from tools import utils
from constant.platform_map import PLATFORM_CRAWLERS_MAP # 导入平台爬虫映射

# 定义一个类来管理爬虫的创建和运行，类似于 main.py 中的 CrawlerFactory
class MediacrawlerApiRunner:
    CRAWLERS = PLATFORM_CRAWLERS_MAP

    def __init__(self):
        self._crawler: Optional[AbstractCrawler] = None
        # 存储原始 config 值，以便在爬取结束后恢复（重要，特别是如果 API 是异步处理请求）
        self._original_config_values = {}

    async def run_crawl(self,
                        platform: str,
                        crawl_type: str, # "search" or "detail"
                        login_type: str = "qrcode", # 登录方式，如 "qrcode", "cookie"
                        save_data_option: Optional[str] = None, # "sqlite", "db", or None（不保存）
                        keywords: Optional[List[str]] = None, # 关键词列表，用于 "search" 类型
                        detail_ids: Optional[List[str]] = None, # 帖子 ID 列表，用于 "detail" 类型
                        enable_get_comments: Optional[bool] = None, # 是否开启评论爬取
                        **kwargs: Any # 接收其他可能需要的 config 参数
                        ) -> Dict[str, Any]:
        """
        根据传入的参数运行 MediaCrawler。
        此函数会临时修改 MediaCrawler 内部的全局 config 变量。
        """
        # --- 1. 备份原始 config 值 (重要：为了防止并发请求导致配置混乱) ---
        # 确保你在调用此函数之前，或其他请求不会同时修改这些全局配置。
        # 如果是单线程阻塞式 API，问题不大；但如果是异步或并发 API，需要更严格的隔离。
        # 这里只是一个简单的备份和恢复机制。
        for attr in ['PLATFORM', 'LOGIN_TYPE', 'SAVE_DATA_OPTION', 'KEYWORD_LIST', 'DETAIL_ID_LIST', 'ENABLE_GET_COMMENTS', 'TYPE']:
            if hasattr(config, attr):
                # 对列表进行深拷贝以避免引用问题
                if isinstance(getattr(config, attr), list):
                    self._original_config_values[attr] = getattr(config, attr).copy()
                else:
                    self._original_config_values[attr] = getattr(config, attr)
            else:
                self._original_config_values[attr] = None # Or a default value if not present

        # --- 2. 设置新的 config 参数 ---
        config.PLATFORM = platform
        config.LOGIN_TYPE = login_type
        # config.TYPE 这个变量通常在 cmd_arg.parse_cmd() 中设置，
        # 在这里我们直接赋值给 config 模块确保生效。
        setattr(config, 'TYPE', crawl_type) # 确保 config.TYPE 存在并被设置

        if save_data_option:
            config.SAVE_DATA_OPTION = save_data_option
        else:
            # 如果不指定保存选项，可以设置为不保存，或让 MediaCrawler 默认处理
            config.SAVE_DATA_OPTION = 'no_save' # 或您可以设置为 None

        if enable_get_comments is not None:
            config.ENABLE_GET_COMMENTS = enable_get_comments

        if crawl_type == "search":
            if keywords:
                config.KEYWORD_LIST = keywords
            else:
                raise ValueError("`keywords` is required for 'search' type.")
            config.DETAIL_ID_LIST = [] # 清空 detail ID 列表
        elif crawl_type == "detail":
            if detail_ids:
                config.DETAIL_ID_LIST = detail_ids
            else:
                raise ValueError("`detail_ids` is required for 'detail' type.")
            config.KEYWORD_LIST = [] # 清空关键词列表
        else:
            raise ValueError(f"Invalid `type`: {crawl_type}. Must be 'search' or 'detail'.")

        # 处理其他通过 kwargs 传入的 config 参数（如果有的话）
        for key, value in kwargs.items():
            # 尝试设置到 config 模块，假设 config 名称是大写
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
            elif hasattr(config.base_config, key.upper()): # 也检查 base_config
                setattr(config.base_config, key.upper(), value)
            # else: 可以选择抛出错误或打印警告，表示未知参数

        # --- 3. 初始化数据库 ---
        if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
            try:
                print(f"Initializing database with option: {config.SAVE_DATA_OPTION}")
                await db.init_db()
                print("Database initialized.")
            except Exception as e:
                print(f"Error initializing database: {e}", file=sys.stderr)
                raise # 如果数据库初始化失败，则阻止爬取并报告错误

        # --- 4. 创建并启动爬虫 ---
        try:
            crawler_class = self.CRAWLERS.get(platform)
            if not crawler_class:
                supported_platforms = ", ".join(self.CRAWLERS.keys())
                raise ValueError(f"无效的媒体平台: {platform}。支持的平台有: {supported_platforms}")
            
            # 类型断言，帮助IDE识别 _crawler 的具体类型
            self._crawler: AbstractCrawler = crawler_class()
            print(f"Starting crawl for platform: {platform}, type: {crawl_type}...")
            await self._crawler.start()
            print("Crawl finished.")

            # --- 5. 返回结果 ---
            # 重要：MediaCrawler 默认将数据保存到数据库或文件。
            # 此 API 层默认不从数据库读取数据并返回。
            # 如果您需要将爬取的数据直接返回给 n8n，您需要在 MediaCrawler 内部
            # 或在此处增加逻辑，从数据库中查询最新数据并序列化返回。
            # For simplicity, we just return status and parameters.
            return {
                "status": "success",
                "message": "MediaCrawler task initiated successfully.",
                "platform": platform,
                "type": crawl_type,
                "keywords": keywords if crawl_type == "search" else None,
                "detail_ids": detail_ids if crawl_type == "detail" else None,
                "save_data_option": config.SAVE_DATA_OPTION,
                # 您可以在这里添加更多关于保存路径或数据库的信息
            }

        except Exception as e:
            print(f"Error during crawl execution: {e}", file=sys.stderr)
            raise # 将错误向上抛出给 API 服务器处理

        finally:
            # --- 6. 清理和恢复原始 config 值 ---
            if self._crawler:
                pass # 根据 MediaCrawler 的设计，可能不需要显式关闭
            if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
                await db.close() # 关闭数据库连接
                print("Database connection closed.")

            # 恢复 config 变量到原始状态，避免影响后续请求
            for attr, original_value in self._original_config_values.items():
                if original_value is not None:
                    # 对于列表，确保是赋值新的列表对象，而不是引用
                    if isinstance(original_value, list):
                        setattr(config, attr, original_value.copy())
                    else:
                        setattr(config, attr, original_value)
