import os
import json
import time
from datetime import datetime
import sys

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

# 修复 logger 导入
from agent.utils import logger

# 修复 MAA 模块导入
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
            logger.info("识别出错，内容为空,请检查判定线样式")
            return CustomAction.RunResult(success=False)
        elif not (len(reco.filterd_results)==7) :
            logger.info("目标点不为7个，请检查难度或者更换打歌背景重新识别。如多次失败请更换其他方式。推荐音符速度设置2~4")
            return CustomAction.RunResult(success=False)
        target=reco.filterd_results[0:7]#只针对简单模式，其他模式再看
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
    def __init__(self):
        # 定义不同类型的音符模板
        self.template_path = "assets/resource/base/image/"
        self.note_templates = {}
        self.load_note_templates()
        # 初始化判定线弧线参数（根据游戏实际情况调整）
        # 弧线方程：y = a * (x - h)^2 + k
        self.arc_params = {
            'a': -0.001,  # 弧线开口方向和幅度
            'h': 640,     # 弧线顶点x坐标（屏幕中心）
            'k': 600      # 弧线顶点y坐标
        }
        # 缓存上一帧的截图，避免重复截图
        self.last_screenshot = None
        self.last_screenshot_time = 0
        # 缓存音符类型识别结果
        self.note_type_cache = {}

    def load_note_templates(self):
        """
        加载音符模板
        """
        # 定义音符类型和对应的模板文件名
        note_types = {
            "tap": "tap_note.png",
            "hold": "hold_note.png", 
            "slide_up": "slide_up_note.png",
            "slide_down": "slide_down_note.png",
            "slide_left": "slide_left_note.png",
            "slide_right": "slide_right_note.png"
        }
        
        for note_type, filename in note_types.items():
            file_path = os.path.join(self.template_path, filename)
            if os.path.exists(file_path):
                # 读取模板图片
                template = cv2.imread(file_path)
                if template is not None:
                    self.note_templates[note_type] = template
                    logger.info(f"成功加载模板: {note_type}")
                else:
                    logger.warning(f"无法读取模板图片: {file_path}")
            else:
                logger.warning(f"模板文件不存在: {file_path}")

    def match_template(self, screenshot, template, threshold=0.8):
        """
        在截图中匹配模板
        返回最佳匹配位置和匹配度
        """
        if template is None:
            return None, 0
        
        # 转换为灰度图进行匹配
        img_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # 模板匹配
        res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # 获取最佳匹配位置和匹配度
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            # 计算模板中心点位置
            center_x = max_loc[0] + template.shape[1] // 2
            center_y = max_loc[1] + template.shape[0] // 2
            return (center_x, center_y), max_val
            
        return None, max_val

    def detect_note_type(self, screenshot, region):
        """
        根据区域内匹配到的模板检测音符类型
        使用缓存避免重复识别
        """
        # 生成区域的哈希值作为缓存键
        region_hash = hash(region.tobytes())
        if region_hash in self.note_type_cache:
            return self.note_type_cache[region_hash]
        
        best_match = "tap"  # 默认类型
        best_score = 0.0
        
        # 在指定区域检测各种类型的音符
        for note_type, template in self.note_templates.items():
            if template is not None:
                position, confidence = self.match_template(region, template, 0.7)
                if confidence > best_score:
                    best_score = confidence
                    best_match = note_type
        
        # 缓存结果
        self.note_type_cache[region_hash] = best_match
        return best_match

    def is_note_at_judgment_line(self, note_x, note_y, threshold=10):
        """
        检查音符是否到达弧形判定线
        弧线方程：y = a * (x - h)^2 + k
        """
        # 根据弧线方程计算给定x坐标处的判定线y坐标
        expected_y = self.arc_params['a'] * (note_x - self.arc_params['h'])**2 + self.arc_params['k']
        
        # 检查音符y坐标是否在判定线附近
        return abs(note_y - expected_y) <= threshold

    def calculate_hold_duration(self, screenshot, position):
        """
        根据音符后面的白条长度计算长按时间
        """
        # 在音符位置周围区域检测白条
        x, y = position
        # 定义检测区域（在音符下方一定范围内）
        roi_y_start = min(y + 20, screenshot.shape[0] - 1)
        roi_y_end = min(y + 100, screenshot.shape[0] - 1)
        roi_x_start = max(x - 20, 0)
        roi_x_end = min(x + 20, screenshot.shape[1] - 1)
        
        if roi_y_end <= roi_y_start or roi_x_end <= roi_x_start:
            return 0.5  # 默认时长
            
        # 提取区域
        roi = screenshot[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        
        # 转换为HSV色彩空间以便更好地检测白色
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 定义白色的HSV范围
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # 创建白色掩码
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 计算白色区域的高度
        white_pixels = np.where(mask == 255)
        if len(white_pixels[0]) > 0:
            height = np.max(white_pixels[0]) - np.min(white_pixels[0])
            # 根据高度计算时长（假定每10像素代表0.1秒）
            duration = max(0.3, height / 100.0)  # 最短0.3秒
            return duration
            
        return 0.5  # 默认时长

    def detect_white_line_path(self, screenshot, start_position):
        """
        检测白线路径，用于复杂滑动音符
        返回路径点列表
        """
        x, y = start_position
        path_points = [start_position]
        
        # 定义检测区域
        roi_y_start = max(y - 50, 0)
        roi_y_end = min(y + 150, screenshot.shape[0] - 1)
        roi_x_start = max(x - 100, 0)
        roi_x_end = min(x + 100, screenshot.shape[1] - 1)
        
        if roi_y_end <= roi_y_start or roi_x_end <= roi_x_start:
            return path_points
            
        # 提取区域
        roi = screenshot[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        
        # 转换为HSV色彩空间以便更好地检测白色
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 定义白色的HSV范围
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # 创建白色掩码
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 简化处理，沿着y轴方向检测白线路径点
        current_y = y
        step = 10  # y轴步长
        
        for _ in range(20):  # 最多检测20个点
            current_y += step
            if current_y >= screenshot.shape[0] - 10:
                break
                
            # 在当前y位置查找白色区域的中心x坐标
            row_mask = mask[current_y - roi_y_start:current_y - roi_y_start + 1, :]
            white_pixels = np.where(row_mask == 255)[1]
            
            if len(white_pixels) > 0:
                center_x = int(np.mean(white_pixels)) + roi_x_start
                path_points.append((center_x, current_y))
            else:
                # 如果没找到白色区域，尝试在附近查找
                found = False
                for dy in range(-5, 6):
                    if 0 <= current_y + dy - roi_y_start < mask.shape[0]:
                        row_mask = mask[current_y + dy - roi_y_start:current_y + dy - roi_y_start + 1, :]
                        white_pixels = np.where(row_mask == 255)[1]
                        if len(white_pixels) > 0:
                            center_x = int(np.mean(white_pixels)) + roi_x_start
                            path_points.append((center_x, current_y))
                            found = True
                            break
                if not found:
                    break  # 如果连续找不到，停止检测
                    
        return path_points

    def handle_tap(self, context, position):
        """
        处理点击音符
        """
        context.tasker.controller.post_click(position[0], position[1]).wait()

    def handle_multiple_tap(self, context, positions):
        """
        处理多个同时点击音符（双击、三击等）
        """
        # 同时点击所有位置
        touch_ids = []
        for i, position in enumerate(positions):
            touch_id = i + 1
            touch_ids.append(touch_id)
            context.tasker.controller.post_touch_down(touch_id, position[0], position[1]).wait()
        
        time.sleep(0.1)  # 短暂延迟
        
        # 释放所有触控点
        for touch_id in touch_ids:
            context.tasker.controller.post_touch_up(touch_id).wait()

    def handle_hold(self, context, position):
        """
        处理长按音符，根据白条长度确定按压时间
        """
        duration = self.calculate_hold_duration(context.tasker.controller.post_screencap().wait().get(), position)
        context.tasker.controller.post_touch_down(1, position[0], position[1]).wait()
        time.sleep(duration)
        context.tasker.controller.post_touch_up(1).wait()

    def handle_multiple_hold(self, context, positions):
        """
        处理多个同时长按音符
        """
        # 对于多个长按音符，我们逐个处理
        for position in positions:
            screenshot = context.tasker.controller.post_screencap().wait().get()
            duration = self.calculate_hold_duration(screenshot, position)
            
            # 检查白条形状以判断是否是复杂路径
            path_points = self.detect_white_line_path(screenshot, position)
            
            if len(path_points) > 5:  # 如果检测到足够多的路径点，认为是复杂路径
                # 处理复杂路径长按
                self.handle_complex_hold(context, position, path_points, duration)
            else:
                # 普通长按
                context.tasker.controller.post_touch_down(1, position[0], position[1]).wait()
                time.sleep(duration)
                context.tasker.controller.post_touch_up(1).wait()

    def handle_slide(self, context, start_position, direction="down"):
        """
        处理滑动音符，根据箭头方向滑动
        """
        context.tasker.controller.post_touch_down(1, start_position[0], start_position[1]).wait()
        
        # 根据方向滑动
        slide_distance = 80  # 滑动距离
        if direction == "up":
            end_position = (start_position[0], start_position[1] - slide_distance)
        elif direction == "down":
            end_position = (start_position[0], start_position[1] + slide_distance)
        elif direction == "left":
            end_position = (start_position[0] - slide_distance, start_position[1])
        elif direction == "right":
            end_position = (start_position[0] + slide_distance, start_position[1])
        else:
            end_position = (start_position[0], start_position[1] + slide_distance)  # 默认向下
            
        context.tasker.controller.post_touch_move(1, end_position[0], end_position[1]).wait()
        context.tasker.controller.post_touch_up(1).wait()

    def handle_complex_hold(self, context, start_position, path_points, duration):
        """
        处理复杂长按滑动音符，根据白线路径滑动
        """
        # 按路径滑动
        context.tasker.controller.post_touch_down(1, path_points[0][0], path_points[0][1]).wait()
        
        # 沿路径移动
        for i in range(1, len(path_points)):
            x, y = path_points[i]
            context.tasker.controller.post_touch_move(1, x, y).wait()
            # 根据距离调整延迟
            if i > 0:
                dist = np.sqrt((path_points[i][0] - path_points[i-1][0])**2 + 
                              (path_points[i][1] - path_points[i-1][1])**2)
                time.sleep(dist / 1000.0)  # 距离越长，延迟越长
        
        context.tasker.controller.post_touch_up(1).wait()

    def get_screenshot(self, context):
        """
        获取截图，使用缓存避免重复截图
        """
        current_time = time.time()
        # 如果距离上次截图超过0.05秒，或者没有缓存，则重新截图
        if self.last_screenshot is None or (current_time - self.last_screenshot_time) > 0.05:
            self.last_screenshot = context.tasker.controller.post_screencap().wait().get()
            self.last_screenshot_time = current_time
        return self.last_screenshot

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
        img = self.get_screenshot(context)  # 使用缓存截图
        pause_flag=False
        end_flag=False         
        while((time.time()-o_s<210)):
            img = self.get_screenshot(context)  # 使用缓存截图
            while(not(pause_flag)): 
                img = self.get_screenshot(context)  # 使用缓存截图
                flag=0
                # 检测当前帧中所有需要点击的位置
                active_positions = []
                for key in points:
                    if not (img[key[1], key[0]] == [255,255,255]).all():
                        # 检查音符是否到达弧形判定线
                        if self.is_note_at_judgment_line(key[0], key[1]):
                            active_positions.append(key)
                
                # 如果有需要点击的位置
                if len(active_positions) > 0:
                    # 对于多个音符，我们需要分别处理每个音符的类型
                    if len(active_positions) == 1:
                        # 单个音符处理
                        position = active_positions[0]
                        # 创建一个区域用于检测音符类型
                        region_size = 50
                        x_start = max(0, position[0] - region_size // 2)
                        y_start = max(0, position[1] - region_size // 2)
                        x_end = min(img.shape[1], position[0] + region_size // 2)
                        y_end = min(img.shape[0], position[1] + region_size // 2)
                        
                        if y_end > y_start and x_end > x_start:
                            # 提取区域
                            region = img[y_start:y_end, x_start:x_end]
                            
                            # 检测音符类型并相应处理
                            note_type = self.detect_note_type(img, region)
                            
                            if note_type == "tap":
                                self.handle_tap(context, position)
                            elif note_type == "hold":
                                self.handle_hold(context, position)
                            elif note_type.startswith("slide"):
                                # 根据类型确定滑动方向
                                direction_map = {
                                    "slide_up": "up",
                                    "slide_down": "down", 
                                    "slide_left": "left",
                                    "slide_right": "right"
                                }
                                direction = direction_map.get(note_type, "down")
                                self.handle_slide(context, position, direction)
                    else:
                        # 多个音符同时处理
                        # 分别处理每个音符
                        tap_positions = []
                        hold_positions = []
                        slide_info = []  # 存储(位置, 方向)元组
                        
                        for position in active_positions:
                            region_size = 50
                            x_start = max(0, position[0] - region_size // 2)
                            y_start = max(0, position[1] - region_size // 2)
                            x_end = min(img.shape[1], position[0] + region_size // 2)
                            y_end = min(img.shape[0], position[1] + region_size // 2)
                            
                            if y_end > y_start and x_end > x_start:
                                region = img[y_start:y_end, x_start:x_end]
                                note_type = self.detect_note_type(img, region)
                                
                                if note_type == "tap":
                                    tap_positions.append(position)
                                elif note_type == "hold":
                                    hold_positions.append(position)
                                elif note_type.startswith("slide"):
                                    direction_map = {
                                        "slide_up": "up",
                                        "slide_down": "down", 
                                        "slide_left": "left",
                                        "slide_right": "right"
                                    }
                                    direction = direction_map.get(note_type, "down")
                                    slide_info.append((position, direction))
                        
                        # 处理点击音符
                        if len(tap_positions) > 0:
                            if len(tap_positions) == 1:
                                self.handle_tap(context, tap_positions[0])
                            else:
                                self.handle_multiple_tap(context, tap_positions)
                        
                        # 处理长按音符
                        if len(hold_positions) > 0:
                            self.handle_multiple_hold(context, hold_positions)
                        
                        # 处理滑动音符
                        for position, direction in slide_info:
                            self.handle_slide(context, position, direction)
                        
                    flag += len(active_positions)
                    
                if(flag>=3):
                    if context.run_recognition("for_end_concert_success",img) or context.run_recognition("for_end_concert_live",img):
                        end_flag=True   
                        break
                    elif((context.run_recognition("for_end_after_concert_1",img))or(context.run_recognition("for_end_after_concert_2",img))or(context.tasker.stopping)):
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