#利用python 3.9版本
import cv2 #4.13.0.92
import cvzone #1.6.1
from cvzone.HandTrackingModule import HandDetector
import numpy as np #2.0.2
import time
import random

# 初始化設定 
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # 寬度
cap.set(4, 720)   # 高度

# 偵測手掌，信心門檻設為 0.8
detector = HandDetector(detectionCon=0.8, maxHands=1)

# 配色：霓虹青 (Cyberpunk Cyan) - BGR 格式
color_cyan = (255, 255, 0)
color_white = (255, 255, 255)

# 用於控制新增視窗的冷卻時間 (CD)
last_add_time = 0         

class DragRect():
    def __init__(self, posCenter, size=[200, 200], label="DATA_NODE"):
        self.posCenter = posCenter #視窗中心
        self.size = size #視窗大小
        self.label = label #視窗標籤
        self.isDragging = False #初始狀態:未被抓起

    def update(self, cursor, is_pinched, already_grabbed): #尖點座標，是否捏合
        cx, cy = self.posCenter
        w, h = self.size

        # 判斷指尖是否在方塊區域內
        #手指的 X 座標必須大於左邊界且小於右邊界。
        #手指的 Y 座標必須大於上邊界且小於下邊界。
        in_range =  cx - w // 2 < cursor[0] < cx + w // 2 and \
                    cy - h // 2 < cursor[1] < cy + h // 2
            
            #如果在範圍內捏合，讓方塊中心跟隨手指
            # 只有在「手指在範圍內」且「這一幀還沒有其他視窗被抓走」的情況下，才能發動抓取
        if in_range and not already_grabbed:
            if is_pinched:
                self.posCenter = cursor
                self.isDragging = True
                return True  # 告訴主程式：我被抓住了！
        
        self.isDragging = False
        return False  # 告訴主程式：這張沒被抓
    
    def draw(self, img_bg):
        cx, cy = self.posCenter
        w, h = self.size
        x1, y1 = cx - w // 2, cy - h // 2 #左上角座標(給opencv用)
        
        # 新增: 繪製半透明灰色背景 (在全圖疊加下會有玻璃感)
        cv2.rectangle(img_bg, (x1, y1), (x1 + w, y1 + h), (60, 60, 60), cv2.FILLED)

        # 1. 繪製科技感外框 (使用 cvzone 的角落矩形)
        # 如果正在拖拽，外框變厚且顏色加亮
        thickness = 6 if self.isDragging else 2
        cvzone.cornerRect(img_bg, (x1, y1, w, h), 25, rt=thickness, colorR=color_cyan) #內建的繪圖函數，在四角繪製L形

        # 2. 裝飾性文字與數據
        cv2.putText(img_bg, f"SYS_{self.label}", (x1 + 10, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_cyan, 2) 
        #在系統左上角加入標籤
        #0.6 是字體大小，2 是字體粗細。
        
        # 3. 動態掃描線效果
        scan_y = y1 + int((time.time() * 100) % h)
        cv2.line(img_bg, (x1, scan_y), (x1 + w, scan_y), color_cyan, 1)

# 建立多個視窗
rectList = []
for x in range(3):
    rectList.append(DragRect([x * 350 + 250, 250], label=f"UNIT_0{x+1}")) 
    #動態計算座標，不讓視窗重疊排列，並自動編號

while True:
    success, img = cap.read()
    if not success: break

    # 鏡像翻轉，操作更直覺
    img = cv2.flip(img, 1)
    
    # 偵測手掌，但已經 flip 了，這裡選 False，不用再轉一次
    hands, img = detector.findHands(img, flipType=False) 

    if hands:
        lmList = hands[0]['lmList']
        
        # 讀取三指尖座標 (x, y)
        p4 = lmList[4][:2]  # 大拇指
        p8 = lmList[8][:2]  # 食指
        p12 = lmList[12][:2] # 中指

        # 1. 計算三指中心點作為控制支點
        grasp_point = [(p4[0] + p8[0] + p12[0]) // 3, (p4[1] + p8[1] + p12[1]) // 3]
        
        # 2. 計算「大拇指」與「食指中指中點」的距離
        # 也可以分別計算 4-8 和 4-12 的距離
        # 計算畫面上點 A(x_1, y_1)與點 B(x_2, y_2)之間的直線距離
        # 回傳距離、資訊、繪圖後影像，但只須距離作判斷，因此以底線來忽略後兩項回傳值
        dist1, _, _ = detector.findDistance(p4, p8)
        dist2, _, _ = detector.findDistance(p4, p12)

        # 3. 三指抓取判定：大拇指同時靠近食指與中指
        # 閾值設定為 60 (三指張開範圍較大，數值可稍微放寬)
        is_pinched = dist1 < 60 and dist2 < 60

        # 4. 這一幀是否已經有東西被抓走了？初始化為 False
        already_grabbed = False
        
        # 視覺回饋：在抓取點畫一個小圓圈，讓你更有「抓握感」
        if is_pinched:
            cv2.circle(img, (grasp_point[0], grasp_point[1]), 15, (0, 255, 0), cv2.FILLED)

        # 使用 reversed 從最上層開始檢查，確保只抓到最上面的那張，而且不會疊在一起就分不開
        for i, rect in enumerate(reversed(rectList)): # 把疊上去的視窗索引值反過來，這樣才能從最上面開始抽
            if rect.update(grasp_point, is_pinched, already_grabbed): #判斷目前是窗是否被抓住
                already_grabbed = True # 抓到就收工，不去檢查疊下面的視窗
                idx = len(rectList) - 1 - i # 因應reversed
                rectList.append(rectList.pop(idx)) # 最上面的先抽走後 再加到最後面 這樣視窗才能疊在別的視窗上面
                break # 抓到一個就停止，防止連帶抓取

        #新增: 當數值>180，則視為手張開，並新增視窗
        if dist1 > 180:
            current_time = time.time()
            if current_time - last_add_time > 2.0: # 2秒冷卻時間
                if len(rectList) < 6: # 限制最多 6 個視窗避免混亂
                    # 在手部中心點位置新增，並帶有一點隨機偏移避免完全重疊
                    new_pos = [grasp_point[0] + 40, grasp_point[1] + 40]
                    rectList.append(DragRect(new_pos, label=f"NEW_{len(rectList)+1}")) #新增視窗並更新其編號
                    last_add_time = current_time

    # 渲染與疊加 
    # 使用一張全新的虛擬黑色畫布 imgUI，，重疊的部分會在這裡重合。
    imgUI = np.zeros_like(img, np.uint8)
    for rect in rectList:
        rect.draw(imgUI)

    # 全圖疊加 Alpha Blending (背景 30%, UI 70%)
    # 這會讓重疊的視窗顏色自然相加，呈現透光質感
    # 公式: Output = Image1 * alpha + Image2 * beta + gamma 
    # img: 攝影機看到的真實世界、 imgUI (Image2)：畫布、 1 - alpha (Beta)：UI 畫面的權重、 0(Gamma): 亮度修正值
    alpha = 0.3 #真實世界的權重
    out = cv2.addWeighted(img, alpha, imgUI, 1 - alpha, 0)

    # 顯示最終成品
    cv2.imshow(" System HUD ", out)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
