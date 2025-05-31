import os
import json
import time
from datetime import datetime
from collections import defaultdict
from utils import logger

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
@AgentServer.custom_action("CompositeGamePlayer")
class   CompositeGamePlayer(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        self.path = "local/temp"
        self.file_path=f"{self.path}/order.json"
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        zyx4_flag=json.loads(argv.custom_action_param)["zyx4"]
        image = context.tasker.controller.post_screencap().wait().get() 
        try:mf_count=context.run_recognition("for_reco_魔法装备资源箱",image).best_result.text
        except:mf_count=context.run_recognition("for_reco_魔法装备资源箱",image,{"for_reco_魔法装备资源箱":{"roi":[409,660,33,33]}}).best_result.text        
        try:zz_count=context.run_recognition("for_reco_种子资源箱",image).best_result.text
        except:zz_count=context.run_recognition("for_reco_种子资源箱",image,{"for_reco_种子资源箱":{"roi":[512,656,24,36]}}).best_result.text    
        try:js_count=context.run_recognition("for_reco_剑士装备资源箱",image).best_result.text
        except:js_count=context.run_recognition("for_reco_剑士装备资源箱",image,{"for_reco_剑士装备资源箱":{"roi":[619,656,25,36]}}).best_result.text
        if(zyx4_flag):
            try:ys_count=context.run_recognition("for_reco_药水资源箱",image).best_result.text
            except:ys_count=context.run_recognition("for_reco_药水资源箱",image,{"for_reco_药水资源箱":{"roi":[718,660,27,32]}}).best_result.text
        else:ys_count="0"
        while mf_count != "0" or zz_count != "0" or js_count != "0" or ys_count != "0":
            try:mf_count=context.run_recognition("for_reco_魔法装备资源箱",image).best_result.text
            except:mf_count=context.run_recognition("for_reco_魔法装备资源箱",image,{"for_reco_魔法装备资源箱":{"roi":[409,660,33,33]}}).best_result.text
            try:zz_count=context.run_recognition("for_reco_种子资源箱",image).best_result.text
            except:zz_count=context.run_recognition("for_reco_种子资源箱",image,{"for_reco_种子资源箱":{"roi":[512,656,24,36]}}).best_result.text
            try:js_count=context.run_recognition("for_reco_剑士装备资源箱",image).best_result.text
            except:js_count=context.run_recognition("for_reco_剑士装备资源箱",image,{"for_reco_剑士装备资源箱":{"roi":[619,656,25,36],"only_rec":True}}).best_result.text
            if(zyx4_flag):
                try:ys_count=context.run_recognition("for_reco_药水资源箱",image).best_result.text
                except:ys_count=context.run_recognition("for_reco_药水资源箱",image,{"for_reco_药水资源箱":{"roi":[718,660,27,32]}}).best_result.text
            else:ys_count="0"
            x,y=385,640
            
            if mf_count !="0":
                x=385
            elif zz_count!="0":
                x=490
            elif js_count!="0":
                x=595
            elif ys_count!="0":
                x=690
                
            order=self.submit_order(context)    
            context.tasker.controller.post_swipe(x, y, x, y, duration=3000).wait()
            context.run_task("for_click_magic_wand")

            image = context.tasker.controller.post_screencap().wait().get() 
            
            matrix_dd=self.parse_tick(context,image,order)
            matrix = self.parse_chessboard(context,image)
            matrix[0][0]=matrix[0][1]=0#屏蔽预留的动态单位
            print(matrix)
            element_positions = defaultdict(list)
            for i in range(5):
                for j in range(7):
                # 如果当前格子不是订单对象
                    if matrix_dd[i][j] != 1:
                        element = matrix[i][j]
                        element_positions[element].append((i, j))
                    else:
                        if (str(matrix[i][j]) in order):
                            if order[f"{matrix[i][j]}"]<=0:#已满足订单需求，后续对于该元素的屏蔽不启用
                                element = matrix[i][j]
                                element_positions[element].append((i, j))
                            else: order[f"{matrix[i][j]}"]-=1
                      
            zz_positions={k: v for k, v in element_positions.items() if k==24}
            composite_positions={k: v for k, v in element_positions.items() if len(v) > 1 and k>10 and k not in [19,24,39,49,54,68,69,70]}#屏蔽名单，各单位最高元素和财宝最后三级元素（用升级卡升）
            for po in composite_positions.values():
                self.post_composite(context,po)
            for po in zz_positions.values():
                for po_click in po:
                    x,y=self.get_swipe_position(po_click[0],po_click[1])
                    for i in range(4):
                        context.tasker.controller.post_click(x,y).wait()
                        time.sleep(0.5)
            if context.tasker.stopping:
                logger.info("检测到停止任务, 开始退出agent")
                return CustomAction.RunResult(success=False)


            
        logger.info("资源箱不足, 终止合成")
        return CustomAction.RunResult(success=True)
    def parse_chessboard(self,context,image):
         """解析棋盘
        根据识别对象在二维数组对应位置填上编号
        Args:
           image
        Returns:
            5x7的二维数组，识别到的位置用对应物品编号填充：
            编号示例：魔法师装备系列11~19，种子系列21~24，食物系列31~39，剑士装备41~49，药水系列51~54，财宝系列61~70（使用最优升级卡方案不会存在69、70，因为在财宝倒数第三级就可以使用升级卡）
            空位置-1
        """
         matrix = [[0] * 7 for _ in range(5)]
         chain=[9,4,9,9,4,10]#图鉴中各合成链的上限
             
         for j in range(len(chain)):#棋盘生成
                threshold=0.6
                if j==4:threshold=0.8#规定药水组检测下限
                elif j==5 or j==2:threshold=0.7#金币、食物组检测下限
                
                for i in range(chain[j]):
                    
                    
                    template_path=f"合成游戏/{(j+1)*10+i+1}.png"
                    reco_detail=context.run_recognition(
                    "for_reco_in_composite_game",
                    image,
                    {"for_reco_in_composite_game": {"recognition": "TemplateMatch","template":template_path,"threshold": threshold}},
                )
                    matrix=self.fill_chessboard(reco_detail,matrix,(j+1)*10+i+1)                    
                    #不用了，换templatematch
                    # if j==5:#金币不会有动态，使用模版匹配
                    #     reco_detail=context.run_recognition(
                    #     "for_reco_in_composite_game",
                    #     image,
                    #     {"for_reco_in_composite_game": {"recognition": "TemplateMatch","template":template_path }},
                    # )
                    #     matrix=self.fill_chessboard(reco_detail,matrix,(j+1)*10+i+1)
                    #     #if(len(ct)>2):self.post_composite(ct)#金币可以直接合成
                    # else:#其余特征匹配
                    #     reco_detail=context.run_recognition(
                    #         "for_reco_in_composite_game",
                    #         image,
                    #         {"for_reco_in_composite_game": {"template":template_path }},
                    #     )
                    #     while(reco_detail): #进行绿色掩码，因为featurematch当前版本返回值只有一个            
                    #         matrix=self.fill_chessboard(reco_detail,matrix,(j+1)*10+i+1)
                    #         x,y,w,h=reco_detail.best_result.box
                    #         image[y:y+h,x-10:x+w]=[0,255,0]
                    #         reco_detail=context.run_recognition(
                    #         "for_reco_in_composite_game",
                    #         image,
                    #         {"for_reco_in_composite_game": {"template":template_path }},
                    #     )
                            
         return matrix
    def parse_tick(self,context,image,order):
         """解析棋盘中属于订单的元素
        根据识别对象在二维数组对应位置填上编号
        Args:
        order:{"元素编号","所需个数"}
        Returns:
            5x7的二维数组，识别到打钩标记的位置会置1（第四个订单的对象）或者是对应元素编号
        """
         matrix = [[0] * 7 for _ in range(5)]
         reco_detail=context.run_recognition("for_reco_in_composite_game_2",image,)
         matrix=self.fill_chessboard(reco_detail,matrix,1) 
        #挨个识别，重新附上更精确的值

         return matrix
    def load_data(self):
        """加载或初始化数据文件"""
        os.makedirs(self.path, exist_ok=True)
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                try:
                    data = json.load(f)
                    # 如果日期变更则重置
                    if data.get('date') != self.today:return 0
                    else:return data.get('count')
                except json.JSONDecodeError:
                    return 0
        
        return 0
    def save_data(self):
        """保存数据到文件"""
        data={'date': self.today, 'count': self.order_count}
        with open(self.file_path, 'w') as f:
            json.dump(data, f)
    def submit_order(self,context):
        self.order_count=self.load_data()#有提交优先提交
        image=context.tasker.controller.post_screencap().wait().get() 
        order_reco=context.run_recognition("for_reco_in_composite_game_3",image)
        if order_reco:
            for item in order_reco.filterd_results:
                context.tasker.controller.post_click(item.box[0],item.box[1]).wait()
                time.sleep(0.5)
                print("提交1次")
                self.order_count+=1
        self.save_data()
        return self.get_order(context)
    def get_order(self,context):
        '''返回一个订单dict{"元素":int(所需个数)}'''
        image=context.tasker.controller.post_screencap().wait().get() 
        order1_key=context.run_recognition("for_order_reco_1",image).all_results[0].text[:4]#截取前四个字符
        order2_key=context.run_recognition("for_order_reco_2",image).all_results[0].text[:4]#截取前四个字符
        order3_key=context.run_recognition("for_order_reco_3",image).all_results[0].text[:4]#截取前四个字符
        print(order1_key,order2_key,order3_key)
        file_path=f"agent/order_library.json"
        order=defaultdict(int)
        with open(file_path, 'r',encoding='UTF8') as f:
            try:
                data = json.load(f)
                for d in [data.get(order1_key), data.get(order2_key), data.get(order3_key)]:
                    for key, value in d.items():
                            order[key] += value  
            except Exception as e:
                print(f"订单生成时出错:{e}")
        print(order)
        return order

        
        
        

        
    def fill_chessboard(self, recognition_data, matrix, fill_value):
        """棋盘填空
        根据识别对象在二维数组对应位置填上编号
        Args:
            recognition_data: 识别数据
            fill_value: 用于填充识别到位置的数值，默认为0
            matrix: 外部传入的8x8矩阵，如果为None则新建
        Returns:
            5x7的二维数组，识别到的位置用对应物品编号填充：
            编号示例：魔法师装备系列11~19，种子系列21~24，食物系列31~39，剑士装备41~49，药水系列51~54，财宝系列61~70（使用最优升级卡方案不会存在69、70，因为在财宝倒数第三级就可以使用升级卡）
            空位置-1
            长度不定的二维数组，list<list<row_idx,col_idx >>,一个数组装有同类元素的所有位置
        """
        if not recognition_data:
            return matrix

        # 计算每个单元格的Y坐标(行)和X坐标(列)
        cell_height = 519 // 5
        cell_width = 724 // 7

        ROW_Y = [40 + i * cell_height + cell_height // 2 for i in range(5)]
        COL_X = [330 + j * cell_width + cell_width // 2 for j in range(7)]

        for item in recognition_data.filterd_results:
            x, y, w, h = item.box

            # 行列索引查找逻辑
            row_idx = next(
                (
                    i
                    for i, ry in enumerate(ROW_Y)
                    if ry - cell_height // 2 <= y+h//2 <= ry + cell_height // 2
                ),
                None,
            )
            col_idx = next(
                (
                    i
                    for i, cx in enumerate(COL_X)
                    if cx - cell_width // 2 <= x+h//2 <= cx + cell_width // 2
                ),
                None,
            )
            #candidate_list=[]
            if row_idx is not None and col_idx is not None:
                matrix[row_idx][col_idx] = fill_value
                #candidate_list.append((row_idx,col_idx))


        return matrix 
    def post_composite(self,context,compose_list):
         """合成操作
        根据传入数组合成
        Args:
           list[(x,y),(x,y)],长度大于2会挨个合成，
        """
         if len(compose_list)<2:return         
         else:
            flag=1
            while(flag<len(compose_list)):
                x1,y1=self.get_swipe_position(compose_list[flag-1][0],compose_list[flag-1][1])
                x2,y2=self.get_swipe_position(compose_list[flag][0],compose_list[flag][1])
                # context.tasker.controller.post_click(x1,y1).wait()
                context.tasker.controller.post_swipe(x1, y1, x2, y2, duration=500).wait()
                time.sleep(0.5)
                print(f"移动:{compose_list[flag-1]}到{compose_list[flag]}")
                flag+=2
         return
             
    def get_swipe_position(self, row, col):
        """将二维数组位置转换为屏幕点击坐标
        Args:
            row: 行索引(0-4)
            col: 列索引(0-6)
        Returns:
            (x, y) 屏幕坐标
        """
        # 棋盘ROI参数[330,40,724,519]
        board_x, board_y, board_width, board_height = 330, 40, 724, 519

        # 计算单元格尺寸
        cell_width = board_width // 7
        cell_height = board_height // 5

        # 计算中心点坐标
        x = board_x + col * cell_width + cell_width // 2
        y = board_y + row * cell_height + cell_height // 2

        return (x, y)