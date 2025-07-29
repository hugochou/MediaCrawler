# api_server.py
# 此文件作为 Flask Web API 服务器，接收 n8n 的 HTTP 请求并调用 MediaCrawler 爬虫。

from flask import Flask, request, jsonify
import asyncio
import sys
import os
from typing import Optional, Dict, Tuple

# 导入上面创建的 MediaCrawler 运行器
from mediacrawler_runner import MediacrawlerApiRunner
from downloader.video_download_runner import VideoDownloadRunner # 导入视频下载runner

# 导入config模块以获取配置，如SAVE_LOGIN_STATE, USER_DATA_DIR, HEADLESS等
import config 
from tools import utils # 导入工具函数，如convert_cookies

app = Flask(__name__)
runner = MediacrawlerApiRunner() # 实例化爬虫运行器
video_download_runner = VideoDownloadRunner() # 实例化视频下载runner

@app.route('/crawl', methods=['POST'])
async def handle_crawl_request():
    """
    处理来自 n8n 的爬取请求。
    期望接收一个 JSON 请求体，包含 'platform', 'type' (search/detail),
    以及 'keywords' 或 'detail_ids' 等参数。
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # 从请求体中解析参数
    platform = data.get('platform')
    crawl_type = data.get('type') # 'search' or 'detail'
    login_type = data.get('login_type', 'qrcode') # 默认为 qrcode
    save_data_option = data.get('save_data_option') # e.g., "sqlite", "db"
    keywords = data.get('keywords') # 列表，用于 search 类型
    detail_ids = data.get('detail_ids') # 列表，用于 detail 类型
    enable_get_comments = data.get('enable_get_comments') # 布尔值，是否获取评论

    # 基本参数校验
    if not platform:
        return jsonify({"error": "Missing 'platform' parameter."}), 400
    if not crawl_type or crawl_type not in ["search", "detail"]:
        return jsonify({"error": "Invalid or missing 'type' parameter. Must be 'search' or 'detail'."}), 400
    if crawl_type == "search" and not keywords:
        return jsonify({"error": "For 'search' type, 'keywords' (list of strings) is required."}), 400
    if crawl_type == "detail" and not detail_ids:
        return jsonify({"error": "For 'detail' type, 'detail_ids' (list of strings) is required."}), 400

    try:
        # 调用 MediacrawlerApiRunner 中的异步爬取函数
        # Flask 2.0+ 支持 async def 路由，可以直接 await 异步任务。
        result = await runner.run_crawl(
            platform=platform,
            crawl_type=crawl_type,
            login_type=login_type,
            save_data_option=save_data_option,
            keywords=keywords,
            detail_ids=detail_ids,
            enable_get_comments=enable_get_comments
            # 可以通过 'kwargs' 参数传递更多 config 参数，例如：
            # MAX_CONCURRENT_REQUESTS=data.get('max_concurrent_requests')
        )
        return jsonify(result), 200

    except ValueError as e:
        # 参数验证失败或业务逻辑错误
        print(f"Client error: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        # 捕获未知错误
        print(f"Internal server error: {e}", file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"An internal server error occurred: {str(e)}",
            "details": str(e) # 调试时显示细节，生产环境请移除或精简
        }), 500


@app.route('/download/video', methods=['POST'])
async def download_video_api():
    """
    通过分享链接下载视频，支持所有平台。
    期望接收一个 JSON 请求体，包含 'share_url' 和 'platform' 参数。
    """
    data = request.get_json()

    if not data or 'share_url' not in data or 'platform' not in data:
        return jsonify({"error": "请求体必须是JSON，并且包含 'share_url' 和 'platform' 参数。"}), 400

    share_url = data.get('share_url')
    platform = data.get('platform', config.PLATFORM) # 如果未提供，则从config中获取

    if not share_url:
        return jsonify({"error": "'share_url' 不能为空。"}), 400
    if not platform:
        return jsonify({"error": "'platform' 不能为空。请在请求中指定平台或在config中设置默认平台。"}), 400

    try:
        # 直接调用 video_download_runner 的 run_download 方法
        result = await video_download_runner.run_download(platform, share_url)
        
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"{platform} 视频下载API发生错误: {e}", file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"视频下载过程中发生内部服务器错误: {str(e)}",
            "details": str(e)
        }), 500
    finally:
        # video_download_runner 内部已负责关闭浏览器上下文，此处无需额外关闭
        pass


if __name__ == '__main__':
    # 确保 Flask API 服务器监听在 0.0.0.0，以便 Docker 容器可以访问。
    # 端口可以自由选择，例如 6600 。
    print("在 http://0.0.0.0:6600 启动 Flask API 服务器")
    app.run(host='0.0.0.0', port=6600, debug=True) # debug=True 用于开发调试
