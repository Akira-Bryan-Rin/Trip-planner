# AI 旅遊行程規劃工具 (AI Travel Planner)

## 專案背景
本專案為大學課程專案 (Course Project)，由 6 人小組合作完成。  
我主要負責 **輸入模組 (Input Module)** 的設計與實作，處理使用者需求輸入並轉換為景點候選清單，供後續模組使用。

---

## 功能特色
- 使用者輸入旅遊條件（地點、天數、偏好），自動生成景點清單  
- 景點排序與交通路徑規劃（模擬退火演算法解決 TSP 問題）  
- 自動插入餐廳與住宿推薦（Google Maps / OpenStreetMap API）  
- 行程摘要與景點介紹（AI 生成）  
- 匯出完整行程表（Excel / CSV）與互動地圖  

---

## 我的貢獻
- 設計並實作 **輸入模組 (Input Module)**  
  - 處理使用者輸入（旅遊天數、地點、旅遊偏好）  
  - 轉換需求為候選景點清單，供路徑模組最佳化使用  
- 協助撰寫系統架構文件與模組流程圖  

---

## 📓 Jupyter Notebook 展示
專案以 Jupyter Notebook 展示，以tool.ipynb命名

---

## 技術與工具
- 程式語言：Python  
- AI API：DuckDuckGo AI API（現已停止服務）  
- 地圖與地理資訊 API：Google Maps API, OpenStreetMap API, Here Maps API  
- 其他工具：ipywidgets, folium, pandas  

---

## 注意事項
- 由於原始開發使用的 **DuckDuckGo AI API 已停止服務**，
- LLM 模組需由使用者自行外接付費的 API（如 OpenAI API）才能運行。  
- 其他模組（輸入、地圖、輸出）仍可正常執行，可搭配不同 LLM 取代原始設計。  
- 本專案為課程作業，僅針對 **台灣地區**輸出優化，功能有限制（例如每日固定景點數量）。

- ---

## 未來展望
- 擴展至國際旅遊地點  
- 增加自由輸入與個人化行程偏好  
- 加入氣候與季節性建議  
- 支援多人協作與社群分享  
