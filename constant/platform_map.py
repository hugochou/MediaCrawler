# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler

# PLATFORM_CRAWLERS_MAP:
# 将平台简称（如 "xhs", "dy"）映射到对应的爬虫类。
# 这个映射主要用于 mediacrawler_runner.py 中，根据配置的平台动态选择并实例化正确的爬虫。
# 这种设计提高了系统的可扩展性，使得添加新平台时无需修改核心运行逻辑。
PLATFORM_CRAWLERS_MAP = {
    "xhs": XiaoHongShuCrawler,
    "dy": DouYinCrawler,
    "ks": KuaishouCrawler,
    "bili": BilibiliCrawler,
    "wb": WeiboCrawler,
    "tieba": TieBaCrawler,
    "zhihu": ZhihuCrawler,
}

# PLATFORM_MODULE_MAP:
# 将平台简称映射到对应的 Python 模块名称字符串。
# 例如，"dy" 映射到 "douyin"，这意味着抖音相关的代码通常位于 `media_platform/douyin` 或 `downloader/douyin_downloader.py` 等模块中。
# 这个映射主要用于动态导入模块，例如在 video_download_runner.py 中根据平台名称动态加载下载器模块。
PLATFORM_MODULE_MAP = {
    "xhs": "xhs",
    "dy": "douyin",
    "ks": "kuaishou",
    "bili": "bilibili",
    "wb": "weibo",
    "tieba": "tieba",
    "zhihu": "zhihu",
}

# PLATFORM_CLASS_NAME_MAP:
# 将平台简称映射到对应的主要类名基础字符串。
# 例如，"dy" 映射到 "Douyin"，这通常用于构建完整的类名，如 "DouyinDownloader" 或 "DouyinClient"。
# 这个映射与 PLATFORM_MODULE_MAP 结合使用，在动态加载时用于通过字符串名称获取模块内的具体类。
PLATFORM_CLASS_NAME_MAP = {
    "xhs": "XiaoHongShu",
    "dy": "Douyin",
    "ks": "Kuaishou",
    "bili": "Bilibili",
    "wb": "Weibo",
    "tieba": "TieBa",
    "zhihu": "Zhihu",
}
