import json
from typing import Union, Optional

from utils import logger
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType
@AgentServer.custom_recognition("SearchMusic")
class SearchMusic(CustomRecognition):
    '''
    对Click进行计次，以在运行超过规定次数后终止搜索
    '''
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
            "礼包提示_REC_星光",
            "Click_星光ver"
        ] 
        flag=0

        while True:
            if context.tasker.stopping:
                    logger.info("正在终止任务…")
                    return None          
            img = context.tasker.controller.post_screencap().wait().get()

            reco1 = context.run_recognition(next_order[0], img)
            reco2 = context.run_recognition(next_order[1], img)
            hit1 = reco1 is not None and reco1.hit
            hit2 = reco2 is not None and reco2.hit
            if hit1 or hit2:#next识别到
                if hit1:context.run_task(next_order[0],pipeline_override={next_order[0]:{"next":[]}})
                if hit2:context.run_task(next_order[1],pipeline_override={next_order[1]:{"next":[]}})
                return None
            else:                
                logger.info("正在寻找可进行演唱会…")

                task_flag=-1
                for index,item in enumerate(interrupt_order):
                    act_reco=context.run_recognition(item,img)
                    if act_reco is not None and act_reco.hit:
                        task_flag=index
                        break

                if(task_flag==len(interrupt_order)-1):flag+=1#对Click计次
                if(task_flag!=-1):context.run_task(interrupt_order[task_flag])
    
                if flag>10: 
                    logger.info("未检测到可进行演唱会，任务即将终止")
                    return None
        return None






       