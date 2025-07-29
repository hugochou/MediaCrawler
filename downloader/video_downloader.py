import asyncio
import os
from typing import List, Optional, Dict, Any
from yt_dlp import YoutubeDL
from tools import utils

class VideoDownloader:
    def __init__(self):
        # Base configuration for yt-dlp
        self.base_ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4', # Prioritize mp4 format and merge audio/video
            'outtmpl': os.path.join('data', '%(extractor)s', 'videos', '%(id)s.%(ext)s'), # Output path and filename template
            'noplaylist': True, # Do not download playlists
            'quiet': True, # Do not print verbose information
            'no_warnings': True, # Do not print warnings
            'merge_output_format': 'mp4', # Merged format
            'cookiefile': None, # Default to no cookie file
        }

    async def download_video(self, url: str, platform: str, cookies_list: Optional[List[Dict[str, Any]]] = None) -> dict:
        """
        Downloads a video using yt-dlp, supporting various platforms.
        :param url: The share link or video detail page link.
        :param platform: The platform name (e.g., 'douyin', 'bilibili').
        :param cookies_list: Optional list of Playwright Cookie objects (dictionaries).
        :return: A dictionary containing download status and file path.
        """
        current_ydl_opts = self.base_ydl_opts.copy()
        
        # Customize output directory based on platform
        current_ydl_opts['outtmpl'] = os.path.join('data', platform, 'videos', '%(id)s.%(ext)s')

        temp_cookie_file = None
        if cookies_list:
            try:
                netscape_cookies = ["# Netscape HTTP Cookie File"]
                for cookie in cookies_list:
                    domain = cookie.get('domain', '')
                    domain_specified_flag = "TRUE" if domain.startswith('.') else "FALSE"
                    path = cookie.get('path', '/')
                    secure = "TRUE" if cookie.get('secure') else "FALSE"
                    # 处理 expires 为 -1 的情况，将其设置为一个未来的时间戳
                    expires_timestamp = int(cookie.get('expires', 0))
                    if expires_timestamp == -1:
                        # 设置为当前时间 + 10年，确保yt-dlp不会跳过
                        expiration = str(int(asyncio.get_event_loop().time()) + 10 * 365 * 24 * 60 * 60)
                    else:
                        expiration = str(expires_timestamp)
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    
                    netscape_cookies.append(f"{domain}\t{domain_specified_flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
                
                netscape_cookies_str = "\n".join(netscape_cookies)

                temp_cookie_file = f"temp_{platform}_cookies.txt"
                with open(temp_cookie_file, "w") as f:
                    f.write(netscape_cookies_str)
                current_ydl_opts['cookiefile'] = temp_cookie_file
            except Exception as e:
                print(f"Failed to write temporary cookie file for {platform}: {e}")
                temp_cookie_file = None

        try:
            # Ensure download directory exists
            download_dir = os.path.join('data', platform, 'videos')
            os.makedirs(download_dir, exist_ok=True)

            with YoutubeDL(current_ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                print(f"Video downloaded successfully for {platform}: {filepath}")
                return {
                    "status": "success",
                    "message": f"{platform} video downloaded successfully.",
                    "download_path": filepath,
                    "video_id": info.get('id'),
                    "title": info.get('title'),
                    "extractor": info.get('extractor')
                }
        except Exception as e:
            print(f"Error downloading video for {platform} with yt-dlp: {e}")
            return {
                "status": "error",
                "message": f"Failed to download video for {platform} with yt-dlp: {str(e)}"
            }
        finally:
            if temp_cookie_file and os.path.exists(temp_cookie_file):
                os.remove(temp_cookie_file)
