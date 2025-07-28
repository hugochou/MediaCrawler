# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  


import asyncio
import copy
import json
import urllib.parse
import random
from datetime import datetime
from typing import Any, Callable, Dict, Optional, List

import requests
from playwright.async_api import BrowserContext, Page
import config

from base.base_crawler import AbstractApiClient
from tools import utils
from var import request_keyword_var

from .exception import *
from .field import *
from .help import *


class DOUYINClient(AbstractApiClient):
    def __init__(
            self,
            timeout=30,
            proxies=None,
            *,
            headers: Dict,
            playwright_page: Optional[Page],
            cookie_dict: Dict
    ):
        self.proxies = proxies
        self.timeout = timeout
        self.headers = headers
        self._host = "https://www.douyin.com"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict
        # 解决 AttributeError: 'DOUYINClient' object has no attribute 'min_interval_time'
        # 使用 config 中的 CRAWLER_MAX_SLEEP_SEC，并设置一个默认的最小间隔时间
        self.min_interval_time = 1  # 默认最小间隔时间为1秒
        self.max_interval_time = config.CRAWLER_MAX_SLEEP_SEC # 从 config 获取最大间隔时间

    async def __process_req_params(
            self, uri: str, params: Optional[Dict] = None, headers: Optional[Dict] = None,
            request_method="GET"
    ):

        if not params:
            return
        headers = headers or self.headers
        local_storage: Dict = await self.playwright_page.evaluate("() => window.localStorage")  # type: ignore
        common_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "version_code": "190600",
            "version_name": "19.6.0",
            "update_version_code": "170400",
            "pc_client_type": "1",
            "cookie_enabled": "true",
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "125.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "os_name": "Mac OS",
            "os_version": "10.15.7",
            "cpu_core_num": "8",
            "device_memory": "8",
            "engine_version": "109.0",
            "platform": "PC",
            "screen_width": "2560",
            "screen_height": "1440",
            'effective_type': '4g',
            "round_trip_time": "50",
            "webid": get_web_id(),
            "msToken": local_storage.get("xmst"),
        }
        params.update(common_params)
        query_string = urllib.parse.urlencode(params)

        # 20240927 a-bogus更新（JS版本）
        post_data = {}
        if request_method == "POST":
            post_data = params
        a_bogus = await get_a_bogus(uri, query_string, post_data, headers["User-Agent"], self.playwright_page)
        params["a_bogus"] = a_bogus

    async def request(self, method, url, **kwargs):
        response = None
        if method == "GET":
            response = requests.request(method, url, **kwargs)
        elif method == "POST":
            response = requests.request(method, url, **kwargs)
        try:
            if response.text == "" or response.text == "blocked":
                utils.logger.error(f"request params incrr, response.text: {response.text}")
                raise Exception("account blocked")
            return response.json()
        except Exception as e:
            raise DataFetchError(f"{e}, {response.text}")

    async def get(self, uri: str, params: Optional[Dict] = None, headers: Optional[Dict] = None):
        """
        GET请求
        """
        await self.__process_req_params(uri, params, headers)
        headers = headers or self.headers
        return await self.request(method="GET", url=f"{self._host}{uri}", params=params, headers=headers)

    async def post(self, uri: str, data: dict, headers: Optional[Dict] = None):
        await self.__process_req_params(uri, data, headers)
        headers = headers or self.headers
        return await self.request(method="POST", url=f"{self._host}{uri}", data=data, headers=headers)

    async def pong(self, browser_context: BrowserContext) -> bool:
        local_storage = await self.playwright_page.evaluate("() => window.localStorage")
        if local_storage.get("HasUserLogin", "") == "1":
            return True

        _, cookie_dict = utils.convert_cookies(await browser_context.cookies())
        return cookie_dict.get("LOGIN_STATUS") == "1"

    async def update_cookies(self, browser_context: BrowserContext):
        cookie_str, cookie_dict = utils.convert_cookies(await browser_context.cookies())
        self.headers["Cookie"] = cookie_str
        self.cookie_dict = cookie_dict

    async def search_info_by_keyword(
            self,
            keyword: str,
            offset: int = 0,
            search_channel: SearchChannelType = SearchChannelType.GENERAL,
            sort_type: SearchSortType = SearchSortType.GENERAL,
            publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
            search_id: str = ""
    ):
        """
        DouYin Web Search API
        :param keyword:
        :param offset:
        :param search_channel:
        :param sort_type:
        :param publish_time: ·
        :param search_id: ·
        :return:
        """
        query_params = {
            'search_channel': search_channel.value,
            'enable_history': '1',
            'keyword': keyword,
            'search_source': 'tab_search',
            'query_correct_type': '1',
            'is_filter_search': '0',
            'from_group_id': '7378810571505847586',
            'offset': offset,
            'count': '15',
            'need_filter_settings': '1',
            'list_type': 'multi',
            'search_id': search_id,
        }
        if sort_type.value != SearchSortType.GENERAL.value or publish_time.value != PublishTimeType.UNLIMITED.value:
            query_params["filter_selected"] = json.dumps({
                "sort_type": str(sort_type.value),
                "publish_time": str(publish_time.value)
            })
            query_params["is_filter_search"] = 1
            query_params["search_source"] = "tab_search"
        referer_url = f"https://www.douyin.com/search/{keyword}?aid=f594bbd9-a0e2-4651-9319-ebe3cb6298c1&type=general"
        headers = copy.copy(self.headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=':/')
        return await self.get("/aweme/v1/web/general/search/single/", query_params, headers=headers)

    async def get_video_by_id(self, aweme_id: str) -> Any:
        """
        DouYin Video Detail API
        :param aweme_id:
        :return:
        """
        params = {
            "aweme_id": aweme_id
        }
        headers = copy.copy(self.headers)
        del headers["Origin"]
        res = await self.get("/aweme/v1/web/aweme/detail/", params, headers)
        return res.get("aweme_detail", {})

    async def get_aweme_comments(self, aweme_id: str, cursor: int = 0):
        """get note comments

        """
        uri = "/aweme/v1/web/comment/list/"
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": 20,
            "item_type": 0
        }
        keywords = request_keyword_var.get()
        referer_url = "https://www.douyin.com/search/" + keywords + '?aid=3a3cec5a-9e27-4040-b6aa-ef548c2c1138&publish_time=0&sort_type=0&source=search_history&type=general'
        headers = copy.copy(self.headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=':/')
        return await self.get(uri, params)

    async def get_sub_comments(self, aweme_id: str, comment_id: str, cursor: int = 0):
        """
            获取子评论
        """
        uri = "/aweme/v1/web/comment/list/reply/"
        params = {
            'comment_id': comment_id,
            "cursor": cursor,
            "count": 20,
            "item_type": 0,
            "item_id": aweme_id,
        }
        keywords = request_keyword_var.get()
        referer_url = "https://www.douyin.com/search/" + keywords + '?aid=3a3cec5a-9e27-4040-b6aa-ef548c2c1138&publish_time=0&sort_type=0&source=search_history&type=general'
        headers = copy.copy(self.headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=':/')
        return await self.get(uri, params)

    async def get_aweme_all_comments(
            self,
            aweme_id: str,
            crawl_interval: float = 1.0,
            is_fetch_sub_comments=False,
            callback: Optional[Callable] = None,
            max_count: int = 10,
    ):
        """
        获取帖子的所有评论，包括子评论
        :param aweme_id: 帖子ID
        :param crawl_interval: 抓取间隔
        :param is_fetch_sub_comments: 是否抓取子评论
        :param callback: 回调函数，用于处理抓取到的评论
        :param max_count: 一次帖子爬取的最大评论数量
        :return: 评论列表
        """
        result = []
        comments_has_more = 1
        comments_cursor = 0
        while comments_has_more and len(result) < max_count:
            comments_res = await self.get_aweme_comments(aweme_id, comments_cursor)
            comments_has_more = comments_res.get("has_more", 0)
            comments_cursor = comments_res.get("cursor", 0)
            comments = comments_res.get("comments", [])
            if not comments:
                continue
            if len(result) + len(comments) > max_count:
                comments = comments[:max_count - len(result)]
            result.extend(comments)
            if callback:  # 如果有回调函数，就执行回调函数
                await callback(aweme_id, comments)

            await asyncio.sleep(crawl_interval)
            if not is_fetch_sub_comments:
                continue
            # 获取二级评论
            for comment in comments:
                reply_comment_total = comment.get("reply_comment_total")

                if reply_comment_total > 0:
                    comment_id = comment.get("cid")
                    sub_comments_has_more = 1
                    sub_comments_cursor = 0

                    while sub_comments_has_more:
                        sub_comments_res = await self.get_sub_comments(aweme_id, comment_id, sub_comments_cursor)
                        sub_comments_has_more = sub_comments_res.get("has_more", 0)
                        sub_comments_cursor = sub_comments_res.get("cursor", 0)
                        sub_comments = sub_comments_res.get("comments", [])

                        if not sub_comments:
                            continue
                        result.extend(sub_comments)
                        if callback:  # 如果有回调函数，就执行回调函数
                            await callback(aweme_id, sub_comments)
                        await asyncio.sleep(crawl_interval)
        return result

    async def get_user_info(self, sec_user_id: str):
        uri = "/aweme/v1/web/user/profile/other/"
        params = {
            "sec_user_id": sec_user_id,
            "publish_video_strategy_type": 2,
            "personal_center_strategy": 1,
        }
        return await self.get(uri, params)

    async def get_user_aweme_posts(self, sec_user_id: str, max_cursor: str = "") -> Dict:
        uri = "/aweme/v1/web/aweme/post/"
        params = {
            "sec_user_id": sec_user_id,
            "count": 18,
            "max_cursor": max_cursor,
            "locate_query": "false",
            "publish_video_strategy_type": 2,
            'verifyFp': 'verify_ma3hrt8n_q2q2HyYA_uLyO_4N6D_BLvX_E2LgoGmkA1BU',
            'fp': 'verify_ma3hrt8n_q2q2HyYA_uLyO_4N6D_BLvX_E2LgoGmkA1BU'
        }
        return await self.get(uri, params)

    async def get_all_user_aweme_posts(self,
                                       sec_user_id: str,
                                       callback: Optional[Callable] = None,
                                       max_notes_count: int = 0,
                                       target_timestamp: Optional[int] = None
                                       ) -> List[Dict]:
        """
        Get all user aweme posts by sec_user_id
        Args:
            sec_user_id: user id
            callback: callback function
            max_notes_count: 最大爬取视频数量，0表示不限制 (如果target_timestamp设置，此参数将被忽略)
            target_timestamp: 目标日期（Unix时间戳）。程序会爬取该日期（含）之后发布的视频。
                              当出现非置顶视频在指定日期后发布，之后再出现视频在指定日期前发布时，将停止请求新的页面。
                              置顶视频即使发布时间早于目标日期，也会被跳过，但不触发停止条件。
        """
        posts_has_more = 1
        max_cursor = ""
        result = []  # 累计所有符合条件的视频
        current_crawl_count = 0

        # 新增的两个状态变量
        has_seen_new_video_this_user: bool = False  # 标志是否已见过日期符合的视频
        num_videos_processed_this_user: int = 0    # 统计已处理的视频总数（包括跳过的）
        # 假设最多3个置顶视频，设置一个略大于3的阈值，例如4，以确保跳过所有可能的置顶视频。
        STOP_THRESHOLD_FOR_INFERRED_PINNED_VIDEOS: int = 4

        while posts_has_more == 1:
            # 只有当没有设置 target_timestamp 时，才检查 max_notes_count
            if target_timestamp is None and max_notes_count > 0 and current_crawl_count >= max_notes_count:
                utils.logger.info(f"[DOUYINClient] Reached max notes count limit ({max_notes_count}) for user {sec_user_id}. Stopping new requests.")
                break

            aweme_post_res = await self.get_user_aweme_posts(sec_user_id, max_cursor)
            posts_has_more = aweme_post_res.get("has_more", 0)
            next_max_cursor = aweme_post_res.get("max_cursor")
            aweme_list = aweme_post_res.get("aweme_list") if aweme_post_res.get("aweme_list") else []

            if not aweme_list:
                utils.logger.info(f"[DOUYINClient] No more aweme_list for user {sec_user_id} in current response.")
                # 如果当前批次没有视频，但 has_more 仍为1，且游标未变，则可能已无更多内容，强制停止以防死循环
                if max_cursor == next_max_cursor and posts_has_more == 1:
                    utils.logger.warning(f"[DOUYINClient] Cursor did not advance but 'has_more' is still 1. Forcing stop for user {sec_user_id}.")
                posts_has_more = 0  # 停止后续页面的请求
                break  # 结束外层循环

            filtered_current_batch_videos = []
            should_stop_fetching_new_pages = False  # 标记是否需要停止外层循环（即停止请求新页面）

            for video_item in aweme_list:
                create_time = video_item.get("create_time")
                num_videos_processed_this_user += 1 # 无论视频是否符合日期，都增加计数

                if create_time is None:
                    utils.logger.warning(f"[DOUYINClient] Video ID {video_item.get('aweme_id')} has no create_time. Skipping.")
                    continue

                if target_timestamp is not None:
                    # 如果设置了目标日期，优先按日期过滤
                    if create_time >= target_timestamp:
                        # 视频的发布时间在新日期范围内或者就是目标日期
                        filtered_current_batch_videos.append(video_item)
                        current_crawl_count += 1
                        has_seen_new_video_this_user = True # 标记已见过新视频
                    else:
                        # 视频的发布时间早于目标日期 (即太旧了)
                        if has_seen_new_video_this_user and \
                           num_videos_processed_this_user > STOP_THRESHOLD_FOR_INFERRED_PINNED_VIDEOS:
                            # 已经见过新视频，并且处理的视频数量超过了预设的置顶视频阈值
                            # 这意味着当前这个旧视频不是置顶的，且出现在新视频之后，可以停止了。
                            utils.logger.info(
                                f"[DOUYINClient] Encountered an old video ({datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')}) "
                                f"after seeing newer videos and processing more than {STOP_THRESHOLD_FOR_INFERRED_PINNED_VIDEOS} videos ({num_videos_processed_this_user} total). "
                                f"Stopping further page requests for user {sec_user_id}."
                            )
                            should_stop_fetching_new_pages = True
                            break # 跳出内层循环，不再处理当前批次中该视频之后（更旧）的视频
                        else:
                            # 即使这个视频早于目标日期，
                            # 但如果还没见过新视频（可能在处理置顶视频），
                            # 或者还没处理足够数量的视频来排除置顶视频的可能性，
                            # 则跳过此视频（不抓取），但不停止爬取进程。
                            utils.logger.debug(
                                f"[DOUYINClient] Skipping presumed pinned/early old video {video_item.get('aweme_id')} "
                                f"(published {datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')}) as it is older than target date. "
                                f"has_seen_new_video_this_user={has_seen_new_video_this_user}, num_videos_processed_this_user={num_videos_processed_this_user}. "
                                f"Continuing to search for newer videos."
                            )
                            continue # 跳过此视频，处理当前批次的下一个视频

                else:  # target_timestamp 为 None，表示按数量限制爬取
                    if max_notes_count > 0 and current_crawl_count >= max_notes_count:
                        utils.logger.info(f"[DOUYINClient] Reached max notes count limit ({max_notes_count}) during batch processing for user {sec_user_id}. Stopping current batch.")
                        should_stop_fetching_new_pages = True
                        break  # 跳出内层循环

                    # 如果未达到数量限制，则添加到当前批次结果中
                    filtered_current_batch_videos.append(video_item)
                    current_crawl_count += 1

            # 对当前批次中筛选出的视频执行回调和结果累加
            if callback:
                await callback(filtered_current_batch_videos)
            result.extend(filtered_current_batch_videos)

            # 更新游标，准备请求下一页
            max_cursor = next_max_cursor

            # 如果在内层循环中设置了停止标志，则停止外层循环（即停止请求更多页面）
            if should_stop_fetching_new_pages:
                posts_has_more = 0  # 标记不再有更多页面
                break  # 结束外层循环

            # 添加一个随机延迟，避免触发限流
            await asyncio.sleep(random.uniform(self.min_interval_time, self.max_interval_time))

        return result