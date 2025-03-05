import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain

@register("forward_plugin", "w33d", "转发消息插件：收到消息自动转发给指定用户", "1.0.0", "https://github.com/Last-emo-boy/forward-bot")
class ForwardPlugin(Star):
    def __init__(self, context: Context, config: dict):
        """
        初始化插件，config 会由 AstrBot 根据 _conf_schema.json 自动加载。
        如果 config 中没有 forward_target 键，则初始化为空。
        """
        super().__init__(context)
        self.config = config
        if "forward_target" not in self.config:
            self.config["forward_target"] = None

    @filter.command("enable_forward")
    async def enable_forward(self, event: AstrMessageEvent):
        """
        启用转发功能：使用该命令后，机器人将把所有收到的消息转发给你。
        命令示例：/enable_forward
        """
        user_id = event.get_sender_id()
        self.config["forward_target"] = user_id
        # 持久化保存配置（确保配置对象支持 save_config 方法）
        self.config.save_config()
        yield event.plain_result(f"转发功能已启用，所有消息将转发给你，{event.get_sender_name()}。")

    @filter.command("disable_forward")
    async def disable_forward(self, event: AstrMessageEvent):
        """
        禁用转发功能：只有当前转发目标才能使用该命令取消转发。
        命令示例：/disable_forward
        """
        if self.config.get("forward_target") == event.get_sender_id():
            self.config["forward_target"] = None
            self.config.save_config()
            yield event.plain_result("转发功能已禁用。")
        else:
            yield event.plain_result("你不是当前的转发目标，无法禁用转发。")

    @filter.command("status_forward")
    async def status_forward(self, event: AstrMessageEvent):
        """
        查询转发状态：显示当前是否已启用转发以及目标用户的 ID。
        命令示例：/status_forward
        """
        if self.config.get("forward_target"):
            yield event.plain_result(f"转发功能已启用，目标用户ID：{self.config.get('forward_target')}")
        else:
            yield event.plain_result("转发功能当前未启用。")

    @event_message_type(EventMessageType.ALL)
    async def forward_message(self, event: AstrMessageEvent):
        """
        监听所有收到的消息。如果转发功能已启用，则构造带有时间戳和来源信息的消息，
        并将其发送给配置中的目标用户。为避免循环转发，如果消息来自转发目标，则不转发。
        """
        forward_target = self.config.get("forward_target")
        if not forward_target:
            return  # 未启用转发

        # 避免转发目标自己的消息
        if event.get_sender_id() == forward_target:
            return

        # 获取当前时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 判断消息来源：若有 group_id 则认为是群聊消息，否则为私聊
        if event.message_obj.group_id:
            group_info = f"群聊ID：{event.message_obj.group_id}"
            sender_info = f"发送者：{event.get_sender_name()}"
            source_info = f"{group_info}，{sender_info}"
        else:
            sender_info = f"发送者：{event.get_sender_name()}"
            source_info = f"私聊，{sender_info}"

        forwarded_text = f"[{timestamp}] {source_info}\n消息内容：{event.message_str}"
        await self.context.send_message(forward_target, [Plain(forwarded_text)])
