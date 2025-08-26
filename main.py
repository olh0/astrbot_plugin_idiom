import asyncio
import aiohttp
import datetime
import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.message_event_result import MessageChain
from astrbot.api.message_components import Plain

# 成语列表
IDIOM_LIST = [
    "好高骛远", "有恃无恐", "淋漓尽致", "愤世嫉俗", "涣然冰释", "庸人自扰", "引吭高歌", "老奸巨猾", "略见一斑", "味极嚼蜡",
    "绵里藏针", "一语破的", "买椟还珠", "匠心独运", "安之若素", "刚愎自用", "弱不禁风", "门可罗雀", "动辄得咎", "莫衷一是",
    "为虎作伥", "痴心妄想", "不三不四", "事半功倍", "委曲求全", "蔚然成风", "汗牛充栋", "文过饰非", "明日黄花", "如法炮制",
    "满面春风", "侃侃而谈", "包罗万象", "鬼鬼祟祟", "阴谋诡计", "迫在眉睫", "鳞次栉比", "绝无仅有", "细大不捐", "融会贯通",
    "众口铄金", "返璞归真", "韬光养晦", "生灵涂炭", "忍俊不禁", "美轮美奂", "志同道合极", "纵横捭阖", "耳闻目睹", "蔚为大观",
    "居心叵测", "锱铢必较", "虚与委蛇", "咸与维新", "老马识途", "惘然若失", "空前绝后", "雷厉风行", "各行其是", "任劳任怨",
    "耳濡目染", "鞭长莫及", "变本加厉", "蒙昧无知", "踌躇满志", "弥天大谎", "殚精竭虑", "美不胜收", "如数家珍", "披星戴月",
    "欣欣向荣", "铤而走险", "异想天开", "息息相关", "纷至沓来", "振聋发聩", "不胫而走", "声情并茂", "事必躬亲", "求全责备",
    "戒骄戒躁", "设身处地", "闻一知十", "良莠不齐", "过犹不及", "破釜沉舟", "危言危行", "黄粱一梦", "虎视眈眈", "草菅人命",
    "举一反三", "天网恢恢", "麻木不仁", "汗流浃背", "寥寥无几", "满腹经纶", "兢兢业业", "事倍功半", "栉风沐雨", "醍醐灌顶",
    "目不暇接", "秘而不宣", "浮想联翩", "按兵不动", "再接再厉", "不刊之论极", "迫不及待", "无可非议", "风声鹤唳", "厚此薄彼",
    "墨守成规", "鞠躬尽瘁", "提纲挈领", "自惭形秽", "毫厘不爽", "相得益彰", "河清海晏", "筚路蓝缕", "阳春白雪", "随心所欲",
    "无稽之谈", "流言蜚语", "和蔼可亲", "光怪陆离", "明珠暗投", "无事生非", "同仇敌忾", "层出不穷", "作茧自缚", "始作俑者",
    "秀色可餐", "黯然失色", "如火如荼", "拭目以待", "中流砥柱", "重蹈覆辙", "鼎力相助", "车水马龙", "不落窠臼", "略胜一筹",
    "开门揖盗", "走投无路", "急如星火", "各抒己见", "薪尽极传", "文不加点", "路有饿殍", "毛骨悚然", "颐指气使", "堂而皇之",
    "流连忘返", "既往不咎", "一言九鼎", "余音绕梁", "独树一帜", "指手画脚", "临渊羡鱼", "亘古未有", "微不足道", "升堂入室",
    "箪食壶浆", "肆无忌惮", "白璧微瑕", "鸿篇巨制", "有口皆碑", "励精图治", "炙手可热", "纵横驰骋", "唉声叹气", "博闻强识",
    "慷慨激昂", "差强人意", "怙恶不悛", "一针见血", "百无聊赖", "刻不容缓", "粗茶淡饭", "想入非非", "临深履薄", "病入膏肓",
    "有口皆碑", "责无旁贷", "声名狼藉", "味同嚼蜡", "曲高和寡", "诚惶诚恐", "休戚相关", "望其项背", "娓娓动听", "以逸待劳",
    "迥然不同", "左右逢源", "一往无前", "所向披靡", "剑拔弩张", "浮想联翩", "应接不暇", "凤毛麟角", "一意孤行", "语无伦次",
    "穷兵黩武", "靡靡之音", "官样文章", "恣意妄为", "发愤图强", "并行不悖", "不耻下问", "莘莘学子", "未雨绸缪", "姑息养奸",
    "处心积虑", "死不瞑目", "拾人牙慧", "不遗余力", "恬不知耻", "星罗棋布", "任重道远", "锱铢必较", "与人为善", "见贤思齐",
    "不可开交", "束之高阁", "蠢蠢欲动", "趋之若鹜", "海市蜃楼", "耳提面命", "别具一格", "面目全新", "名副其实", "融会贯通",
    "未置可否", "一暴十寒", "有声有色", "飞扬跋扈", "川流不息", "漠不关心", "错综复杂", "缘木求鱼", "暴殄天物", "泾渭分明",
    "失之交臂极", "焕然一新", "相濡以沫", "司空见惯", "义不容辞", "斑驳陆离", "功败垂成", "洗心革面", "迫不及待", "付之一笑",
    "厉行节约", "相敬如宾", "间不容发", "不负众望", "艰苦奋斗", "匪夷所思", "不孚众望", "相形见绌", "蓬荜生辉", "附庸风雅",
    "信手拈来", "安步当车", "畸形发展", "火中取栗", "适逢其会", "蛊惑人心", "另眼相看", "如雷贯耳", "虚怀若谷", "绘声绘色",
    "触类旁通", "矫揉造作", "一丘之貉", "得不偿失", "偃旗息鼓", "目不斜视", "功亏一篑", "灯红酒绿", "捉襟见肘", "极辨是非",
    "素不相能", "脍炙人口", "短小精悍", "万籁无声", "五花八门", "巧夺天工", "如虎添翼", "擢发难数", "甘之如饴", "屡试不爽",
    "姑妄言之", "别出心裁", "咬文嚼字", "大显身手", "琳琅满目", "顾影自怜", "沽名钓誉", "瞠目结舌", "故伎重演", "无可厚非"
]


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

    async def fetch_idiom_data(self, idiom):
        """获取成语数据
        
        :param idiom: 要查询的成语
        :return: 成语数据字典
        :rtype: dict
        """
        try:
            url = f"https://api.timelessq.com/idiom?wd={idiom}&page=&pageSize="
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 检查API返回的错误码
                        if data.get("errno") != 0:
                            raise Exception(f"API返回错误: {data.get('errmsg', '未知错误')}")
                        
                        # 检查是否有数据
                        if not data.get("data", {}).get("data"):
                            raise Exception(f"未找到成语 '{idiom}' 的相关数据")
                        
                        # 返回第一个成语数据
                        return data["data"]["data"][0]
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
        # 从API响应中提取数据
        name = idiom_data.get("name", "未知成语")
        pinyin = idiom_data.get("pinyin", "")
        
        # 处理基本释义（jbsy字段）
        jbsy = idiom_data.get("jbsy", [])
        explanation = jbsy[0] if jbsy else "暂无解释"
        
        # 处理出处（chuchu字段）
        chuchu = idiom_data.get("chuchu", "")
        
        # 处理近义词（jyc字段）
        jyc = idiom_data.get("jyc", [])
        synonyms = "、".join(jyc[:5]) if jyc else "暂无"
        
        # 处理反义词（fyc字段）
        fyc = idiom_data.get("fyc", [])
        antonyms = "、".join(fyc[:5]) if fyc else "暂无"
        
        # 处理详细释义（xxsy字段）
        xxsy = idiom_data.get("xxsy", [])
        detailed_explanation = "\n".join(xxsy[:3]) if xxsy else "暂无详细解释"
        
        message = f"📖 每日成语 - {datetime.date.today()}\n\n"
        message += f"成语: {name}\n"
        if pinyin:
            message += f"拼音: {pinyin}\n"
        message += f"解释: {explanation}\n"
        if chuchu:
            message += f"出处: {chuchu}\n"
        message += f"近义词: {synonyms}\n"
        message += f"反义词: {antonyms}\n\n"
        message += f"详细释义:\n{detailed_explanation}\n\n"
        message += f"数据来源: https://api.timelessq.com/idiom"
        
        return message

    async def send_daily_idiom(self):
        """向所有目标群组推送每日成语"""
        try:
            # 随机选择一个成语
            selected_idiom = random.choice(IDIOM_LIST)
            logger.info(f"[每日极语] 随机选择的成语: {selected_idiom}")
            
            # 获取成语数据
            idiom_data = await self.fetch_idiom_data(selected_idiom)
            logger.debug(f"[每日成语] 获取到的成语数据: {idiom_data}")
            
            if not self.target_groups:
                logger.info("[每日成语] 未配置目标群组")
                return

            message_text = self.format_idiom_message(idiom_data)
            logger.info(f"[每日成语] 准备向 {len(self.target_groups)} 个群组推送每日成语")

            for group_id in self.target_groups:
                try:
                    # 创建消息链
                    message_chain = MessageChain()
                    message_chain.chain = [Plain(message_text)]
                    
                    await self.context.send_message(group_id, message_chain)
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
                await asyncio.sleep(86400)  # 86400秒 = 24小时
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
            # 随机选择一个成语
            selected_idiom = random.choice(IDIOM_LIST)
            idiom_data = await self.fetch_idiom_data(selected_idiom)
            message_text = self.format_idiom_message(idiom_data)
            
            # 回复给发送者
            yield event.plain_result(message_text)
        except Exception as e:
            logger.error(f"[每日成语] 手动获取成语时出错: {e}")
            yield event.plain_result(f"获取成语失败: {str(e)}")
