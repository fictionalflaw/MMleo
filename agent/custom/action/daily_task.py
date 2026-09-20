from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils import logger

import time


@AgentServer.custom_action("DailyTaskSelect")
class DailyTask(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        custom_order = [
            "Entry_Store",  # 领取月卡钻石
            "Entry_Recruit",  # 每日海选
            "Entry_Card",  # 每日练卡
            "Entry_NormalTale",  # 每日阅读
            "Entry_GuildNormal" # 协会日常，以上都都已在定义修改enable至false
              # 使用每日免费送抽,安排入领取奖励中
        ]
        order_outname={
            "Entry_Store":"领取月卡",  
            "Entry_Recruit":"每日海选", 
            "Entry_Card":"每日练卡",  
            "Entry_NormalTale":"每日阅读",  
            "Entry_GuildNormal" :"协会日常"
        }
        for key in custom_order:
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                
                return CustomAction.RunResult(success=False)
            # 检查任务是否开启
            keyout=order_outname[key]
            nodeDetail = context.get_node_data(f"{key}")
            if not nodeDetail or not nodeDetail.get("enabled", False):
                logger.info(f"任务: {keyout} 已禁用, 跳过该任务")
                continue


            logger.info(f"执行任务: {keyout}")
            image = context.tasker.controller.post_screencap().wait().get()
            reco = context.run_recognition(key, image)
            if reco is not None and reco.hit:
                context.run_task(key)
                logger.info(f"完成任务: {keyout}")
            else:
                logger.warning(f"任务: {keyout} 识别失败, 跳过该任务")
            

            time.sleep(1)
            
        return CustomAction.RunResult(success=True)