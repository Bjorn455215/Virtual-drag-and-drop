#只能用python 3.9版本 3.10以上無法
import cv2 #4.13.0.92
import cvzone #1.6.1
from cvzone.HandTrackingModule import HandDetector
import numpy as np #2.0.2
import time

# 初始化設定 
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # 寬度
cap.set(4, 720)   # 高度

# 偵測手掌，信心門檻設為 0.8
detector = HandDetector(detectionCon=0.8, maxHands=1)

# 配色：霓虹青 - BGR 格式
color_cyan = (255, 255, 0)
color_white = (255, 255, 255)

class DragRect():
    def __init__(self, posCenter, size=[200, 200], label="DATA_NODE"):
        self.posCenter = posCenter #視窗中心
        self.size = size #視窗大小
        self.label = label #視窗標籤
        self.isDragging = False #初始狀態:未被抓起

    def update(self, cursor, is_pinched): #尖點座標，是否捏合
        cx, cy = self.posCenter
        w, h = self.size

        # 判斷指尖是否在方塊區域內
        #手指的 X 座標必須大於左邊界且小於右邊界。
        #手指的 Y 座標必須大於上邊界且小於下邊界。
        if cx - w // 2 < cursor[0] < cx + w // 2 and \
           cy - h // 2 < cursor[1] < cy + h // 2:
            
            #如果在範圍內捏合，讓方塊中心跟隨手指
            if is_pinched:
                self.posCenter = cursor
                self.isDragging = True
            else:
                self.isDragging = False
        else:
            self.isDragging = False

    def draw(self, img_bg):
        cx, cy = self.posCenter
        w, h = self.size
        x1, y1 = cx - w // 2, cy - h // 2 #左上角座標(給opencv用)
        
        # 1. 繪製科技感外框 (使用 cvzone 的角落矩形)
        # 如果正在拖拽，外框變厚且顏色加亮
        thickness = 5 if self.isDragging else 2
        cvzone.cornerRect(img_bg, (x1, y1, w, h), 25, rt=thickness, colorR=color_cyan) #內建的繪圖函數，在四角繪製L形

        # 2. 裝飾性文字與數據
        cv2.putText(img_bg, f"SYS_{self.label}", (x1 + 10, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_cyan, 2) 
        #在系統左上角加入標籤
        #0.6 是字體大小，2 是字體粗細。
        
        # 3. 動態掃描線效果
        scan_y = y1 + int((time.time() * 100) % h)
        cv2.line(img_bg, (x1, scan_y), (x1 + w, scan_y), color_cyan, 1)

# 建立多個科技視窗
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

        # 1. 計算食指與中指的中點 (作為操控支點)
        grasp_point = [ (p8[0] + p12[0]) // 2, (p8[1] + p12[1]) // 2 ]
        
        # 2. 計算「大拇指」與「食指中指中點」的距離
        # 也可以分別計算 4-8 和 4-12 的距離
        # 計算畫面上點 A(x_1, y_1)與點 B(x_2, y_2)之間的直線距離
        # 回傳距離、資訊、繪圖後影像，但只須距離作判斷，因此以底線來忽略後兩項回傳值
        dist1, _, _ = detector.findDistance(p4, p8)
        dist2, _, _ = detector.findDistance(p4, p12)

        # 3. 三指抓取判定：大拇指同時靠近食指與中指
        # 閾值設定為 60 (三指張開範圍較大，數值可稍微放寬)
        is_pinched = dist1 < 60 and dist2 < 60
        
        # 視覺回饋：在抓取點畫一個小圓圈，讓你更有「抓握感」
        if is_pinched:
            cv2.circle(img, (grasp_point[0], grasp_point[1]), 15, (0, 255, 0), cv2.FILLED)

        # 更新所有視窗狀態：使用三指的中心點作為拖拽座標
        for rect in rectList:
            rect.update(grasp_point, is_pinched)

    # --- 繪製半透明 UI 層 ---
    imgUI = np.zeros_like(img, np.uint8)
    for rect in rectList:
        # 在透明層繪製背景矩形
        cx, cy = rect.posCenter
        w, h = rect.size
        cv2.rectangle(imgUI, (cx-w//2, cy-h//2), (cx+w//2, cy+h//2), (100, 100, 100), cv2.FILLED)
        
        # 呼叫自定義的帥氣繪圖函數
        rect.draw(imgUI)

    # 疊加透明層與原圖
    alpha = 0.3
    mask = imgUI.astype(bool)
    out = img.copy()
    
    # 只在有 UI 的地方進行加權疊加
    out[mask] = cv2.addWeighted(img, alpha, imgUI, 1 - alpha, 0)[mask]

    # 顯示畫面
    cv2.imshow("Stark HUD Interface", out)
    
    # 按 'q' 退出，或按 'r' 重置位置
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
