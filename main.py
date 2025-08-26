import asyncio
import aiohttp
import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register(
    "daily_idiom",
    "YourName",
    "每日成语推送插件，定时从API获取成语并推送到指定群组",
    "1.0.0"
)
class DailyIdiomPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.target_groups = config.get("target_groups", [])
        self.push_time = config.get("push_time", "08:00")
        
        # 启动定时任务
        asyncio.create_task(self.daily_task())

    async def fetch_idiom_data(self):
        """获取成语数据
        
        :return: 成语数据字典
        :rtype: dict
        """
        try:
            url = "https://api.timelessq.com/idiom"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        raise Exception(f"API返回错误代码: {response.status}")
        except Exception as e:
            logger.error(f"[每日成语] 获取成语数据时出错: {e}")
            raise

    def format_idiom_message(self, idiom_data):
        """格式化成语消息
        
        :param idiom_data: 成语数据
        :return: 格式化后的消息文本
        :rtype: str
        """
        # 根据API返回的实际数据结构调整以下字段
        name = idiom_data.get("name", "未知成语")
        pinyin = idiom_data.get("pinyin", "")
        explanation = idiom_data.get("explanation", "")
        derivation = idiom_data.get("derivation", "")
        
        message = f"📖 每日成语 - {datetime.date.today()}\n\n"
        message += f"成语: {name}\n"
        if pinyin:
            message += f"拼音: {pinyin}\n"
        if explanation:
            message += f"解释: {explanation}\n"
        if derivation:
            message += f"出处: {derivation}\n"
        
        message += f"\n数据来源: https://api.timelessq.com/idiom"
        return message

    async def send_daily_idiom(self):
        """向所有目标群组推送每日成语"""
        try:
            idiom_data = await self.fetch_idiom_data()
            logger.debug(f"[每日成语] 获取到的成语数据: {idiom_data}")
            
            if not self.target_groups:
                logger.info("[每日成语] 未配置目标群组")
                return

            message_text = self.format_idiom_message(idiom_data)
            logger.info(f"[每日成语] 准备向 {len(self.target_groups)} 个群组推送每日成语")

            for group_id in self.target_groups:
                try:
                    await self.context.send_message(group_id, message_text)
                    logger.info(f"[每日成语] 已向群 {group_id} 推送每日成语")
                    await asyncio.sleep(1)  # 避免发送过快
                except Exception as e:
                    logger.error(f"[每日成语] 向群组 {group_id} 推送消息时出错: {e}")
        except Exception as e:
            logger.error(f"[每日成语] 推送每日成语时出错: {e}")

    def calculate_sleep_time(self):
        """计算到下一次推送时间的秒数"""
        now = datetime.datetime.now()
        hour, minute = map(int, self.push_time.split(":"))

        # 创建今天的目标时间
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果今天的时间已过，则设置为明天
        if target_time <= now:
            target_time += datetime.timedelta(days=1)
        
        seconds = (target_time - now).total_seconds()
        return seconds

    async def daily_task(self):
        """定时推送任务"""
        while True:
            try:
                # 计算到下次推送的时间
                sleep_time = self.calculate_sleep_time()
                logger.info(f"[每日成语] 下次推送将在 {sleep_time/3600:.2f} 小时后")
                
                # 等待到设定时间
                await asyncio.sleep(sleep_time)
                
                # 推送成语
                await self.send_daily_idiom()
                
                # 等待一天后再执行下一次推送
                await asyncio.sleep(86400 - sleep_time)
            except Exception as e:
                logger.error(f"[每日成语] 定时任务出错: {e}")
                # 出错后等待5分钟再重试
                await asyncio.sleep(300)

    @filter.command("idiom_status")
    async def check_status(self, event: AstrMessageEvent):
        """检查插件状态"""
        sleep_time = self.calculate_sleep_time()
        hours = int(sleep_time / 3600)
        minutes = int((sleep_time % 3600) / 60)
        
        yield event.plain_result(
            f"每日成语插件正在运行\n"
            f"目标群组: {', '.join(map(str, self.target_groups))} \n"
            f"推送时间: {self.push_time}\n"
            f"距离下次推送还有: {hours}小时{minutes}分钟"
        )

    @filter.command("get_idiom")
    async def manual_get_idiom(self, event: AstrMessageEvent):
        """手动获取今日成语"""
        try:
            idiom_data = await self.fetch_idiom_data()
            message_text = self.format_idiom_message(idiom_data)
            
            # 回复给发送者
            yield event.plain_result(message_text)
        except Exception as e:
            logger.error(f"[每日成语] 手动获取成语时出错: {e}")
            yield event.plain_result(f"获取成语失败: {str(e)}")
