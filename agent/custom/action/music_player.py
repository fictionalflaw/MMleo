import os
import json
import time
from datetime import datetime
from PIL import Image
from utils import logger

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
@AgentServer.custom_action("TargetAreaSearchAndSave")
class   TargetAreaSearchAndSave(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        #image getting
        img = context.tasker.controller.post_screencap().wait().get()
        reco = context.run_recognition("MusicalTargetRco", img)#在该识别域中识别结果自动按横轴排序，不用再处理
        if reco is None:
            logger.info("识别出错，内容为空")
            return CustomAction.RunResult(success=False)
        elif not (len(reco.all_results)==7) :
            logger.info("目标点不为7个，请检查难度或者更换打歌背景重新识别。如多次失败请更换其他方式。推荐音符速度设置2~4")
            return CustomAction.RunResult(success=False)
        target=reco.all_results[0:7]#只针对简单模式，其他模式再看
        clickpoints={}
        flag=0
        for i in target:
            flag+=1
            t=[0,0]
            t[0]=int(i.box[0]+i.box[2]/2)
            t[1]=int(i.box[1]+i.box[3]/2)
            clickpoints[f"{len(clickpoints)+1}"]=t
        path = "local/temp"
        file_path=f"{path}/Easy.json"
        os.makedirs(path, exist_ok=True)#文档操作,没有路径创造路径
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(clickpoints,file)
        
            logger.info(f"数据已成功写入文件: {file_path}")
    
        except Exception as e:
            logger.info(f"写入文件时出错: {e}")
        return CustomAction.RunResult(success=True)

@AgentServer.custom_action("MusicPlayer")
class   MusicPlayer(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        points=[]
        with open("local/temp/Easy.json", encoding="utf-8") as f:
            data = json.load(f)
        for key in list(data.keys()):
            points.append(data[key])#points[[]]
        o_s=time.time()
        img = context.tasker.controller.post_screencap().wait().get()
        pause_flag=False
        end_flag=False         
        while((time.time()-o_s<210)):
            img = context.tasker.controller.post_screencap().wait().get()          
            while(not(pause_flag)): 
                img = context.tasker.controller.post_screencap().wait().get()#别管，自有它的道理           
                flag=0
                for key in points:#注意必须是y,x的顺序，"别问，这就是计算机视觉"                    
                    if not (img[key[1], key[0]] == [255,255,255]).all():
                        context.tasker.controller.post_click(key[0],key[1]).wait()
                        flag+=1
                if(flag>=2):
                    if((context.run_recognition("for_end_after_concert_1",img))or(context.run_recognition("for_end_after_concert_2",img))):
                        end_flag=True   
                        break
                    elif(context.run_recognition("for_pause_in_concert",img)):#还要加中途终止和回到打歌界面的识别
                        pause_flag=True
                        break
            if(not(context.run_recognition("for_pause_in_concert",img))):pause_flag=False
            if(context.run_recognition("for_stop_in_concert",img)):break#因为识别速度过快，所以中途停止界面一定会被识别到（除非通过脚本发送快过截图时间的操作）
            elif(context.run_recognition("ConfirmConcert",img)):break#外层堆再多延迟也是应该的，这就是中途暂停的代价
            elif(context.tasker.stopping):break
            if end_flag:break            
           #超过合理时间必须强制结束，及时释放资源，同时得再加入错误识别，即为什么会停止这么久，如果只是暂停就一直暂停（这是不合理行为，不做判定），如果是在打歌画面却不动，直接引入画面判断——>成功就强制结束/重启es2
        return CustomAction.RunResult(success=True)

       


