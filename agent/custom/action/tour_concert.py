import os
import json
import time

from utils import logger

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
@AgentServer.custom_action("TourConcert")
class   TourConcert(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        '''
        custom_param:{
        tour_count:int
        }
        默认会打完一天的四首歌，不满四首时识别是否回到主页作为中断条件
        起点：打歌界面第一首，不是也无所谓，反正打完一天或是不满一天都会中断
        '''
        degree="Feat_难度调整"
        tour_count=argv.get("tour_count")

        for i in range(4):
            logger.info(f"开始第{i+1}次打歌...")
            context.run_task(degree)
            context.run_task("Feat_编队调整",
                {"调整_寻找目标编队":
                 {
                    "next":f"for_编队调整_巡演{i+1}"             
                    }
                }
            )
            if i==3:
                context.run_task("Feat_巡演BP调整")#interface中修改切10的enable                 
            else:
                context.run_task("Feat_巡演BP调整_切3")#interface中修改其中关于BP回复的选项
            #调完bp，开始打歌了
            context.run_task("Feat_开始演唱会")
            out=context.run_task("Flag_TourMap")
            print("结果:",out)
        return CustomAction.RunResult(success=True)