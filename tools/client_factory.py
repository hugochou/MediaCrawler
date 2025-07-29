import os
from typing import Optional, Dict
from playwright.async_api import BrowserContext, Page

import config
from media_platform.douyin.client import DOUYINClient
from tools import utils

async def create_douyin_client(
    browser_context: BrowserContext,
    context_page: Page,
    httpx_proxy: Optional[str]
) -> DOUYINClient:
    """
    创建抖音客户端。
    此方法从浏览器上下文和页面获取必要的cookies和User-Agent，
    并初始化DOUYINClient实例。
    """
    cookie_str, cookie_dict = utils.convert_cookies(await browser_context.cookies())
    user_agent = await context_page.evaluate("() => navigator.userAgent")

    douyin_client = DOUYINClient(
        proxies=httpx_proxy,
        headers={
            "User-Agent": user_agent,
            "Cookie": cookie_str,
            "Host": "www.douyin.com",
            "Origin": "https://www.douyin.com/",
            "Referer": "https://www.douyin.com/",
            "Content-Type": "application/json;charset=UTF-8",
        },
        playwright_page=context_page,
        cookie_dict=cookie_dict,
    )
    return douyin_client
