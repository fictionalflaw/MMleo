import json
from typing import Union, Optional

from utils import logger
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType
@AgentServer.custom_recognition("SearchMusic")
class SearchMusic(CustomRecognition):
    
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        next_order = [
            "找回昨日次数",    
            "寻找打歌入口_星光循环内ver"
        ]
        interrupt_order = [
            "点击屏幕获取奖励",
            "OK_pt增加时弹出的奖励界面",
            "活动期间pt达标跳出的卡面领取",
            "Click_星光ver"
        ] 
        flag=0
        
            
        img = context.tasker.controller.post_screencap().wait().get()

        reco1 = context.run_recognition(next_order[0], img)
        reco2 = context.run_recognition(next_order[1], img)
        while((not reco1) and (not reco2)):#都未识别到时一直循环
            if context.tasker.stopping:
                return None
            logger.info("正在寻找可进行演唱会…")
            task_flag=-1
            while(task_flag==-1):
                for index,item in enumerate(interrupt_order):
                    act_reco=context.run_recognition(item,img)
                    if act_reco:
                        task_flag=index
                        break
            print("task_flag=:",task_flag)         
            if(task_flag==len(interrupt_order)-1):flag+=1#Click计次
            context.run_task(interrupt_order[task_flag])
            if flag>10: 
                logger.info("未检测到可进行演唱会，任务即将终止")
                return None
            img = context.tasker.controller.post_screencap().wait().get()
            
            reco1 = context.run_recognition(next_order[0], img)
            reco2 = context.run_recognition(next_order[1], img)
        return None






       