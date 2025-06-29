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
        argv: dict = json.loads(argv.custom_action_param)
        degree="Feat_难度调整"
        tour_count=argv.get("tour_count")
        for j in range(tour_count):
            image = context.tasker.controller.post_screencap().wait().get()
            key ="巡演_custom启动"

            if context.run_recognition(key,image):
                logger.info(f"即将开始第{j+1}轮巡演打歌...")
            else:
                logger.warning(f"识别失败, 不在巡演选歌界面，即将终止巡演打歌进程...")
                return CustomAction.RunResult(success=True)
            
            for i in range(4):
                nodes=context.run_task(degree).nodes
                flag=self.Check_Completed(nodes,"Feat_难度调整_End")
                if not flag :
                    logger.warning(f"难度调整失败,即将终止巡演打歌进程...")
                    return CustomAction.RunResult(success=True)
                
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

                image = context.tasker.controller.post_screencap().wait().get()
                key ="Feat_开始演唱会"
                if context.run_recognition(key,image):
                    logger.info(f"即将开始第{j+1}轮,第{i+1}次打歌...")
                    context.run_task(key)
                else:
                    logger.warning(f"识别失败, 即将终止巡演打歌进程...")
                    return CustomAction.RunResult(success=True)
                
                logger.info(f"第{j+1}轮巡演，第{i+1}次打歌结束...")

                context.run_task("Entry_巡演后领取星光奖励")
                if j<tour_count-1:context.run_task("Entry_TourMap",pipeline_override=
                                                   {
                                                       "巡演_custom启动":{
                                                           "action": "DoNothing"
                                                           }
                                                        }
                                                    )
                #回到循环开始状态
    def Check_Completed(self,run_detail,completed_node):
        '''
        Args:
            run_detail:[NodeDetail(...), NodeDetail(...), ...],run_task.nodes获取到的结构体数据
            completed_node:string 用来判断task成功与否的关键node的名字,并不一定是最后的node
        Returns:
            bool
        '''
        
        if not run_detail:
            return False
        
        found = False

        for node in run_detail:
            if node.name == completed_node:
                if  node.completed:
                    return True
                else:
                    return False
        
        return found      

        