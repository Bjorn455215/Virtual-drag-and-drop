# Virtual-drag-and-drop
利用OpenCV 及 Mediapipe 實現簡易手勢操作

## 專案簡述
本專案基於 Python 與電腦視覺技術開發的虛擬互動介面，靈感來自於《鋼鐵人》電影中的全像投影 HUD。使用者可以透過網路攝影機，使用手勢直接在空氣中拖拽、移動虛擬視窗。

## 功能 
*   **三指捏合偵測**：結合大拇指、食指與中指的座標運算，實現穩定且符合人體工學的抓取感。
*   **動態科技 UI**：包含霓虹青配色、動態掃描線以及自動編號的數據節點。
*   **半透明玻璃質感**：使用雙層畫布疊加技術，營造出投影在空氣中的透明感。
*   **物件導向設計**：視窗行為由 `DragRect` 類別封裝，易於擴充視窗數量與功能。

## 環境需求
*   **作業系統**：本專案利用Windows
*   **Python 版本**：使用 **3.9**，因為安裝Mediapipe只能搭配**3.10以下的版本**
*   **硬體**：具備網路攝影機 (Webcam)

## 實作成果


https://github.com/user-attachments/assets/79c44e55-4755-4161-81df-f3c9f25a3465



## 參考資料
1. https://github.com/LatchuBright1402/AI-Virtual-Drag-and-Drop/blob/main/VirtualDragAndDrop.py
2. https://www.youtube.com/watch?v=21ATgwVwfWo&t=27s
