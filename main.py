import os
import re
import requests
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig
from astrbot.api import logger
from astrbot.api.event.filter import event_message_type, EventMessageType
from astrbot.api.message_components import *
from astrbot.api.message_components import Video

# 正则表达式模式
BILI_VIDEO_PATTERN = r"(https?:\/\/)?www\.bilibili\.com\/video\/(BV\w+|av\d+)\/?"

@register("bilibili_parse", "功德无量", "一个哔哩哔哩视频解析插件", "1.0.0")
class Bilibili(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def get(self, url):
        """发送 GET 请求并返回响应"""
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            return response.json()  # 返回 JSON 格式的响应
        except requests.RequestException as e:
            return None

    @staticmethod
    def get_file_size(self, size_in_bytes):
        """将字节转换为可读的文件大小格式"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        size = size_in_bytes

        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1

        return f"{size:.2f} {units[index]}"

    async def get_video_info(self, bvid: str, accept: int):
        """获取 Bilibili 视频信息"""
        quality_map = {
            '1080': 80,
            '720': 64,
            '480': 32,
            '360': 16,
        }

        qn = quality_map.get(accept, 80)  # 默认为 1080p
        
        try:
            json_data = await self.get(f'http://114.134.188.188:3003/api?bvid={bvid}&accept=80')
            if json_data is None or json_data['code'] != 0:
                return {'code': '-1', 'msg': "解析失败，参数可能不正确"}

            video_url = json_data['data'][0]['video_url']
            video_size = json_data['data'][0]['video_size']
            quality = json_data['data'][0]['accept_format']

            result = {
                'code': 0,
                'msg': '视频解析成功',
                'title': json_data['title'],
                'video_url': video_url,
                'pic': json_data['imgurl'],
                'video_size': video_size,
                'quality': quality,
                'comment': json_data['data'][0]['comment']
            }
            title = result['title']
            video_url = result['video_url']
            pic = result['pic']
            video_size = result['video_size']
            quality = result['quality']
            comment = result['comment']
            
            response_message = (
                f"🎬 标题: {title}\n"
                f"🔗 视频链接: {video_url}\n"
                f"🖼 视频封面: {pic}\n"
                f"📖 视频大小: {video_size}\n"
                f"👓 清晰度: {quality}\n"
                f"💬 弹幕链接: {comment}"
            )
            
            return response_message

        except requests.RequestException as e:
            return {'code': '-1', 'msg': f"请求错误: {str(e)}"}
        except Exception as e:
            return {'code': '-1', 'msg': f"解析失败: {str(e)}"}

    @filter.regex(BILI_VIDEO_PATTERN)
    @event_message_type(EventMessageType.ALL)
    async def bilibili_parse(self, event):
        """处理 Bilibili 视频解析请求"""
        try:
            url = event.message_obj.message_str  # 从事件中提取消息内容
            match = re.search(BILI_VIDEO_PATTERN, url)
            if match:
                bvid = match.group(2)  # 提取 BV 号
                accept_quality = 80  # 默认接受的清晰度
                video_info = await self.get_video_info(bvid, accept_quality)
                url = await self.text_to_image(video_info)
                yield event.image_result(url)
        except Exception as e:
            yield event.plain_result(e)
