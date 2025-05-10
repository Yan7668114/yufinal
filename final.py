import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import pytz
import io
import qrcode
import random
import altair as alt
import time
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
from typing import Tuple
try:
    from chinese_calendar import is_holiday, get_holiday_detail  # 正確導入函數
except ImportError:
    # 如果無法導入，提供替代函數
    def is_holiday(_):
        return False
    
    def get_holiday_detail(_):
        return False, None

matplotlib.use('Agg')

# 定義主題類型
class Theme:
    SPRING = "春季"
    SUMMER = "夏季"
    AUTUMN = "秋季"
    WINTER = "冬季"
    CHINESE_NEW_YEAR = "春節"
    QINGMING = "清明節"
    DRAGON_BOAT = "端午節"
    MID_AUTUMN = "中秋節"
    CHRISTMAS = "聖誕節"
    DEFAULT = "預設"

# 檢測當前季節或節日的函數
def detect_season_or_festival() -> Tuple[str, str]:
    """
    檢測當前日期所屬的季節或特定節日，並返回對應的主題名稱和描述
    節日優先級高於季節。
    
    Returns:
        Tuple[str, str]: (主題標識, 主題描述)
    """
    # 獲取台灣時區的當前日期
    tw_timezone = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_timezone)
    current_month = now.month
    current_day = now.day
    
    # 嘗試使用chinese_calendar庫檢測節日
    try:
        if is_holiday(now.date()):
            _, holiday_name = get_holiday_detail(now.date())
            if holiday_name:
                # 根據節日名稱判斷對應主題
                if any(name in str(holiday_name) for name in ['春節', '除夕', '初一', '大年初']):
                    return Theme.CHINESE_NEW_YEAR, "春節主題：喜慶的紅金配色，象徵新年的祝福與喜悅"
                elif '清明' in str(holiday_name):
                    return Theme.QINGMING, "清明節主題：清新綠色，象徵生機與懷念"
                elif '端午' in str(holiday_name):
                    return Theme.DRAGON_BOAT, "端午節主題：代表端午的五彩裝飾與艾草綠"
                elif '中秋' in str(holiday_name):
                    return Theme.MID_AUTUMN, "中秋節主題：皎潔的月色和溫暖的燈籠橘"
    except Exception:
        # 若chinese_calendar使用失敗，則略過
        pass
    
    # 手動判斷主要節日作為備用方案
    # 春節通常在1-2月，但具體日期每年不同，這裡僅粗略判斷
    if (current_month == 1 and current_day >= 20) or (current_month == 2 and current_day <= 20):
        return Theme.CHINESE_NEW_YEAR, "春節主題：喜慶的紅金配色，象徵新年的祝福與喜悅"
    
    # 清明節 (4月4日或5日)
    if current_month == 4 and (current_day == 4 or current_day == 5):
        return Theme.QINGMING, "清明節主題：清新綠色，象徵生機與懷念"
    
    # 端午節 (5月底或6月初)
    if (current_month == 5 and current_day >= 25) or (current_month == 6 and current_day <= 5):
        return Theme.DRAGON_BOAT, "端午節主題：代表端午的五彩裝飾與艾草綠"
    
    # 中秋節 (9月中旬至下旬)
    if current_month == 9 and 15 <= current_day <= 25:
        return Theme.MID_AUTUMN, "中秋節主題：皎潔的月色和溫暖的燈籠橘"
    
    # 聖誕節 (12月中下旬)
    if current_month == 12 and 15 <= current_day <= 31:
        return Theme.CHRISTMAS, "聖誕節主題：紅綠相間的經典聖誕配色與雪花點綴"
    
    # 如果不是特殊節日，則按季節判斷
    if 3 <= current_month <= 5:
        return Theme.SPRING, "春季主題：嫩綠漸變背景配以淡雅花朵點綴"
    elif 6 <= current_month <= 8:
        return Theme.SUMMER, "夏季主題：海藍漸變背景搭配明亮陽光元素"
    elif 9 <= current_month <= 11:
        return Theme.AUTUMN, "秋季主題：暖橙褐色背景與秋葉圖案"
    else:  # 12, 1, 2月
        return Theme.WINTER, "冬季主題：冰藍色背景與雪花圖案"

# 為特定主題加載CSS樣式
def load_css_for_theme(theme: str) -> str:
    """
    根據指定的主題名稱，返回對應的CSS樣式定義
    
    Args:
        theme (str): 主題名稱
        
    Returns:
        str: CSS樣式字符串
    """
    if theme == Theme.SPRING:
        return """
        /* 春季主題 - 嫩綠漸變背景與花朵點綴 */
        background: linear-gradient(120deg, #e0f7fa, #c8e6c9) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #388e3c !important;
        }
        
        .stButton button {
            background-color: #66bb6a !important;
            border: 1px solid #43a047 !important;
        }
        
        .stButton button:hover {
            background-color: #43a047 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        """
    
    elif theme == Theme.SUMMER:
        return """
        /* 夏季主題 - 海藍漸變背景與陽光元素 */
        background: linear-gradient(120deg, #bbdefb, #4fc3f7) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #0277bd !important;
        }
        
        .stButton button {
            background-color: #29b6f6 !important;
            border: 1px solid #0288d1 !important;
        }
        
        .stButton button:hover {
            background-color: #0288d1 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.8);
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        """
    
    elif theme == Theme.AUTUMN:
        return """
        /* 秋季主題 - 暖橙背景與木質紋理 */
        background: linear-gradient(120deg, #ffe0b2, #ffab91) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #e65100 !important;
        }
        
        .stButton button {
            background-color: #ff8a65 !important;
            border: 1px solid #e64a19 !important;
        }
        
        .stButton button:hover {
            background-color: #e64a19 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        border-left: 5px solid #bf360c;
        """
    
    elif theme == Theme.WINTER:
        return """
        /* 冬季主題 - 雪花浅藍背景与冰晶效果 */
        background: linear-gradient(120deg, #e3f2fd, #bbdefb) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #1565c0 !important;
        }
        
        .stButton button {
            background-color: #42a5f5 !important;
            border: 1px solid #1976d2 !important;
        }
        
        .stButton button:hover {
            background-color: #1976d2 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(200, 230, 255, 0.8);
        """
    
    elif theme == Theme.CHINESE_NEW_YEAR:
        return """
        /* 春節主題 - 喜慶紅金配色 */
        background: linear-gradient(120deg, #b71c1c, #d32f2f) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #ffd700 !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .stButton button {
            background-color: #ffc107 !important;
            border: 1px solid #ff8f00 !important;
            color: #b71c1c !important;
            font-weight: bold;
        }
        
        .stButton button:hover {
            background-color: #ff8f00 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        border: 2px solid #ffd700;
        """
    
    elif theme == Theme.QINGMING:
        return """
        /* 清明節主題 - 清新綠色 */
        background: linear-gradient(120deg, #e8f5e9, #c8e6c9) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #2e7d32 !important;
        }
        
        .stButton button {
            background-color: #66bb6a !important;
            border: 1px solid #43a047 !important;
        }
        
        .stButton button:hover {
            background-color: #43a047 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #2e7d32;
        """
    
    elif theme == Theme.DRAGON_BOAT:
        return """
        /* 端午節主題 - 五彩裝飾與艾草綠 */
        background: linear-gradient(120deg, #e8f5e9, #81c784) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #1b5e20 !important;
        }
        
        .stButton button {
            background-color: #4caf50 !important;
            border: 1px solid #388e3c !important;
        }
        
        .stButton button:hover {
            background-color: #388e3c !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        border: 2px solid #4caf50;
        border-style: dashed;
        """
    
    elif theme == Theme.MID_AUTUMN:
        return """
        /* 中秋節主題 - 月色和燈籠橘 */
        background: linear-gradient(120deg, #37474f, #263238) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #ffb74d !important;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }
        
        .stButton button {
            background-color: #ff9800 !important;
            border: 1px solid #f57c00 !important;
        }
        
        .stButton button:hover {
            background-color: #f57c00 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        border: 2px solid #ff9800;
        """
    
    elif theme == Theme.CHRISTMAS:
        return """
        /* 聖誕節主題 - 紅綠相間與雪花點綴 */
        background: linear-gradient(120deg, #d32f2f, #1b5e20) !important;
        background-attachment: fixed !important;
        position: relative;
        
        h1, h2, h3 {
            color: #ffeb3b !important;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }
        
        .stButton button {
            background-color: #f44336 !important;
            border: 1px solid #d32f2f !important;
        }
        
        .stButton button:hover {
            background-color: #d32f2f !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        border: 3px solid #f44336;
        border-style: dashed;
        """
    
    else:
        # 默認主題，在主題檢測失敗時使用
        return """
        /* 默認主題 - 簡潔現代風格 */
        background: linear-gradient(120deg, #f5f7fa, #e4e8f1) !important;
        background-attachment: fixed !important;
        
        h1, h2, h3 {
            color: #1E88E5 !important;
        }
        
        .stButton button {
            background-color: #1E88E5 !important;
            border: 1px solid #1976D2 !important;
        }
        
        .stButton button:hover {
            background-color: #1976D2 !important;
        }
        
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        """

# 為聖誕節主題創建雪花
def create_snowflakes() -> str:
    """
    為聖誕節主題創建雪花HTML元素
    
    Returns:
        str: 包含雪花元素的HTML字符串
    """
    snowflakes = ""
    for i in range(20):  # 創建20個雪花
        size = random.uniform(0.5, 1.5)
        left = random.uniform(0, 100)
        opacity = random.uniform(0.3, 1)
        delay = random.uniform(0, 5)
        duration = random.uniform(5, 15)
        
        snowflakes += f"""
        <div class="snowflake" style="
            left: {left}%;
            opacity: {opacity};
            font-size: {size}em;
            animation-duration: {duration}s;
            animation-delay: {delay}s;
            pointer-events: none;
            z-index: -2;
        ">❄</div>
        """
    
    return snowflakes

# 設定頁面佈局與主題
st.set_page_config(
    page_title="游佳驥很屌的留言板",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 檢測當前季節或節日並應用相應主題
try:
    current_theme, theme_description = detect_season_or_festival()
except Exception as e:
    st.error(f"無法檢測日期或節日: {e}")
    current_theme, theme_description = Theme.DEFAULT, "預設主題：簡潔現代風格"

# 定義主題圖標對應
theme_icons = {
    Theme.SPRING: "🌸",
    Theme.SUMMER: "🌞",
    Theme.AUTUMN: "🍂",
    Theme.WINTER: "❄️",
    Theme.CHINESE_NEW_YEAR: "🧧",
    Theme.QINGMING: "🌿",
    Theme.DRAGON_BOAT: "🚣",
    Theme.MID_AUTUMN: "🌕",
    Theme.CHRISTMAS: "🎄",
    Theme.DEFAULT: "🎨"
}

# 為當前主題加載相應的CSS樣式
theme_css = load_css_for_theme(current_theme)

# 將CSS樣式注入到頁面中，添加淡入淡出過渡效果，修改選擇器避免覆蓋關鍵UI元素
st.markdown(f"""
<style>
/* 設置全局過渡效果 */
.theme-transition {{
    transition: background-color 0.5s ease, color 0.5s ease, border-color 0.5s ease, box-shadow 0.5s ease;
}}

/* 頁面初始化時的淡入效果 */
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

/* 將主題樣式修改為較低優先級，避免覆蓋Streamlit UI元素 */
.stApp > header {{
    z-index: 999 !important;
}}

.stApp > .main {{
    z-index: 998 !important;
}}

/* 確保表單和互動元素可見 */
input, textarea, button, .stButton, .stTextInput, .stTextArea, .stRadio, .stCheckbox, .stSelectbox {{
    position: relative !important;
    z-index: 10 !important;
}}

/* 主題相關動畫定義 */
@keyframes hongbao {{
    0%, 100% {{ transform: translateY(0) rotate(-5deg); }}
    50% {{ transform: translateY(-10px) rotate(5deg); }}
}}

@keyframes lantern {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-8px); }}
}}

@keyframes float {{
    0%, 100% {{ transform: translateY(0) rotate(0deg); }}
    50% {{ transform: translateY(-15px) rotate(5deg); }}
}}

@keyframes fall {{
    0% {{ transform: translateY(-20px) rotate(0deg); }}
    50% {{ transform: translateY(10px) rotate(15deg); }}
    100% {{ transform: translateY(-20px) rotate(0deg); }}
}}

@keyframes sway {{
    0%, 100% {{ transform: translateX(0) rotate(0deg); }}
    50% {{ transform: translateX(10px) rotate(10deg); }}
}}

@keyframes boat {{
    0% {{ transform: translateX(0) translateY(0); }}
    25% {{ transform: translateX(20px) translateY(-5px); }}
    50% {{ transform: translateX(40px) translateY(0); }}
    75% {{ transform: translateX(20px) translateY(5px); }}
    100% {{ transform: translateX(0) translateY(0); }}
}}

@keyframes gift {{
    0%, 100% {{ transform: translateY(0) rotate(-5deg); }}
    50% {{ transform: translateY(-10px) rotate(5deg); }}
}}

@keyframes snowfall {{
    0% {{ transform: translateY(0) rotate(0deg); }}
    100% {{ transform: translateY(100vh) rotate(360deg); }}
}}

/* 雪花樣式 */
.snowflake {{
    position: fixed;
    top: -10%;
    z-index: -2;
    color: white;
    font-size: 1.5em;
    animation-name: snowfall;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    pointer-events: none;
}}

/* 修改後的主題樣式，避免使用body、html等全局選擇器 */
.stApp {{
    animation: fadeIn 0.8s ease-in-out forwards;
}}

/* 將主題樣式應用到特定容器 */
.main .block-container {{
    {theme_css.replace('body {', '.decorative-bg {').replace('.stApp {', '.main .block-container {')}
}}
</style>

<!-- 添加一個裝飾性背景容器，而非直接修改body -->
<div class="decorative-bg" style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    pointer-events: none;
"></div>

<!-- 主題裝飾元素，使用絕對定位避免干擾正常內容流 -->
<div style="position: fixed; top: 20px; right: 30px; font-size: 40px; opacity: 0.3; z-index: -1; pointer-events: none;" class="{current_theme.lower()}-icon">
    {theme_icons.get(current_theme, "🎨")}
</div>
<!-- 輔助裝飾元素 -->
<div style="position: fixed; bottom: 35px; left: 25px; font-size: 40px; opacity: 0.3; z-index: -1; pointer-events: none;" class="{current_theme.lower()}-icon2">
    {theme_icons.get(current_theme, "🎨")}
</div>
""", unsafe_allow_html=True)

# 添加主題裝飾元素的動畫CSS
if current_theme == Theme.SPRING:
    st.markdown("""
    <style>
    .spring-icon { animation: float 5s ease-in-out infinite; }
    .spring-icon2 { animation: sway 6s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.SUMMER:
    st.markdown("""
    <style>
    .summer-icon { animation: float 5s ease-in-out infinite; }
    .summer-icon2 { animation: sway 6s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.AUTUMN:
    st.markdown("""
    <style>
    .autumn-icon { animation: fall 8s ease-in-out infinite; }
    .autumn-icon2 { animation: sway 6s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.WINTER:
    st.markdown("""
    <style>
    .winter-icon, .winter-icon2 { animation: snowfall 8s linear infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.CHINESE_NEW_YEAR:
    st.markdown("""
    <style>
    .春節-icon { animation: hongbao 5s ease-in-out infinite; }
    .春節-icon2 { animation: lantern 4s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.DRAGON_BOAT:
    st.markdown("""
    <style>
    .端午節-icon { animation: boat 8s linear infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.MID_AUTUMN:
    st.markdown("""
    <style>
    .中秋節-icon2 { animation: lantern 4s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)
elif current_theme == Theme.CHRISTMAS:
    st.markdown("""
    <style>
    .聖誕節-icon2 { animation: gift 4s ease-in-out infinite; }
    </style>
    """, unsafe_allow_html=True)

# 如果是聖誕節主題，添加雪花效果但確保不干擾UI
if current_theme == Theme.CHRISTMAS:
    snowflakes_html = create_snowflakes()
    st.markdown(f"""
    <div style='position: fixed; width: 100%; height: 100%; top: 0; left: 0; pointer-events: none; z-index: -2;'>
        {snowflakes_html}
    </div>
    """, unsafe_allow_html=True)

# 初始化 session_state
if 'tab_selection' not in st.session_state:
    st.session_state.tab_selection = 0  # 預設顯示第一個標籤
if 'refresh_data' not in st.session_state:
    st.session_state.refresh_data = False
if 'message_submitted' not in st.session_state:
    st.session_state.message_submitted = False
if 'liked_messages' not in st.session_state:
    st.session_state.liked_messages = set()
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "卡片模式"
if 'filter_mood' not in st.session_state:
    st.session_state.filter_mood = "全部心情"
if 'animation_done' not in st.session_state:
    st.session_state.animation_done = False
if 'show_wordcloud' not in st.session_state:
    st.session_state.show_wordcloud = False
if 'submission_success' not in st.session_state:
    st.session_state.submission_success = False
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'search_by' not in st.session_state:
    st.session_state.search_by = "內容"

# 應用程式標題與介紹
st.title("留言板")
st.markdown("### 歡迎來到留言板! 在這裡留下你的想法吧～")

# 連接到Google Sheets的函數
def connect_to_gsheets():
    # 從Streamlit Secrets取得認證信息
    # 在本地測試時，使用以下方式
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ],
        )
        client = gspread.authorize(credentials)
        sheet = client.open("游佳驥很靠北的留言板").sheet1  # 打開第一個工作表
        return sheet
    except Exception as e:
        st.error(f"連接Google Sheets時出錯: {e}")
        return None

# 生成QR碼函數
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 將PIL圖像轉換為bytes以在Streamlit中顯示
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

# 生成詞雲
def generate_wordcloud(messages):
    if not messages:
        return None
    
    # 合併所有留言內容
    text = ""
    for msg in messages:
        # 嘗試從不同可能的鍵中獲取留言內容
        content = ""
        if isinstance(msg, dict):
            # 如果是字典，嘗試從各種可能的鍵獲取留言內容
            for key in msg.keys():
                if key.lower() in ['留言內容', 'message', 'content', 'msg', 'text', '內容']:
                    content = msg[key]
                    break
        elif hasattr(msg, '__getitem__'):
            # 如果是可索引對象但不是字典
            try:
                content = str(msg)
            except:
                pass
        
        text += " " + content if content else ""
    
    if not text.strip():
        return None
    
    # 創建詞雲
    try:
        wordcloud = WordCloud(
            font_path='simhei.ttf' if matplotlib.font_manager.findSystemFonts(fontpaths=['simhei.ttf']) else None,
            width=800, 
            height=400, 
            background_color='white',
            colormap='viridis',
            max_words=100,
            contour_width=1,
            contour_color='steelblue'
        ).generate(text)
        
        # 繪製詞雲圖
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        
        # 將圖轉換為bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"生成詞雲時出錯: {e}")
        return None

# 切換標籤的函數
def change_tab_to_view():
    st.session_state.tab_selection = 1
    st.session_state.refresh_data = True
    st.rerun()

# 計算各種心情的數量
def count_moods(data):
    mood_counts = {}
    for entry in data:
        mood = entry.get('你現在的心情', '未知')
        if mood in mood_counts:
            mood_counts[mood] += 1
        else:
            mood_counts[mood] = 1
    return mood_counts

# 產生互動心情圖表
def create_mood_chart(mood_counts):
    if not mood_counts:
        return None
        
    # 準備數據
    chart_data = pd.DataFrame({
        '心情': list(mood_counts.keys()),
        '數量': list(mood_counts.values())
    })
    
    # 創建圖表
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('心情', sort=None),
        y=alt.Y('數量', title='留言數'),
        color=alt.Color('心情', legend=None, scale=alt.Scale(scheme='category10')),
        tooltip=['心情', '數量']
    ).properties(
        width=600,
        height=300,
        title='留言心情分佈'
    ).interactive()
    
    return chart

# 側邊欄 - QR碼生成
with st.sidebar:
    # 顯示當前主題信息
    st.header("🎨 季節主題")
    
    # 使用已定義的主題圖標
    theme_icon = theme_icons.get(current_theme, "🎨")
    
    # 使用卡片樣式顯示當前主題
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-radius: 10px;
        background-color: rgba(255,255,255,0.7);
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{theme_icon}</div>
        <div style="font-weight: bold; margin-bottom: 0.5rem;">當前主題: {current_theme}</div>
        <div style="font-size: 0.9rem; opacity: 0.8;">{theme_description}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 開發者模式：手動切換主題（可以設置query參數 ?dev_mode=true 啟用）
    dev_mode = st.query_params.get("dev_mode", ["false"])[0].lower() == "true"
    if dev_mode:
        st.markdown("### 🛠️ 開發者模式")
        st.caption("可以手動測試不同的主題效果")
        
        all_themes = [
            Theme.SPRING, 
            Theme.SUMMER, 
            Theme.AUTUMN, 
            Theme.WINTER,
            Theme.CHINESE_NEW_YEAR,
            Theme.QINGMING,
            Theme.DRAGON_BOAT,
            Theme.MID_AUTUMN,
            Theme.CHRISTMAS,
            Theme.DEFAULT
        ]
        
        test_theme = st.selectbox(
            "選擇測試主題",
            all_themes,
            index=all_themes.index(current_theme) if current_theme in all_themes else 0
        )
        
        if st.button("應用所選主題"):
            # 更新URL以保持所選主題
            # 注意：這裡不會立即生效，需要用戶手動刷新頁面
            new_theme_css = load_css_for_theme(test_theme)
            st.markdown(f"""
            <style>
            {new_theme_css}
            </style>
            """, unsafe_allow_html=True)
            
            if test_theme == Theme.CHRISTMAS:
                st.markdown(create_snowflakes(), unsafe_allow_html=True)
            
            st.success(f"已應用 {test_theme} 主題，請刷新頁面查看完整效果")
    
    st.markdown("---")
    
    st.header("分享留言板")
    st.markdown("掃描下方QR碼或分享此連結給朋友！")
    
    # 獲取當前應用URL (在部署後會有實際URL)
    # 本地測試時將使用範例URL
    app_url = st.query_params.get("app_url", ["https://streamlit.io/"])[0]
    
    qr_code = generate_qr_code(app_url)
    st.image(qr_code, caption="掃描此QR碼訪問留言板", width=200)
    st.markdown(f"[留言板連結]({app_url})")

# 主要內容區域
tab_names = ["發表留言", "留言廣場"]
selected_tab = st.radio("導航選項", tab_names, index=st.session_state.tab_selection, horizontal=True, label_visibility="collapsed")

# 更新選中的標籤索引到session_state
if tab_names.index(selected_tab) != st.session_state.tab_selection:
    st.session_state.tab_selection = tab_names.index(selected_tab)
    st.rerun()

# 發表留言標籤內容
if st.session_state.tab_selection == 0:
    # 如果之前留言成功，顯示成功消息
    if st.session_state.submission_success:
        st.success("留言成功發表！")
        st.balloons()
        # 移除查看留言的按鈕
        st.session_state.submission_success = False
    
    # 使用Streamlit表單收集留言信息
    with st.form("留言表單", clear_on_submit=True):
        name = st.text_input("你的名字", placeholder="輸入你的名字...")
        message = st.text_area("留言內容", placeholder="在這裡輸入你想說的話...", height=150)
        
        # 心情選擇標題
        st.write("你現在的心情:")

        # 建立心情文字與表情的對照表
        moods_text = ["開心", "難過", "生氣", "疲倦", "感動", "思考中"]
        mood_emojis = ["😊", "😢", "😡", "😴", "🥰", "🤔"]
        
        # 結合表情與文字
        moods_display = []
        for emoji, text in zip(mood_emojis, moods_text):
            moods_display.append(f"{emoji} {text}")
            
        # 初始化選擇的心情
        if 'selected_mood_index' not in st.session_state:
            st.session_state.selected_mood_index = 0
        
        # 修改為使用radio而不是按鈕
        col_radio = st.radio(
            "選擇心情",
            options=range(len(moods_display)),
            format_func=lambda i: moods_display[i],
            index=st.session_state.selected_mood_index,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # 更新session_state中的選擇
        st.session_state.selected_mood_index = col_radio
        
        # 獲取選中的心情
        mood = moods_display[st.session_state.selected_mood_index]
            
        # 添加 CSS 來美化radio按鈕並添加動畫效果
        st.markdown("""
        <style>
        /* 隱藏原始單選按鈕 */
        div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        
        /* Radio按鈕基本樣式 */
        div.row-widget.stRadio > div[role="radiogroup"] {
            display: flex !important;
            justify-content: space-between !important;
            gap: 8px !important;
            margin: 15px 0 25px 0 !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label {
            flex: 1 !important;
            text-align: center !important;
            padding: 15px 5px !important;
            border-radius: 12px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            background-color: rgba(240, 240, 240, 0.5) !important;
            border: 1px solid #eee !important;
            min-height: 90px !important;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 0.95em !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* 個性化每個按鈕的顏色 */
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(1) {
            background-color: rgba(255, 215, 0, 0.2) !important;
            border-top: 3px solid #FFD700 !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(2) {
            background-color: rgba(30, 144, 255, 0.2) !important;
            border-top: 3px solid #1E90FF !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(3) {
            background-color: rgba(255, 69, 0, 0.2) !important;
            border-top: 3px solid #FF4500 !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(4) {
            background-color: rgba(147, 112, 219, 0.2) !important;
            border-top: 3px solid #9370DB !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(5) {
            background-color: rgba(255, 20, 147, 0.2) !important;
            border-top: 3px solid #FF1493 !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(6) {
            background-color: rgba(32, 178, 170, 0.2) !important;
            border-top: 3px solid #20B2AA !important;
        }
        
        /* 選中效果 */
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(1) {
            background-color: rgba(255, 215, 0, 0.6) !important;
            box-shadow: 0 5px 10px rgba(255, 215, 0, 0.3) !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(2) {
            background-color: rgba(30, 144, 255, 0.6) !important;
            box-shadow: 0 5px 10px rgba(30, 144, 255, 0.3) !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(3) {
            background-color: rgba(255, 69, 0, 0.6) !important;
            box-shadow: 0 5px 10px rgba(255, 69, 0, 0.3) !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(4) {
            background-color: rgba(147, 112, 219, 0.6) !important;
            box-shadow: 0 5px 10px rgba(147, 112, 219, 0.3) !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(5) {
            background-color: rgba(255, 20, 147, 0.6) !important;
            box-shadow: 0 5px 10px rgba(255, 20, 147, 0.3) !important;
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"]:nth-of-type(6) {
            background-color: rgba(32, 178, 170, 0.6) !important;
            box-shadow: 0 5px 10px rgba(32, 178, 170, 0.3) !important;
        }
        
        /* 增大表情符號尺寸並設置位置 */
        div.row-widget.stRadio > div[role="radiogroup"] > label > div {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            line-height: 1.2 !important;
        }
        
        /* 表情符號樣式 */
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(1) > div::before {
            content: "😊";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(2) > div::before {
            content: "😢";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(3) > div::before {
            content: "😡";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(4) > div::before {
            content: "😴";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(5) > div::before {
            content: "🥰";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(6) > div::before {
            content: "🤔";
            font-size: 2em !important;
            display: block !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
            transition: all 0.3s ease !important;
            animation: none !important; /* 確保默認情況下無動畫 */
        }
        
        /* 懸停效果 */
        div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 7px 15px rgba(0,0,0,0.15) !important;
        }
        
        /* 為每個按鈕添加特定的動畫 */
        @keyframes happy-bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
        @keyframes sad-shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        @keyframes angry-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.3); }
        }
        @keyframes tired-rotate {
            0%, 100% { transform: rotate(0deg); }
            50% { transform: rotate(8deg); }
        }
        @keyframes love-float {
            0%, 100% { transform: translateY(0) rotate(0); }
            50% { transform: translateY(-5px) rotate(5deg); }
        }
        @keyframes thinking-tilt {
            0%, 100% { transform: rotate(0); }
            50% { transform: rotate(-15deg); }
        }
        
        /* 當懸停時為每個選項添加動畫 */
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(1):hover > div::before {
            animation: happy-bounce 1s ease-in-out infinite !important;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(2):hover > div::before {
            animation: sad-shake 1s ease-in-out infinite !important;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(3):hover > div::before {
            animation: angry-pulse 0.8s ease-in-out infinite !important;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(4):hover > div::before {
            animation: tired-rotate 2s ease-in-out infinite !important;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(5):hover > div::before {
            animation: love-float 1.5s ease-in-out infinite !important;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:nth-of-type(6):hover > div::before {
            animation: thinking-tilt 2s ease-in-out infinite !important;
        }
        
        /* 隱藏原始表情符號 */
        div.row-widget.stRadio > div[role="radiogroup"] > label > div > div:first-letter {
            opacity: 0 !important;
            font-size: 0 !important;
            position: absolute !important;
        }
        
        /* 為表單標題添加間距 */
        p:has(+ div.row-widget.stRadio) {
            margin-bottom: 15px !important;
            font-weight: bold !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        anonymous = st.checkbox("匿名發表")
        
        submitted = st.form_submit_button("發表留言")
        
        if submitted:
            if not message:
                st.error("請輸入留言內容！")
            else:
                try:
                    sheet = connect_to_gsheets()
                    if sheet:
                        # 準備數據
                        tw_timezone = pytz.timezone('Asia/Taipei')
                        current_time = datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M:%S")
                        display_name = "匿名用戶" if anonymous else name or "匿名用戶"
                        
                        # 使用選中的心情
                        selected_mood = moods_display[st.session_state.selected_mood_index]
                        
                        # 插入數據到Google Sheets
                        sheet.append_row([display_name, message, selected_mood, current_time])
                        
                        # 設置成功標記和標籤
                        st.session_state.submission_success = True
                        st.session_state.refresh_data = True
                        
                        # 使用無參數重新運行
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"發表留言時出錯: {e}")

# 留言廣場標籤內容
else:  # st.session_state.tab_selection == 1
    # 全新設計的留言廣場
    st.header("✨ 留言廣場 ✨")
    
    # 留言板控制區域
    control_col1, control_col2, control_col3 = st.columns([2, 2, 1])
    
    with control_col1:
        view_options = ["卡片模式", "時間軸模式", "網格模式"]
        selected_view = st.selectbox("顯示方式選項", view_options, index=view_options.index(st.session_state.view_mode))
        if selected_view != st.session_state.view_mode:
            st.session_state.view_mode = selected_view
            st.session_state.animation_done = False
    
    with control_col2:
        # 刷新按鈕
        if st.button("🔄 刷新留言", key="refresh_btn"):
            st.session_state.refresh_data = True
            st.session_state.animation_done = False
            st.rerun()
    
    with control_col3:
        # 詞雲切換
        st.session_state.show_wordcloud = st.toggle("顯示詞雲", st.session_state.show_wordcloud, label_visibility="visible")
    
    # 嘗試連接Google Sheets並獲取數據
    try:
        sheet = connect_to_gsheets()
        if sheet:
            # 獲取所有數據，避免使用get_all_records來防止expected_headers問題
            all_values = sheet.get_all_values()
            if len(all_values) <= 1:  # 只有表頭或空表
                st.info("目前還沒有留言，成為第一個留言的人吧！")
            else:
                # 手動處理數據，將第一行作為表頭
                headers = all_values[0]
                # 確保表頭唯一
                unique_headers = []
                for i, header in enumerate(headers):
                    if header in unique_headers:
                        unique_headers.append(f"{header}_{i}")
                    else:
                        unique_headers.append(header)
                
                # 建立數據記錄
                data = []
                for row in all_values[1:]:  # 跳過表頭行
                    record = {}
                    for i, value in enumerate(row):
                        if i < len(unique_headers):  # 防止索引越界
                            record[unique_headers[i]] = value
                    data.append(record)
                
                # 數據處理與顯示
                if not data:
                    st.info("目前還沒有留言，成為第一個留言的人吧！")
                else:
                    # 製作DataFrame用於圖表繪製
                    df = pd.DataFrame(data)
                    
                    # 確保列名存在
                    name_col = unique_headers[0] if len(unique_headers) > 0 else '名字'
                    msg_col = unique_headers[1] if len(unique_headers) > 1 else '留言內容'
                    mood_col = unique_headers[2] if len(unique_headers) > 2 else '心情'
                    time_col = unique_headers[3] if len(unique_headers) > 3 else '時間'
                    
                    # 繪製留言心情分佈圖表
                    mood_data = {}
                    for entry in data:
                        mood = entry.get(mood_col, '未知')
                        if mood in mood_data:
                            mood_data[mood] += 1
                        else:
                            mood_data[mood] = 1
                    
                    mood_chart = create_mood_chart(mood_data)
                    if mood_chart:
                        st.altair_chart(mood_chart, use_container_width=True)
                    
                    # 詞雲顯示
                    if st.session_state.show_wordcloud:
                        # 生成詞雲前準備留言內容
                        messages_for_wordcloud = [{msg_col: entry.get(msg_col, '')} for entry in data]
                        wordcloud_buffer = generate_wordcloud(messages_for_wordcloud)
                        if wordcloud_buffer:
                            st.image(wordcloud_buffer, caption="留言詞雲", use_column_width=True)
                        else:
                            st.info("無法生成詞雲，留言內容可能不足")
                    
                    # 新增搜尋功能
                    st.markdown("### 🔍 留言搜尋")
                    search_col1, search_col2 = st.columns([3, 1])
                    with search_col1:
                        search_query = st.text_input("搜尋留言", placeholder="輸入關鍵字...", key="search_query", value=st.session_state.search_query)
                        if search_query != st.session_state.search_query:
                            st.session_state.search_query = search_query
                            st.rerun()
                    with search_col2:
                        search_by = st.selectbox("搜尋範圍", ["內容", "用戶名"], key="search_by", index=["內容", "用戶名"].index(st.session_state.search_by) if st.session_state.search_by in ["內容", "用戶名"] else 0)
                        if search_by != st.session_state.search_by:
                            st.session_state.search_by = search_by
                            st.rerun()

                    # 心情過濾選項
                    all_moods = ["全部心情"] + sorted(list(set([entry.get(mood_col, '') for entry in data if entry.get(mood_col, '')])))
                    selected_mood = st.selectbox("心情過濾選項", all_moods, index=all_moods.index(st.session_state.filter_mood) if st.session_state.filter_mood in all_moods else 0)
                    
                    if selected_mood != st.session_state.filter_mood:
                        st.session_state.filter_mood = selected_mood
                        st.session_state.animation_done = False
                    
                    # 過濾數據
                    filtered_data = data
                    if selected_mood != "全部心情":
                        filtered_data = [entry for entry in data if entry.get(mood_col, '') == selected_mood]
                    
                    # 應用搜尋過濾
                    if search_query:
                        if search_by == "內容":
                            filtered_data = [entry for entry in filtered_data if search_query.lower() in entry.get(msg_col, '').lower()]
                        elif search_by == "用戶名":
                            filtered_data = [entry for entry in filtered_data if search_query.lower() in entry.get(name_col, '').lower()]
                    
                    # 顯示搜尋結果計數
                    if search_query:
                        st.write(f"找到 {len(filtered_data)} 則符合條件的留言")
                        if st.button("清除搜尋", key="clear_search"):
                            st.session_state.search_query = ""
                            st.session_state.search_by = "內容"
                            st.rerun()
                    
                    # 動畫效果
                    if not st.session_state.animation_done:
                        progress_text = "正在載入留言..."
                        my_bar = st.progress(0, text=progress_text)
                        
                        for percent_complete in range(100):
                            time.sleep(0.01)
                            my_bar.progress(percent_complete + 1, text=progress_text)
                        my_bar.empty()
                        st.session_state.animation_done = True
                    
                    # 根據所選視圖模式顯示留言
                    if st.session_state.view_mode == "卡片模式":
                        # 卡片風格展示
                        st.markdown("### 💌 留言卡片")
                        
                        # 每行顯示2個卡片
                        for i in range(0, len(filtered_data), 2):
                            cols = st.columns(2)
                            
                            for j in range(2):
                                if i + j < len(filtered_data):
                                    entry = filtered_data[i + j]
                                    with cols[j]:
                                        # 生成隨機淺色背景
                                        bg_color = f"rgba({random.randint(200, 255)}, {random.randint(200, 255)}, {random.randint(200, 255)}, 0.3)"
                                        
                                        # 卡片樣式
                                        mood_emoji = entry.get(mood_col, '😊')
                                        mood_class = ""
                                        if "😊" in mood_emoji:
                                            mood_class = "mood-happy"
                                        elif "😢" in mood_emoji:
                                            mood_class = "mood-sad"
                                        elif "😡" in mood_emoji:
                                            mood_class = "mood-angry"
                                        elif "😴" in mood_emoji:
                                            mood_class = "mood-tired"
                                        elif "🥰" in mood_emoji:
                                            mood_class = "mood-love"
                                        elif "🤔" in mood_emoji:
                                            mood_class = "mood-thinking"
                                        
                                        # 提取純表情符號，避免HTML標籤顯示
                                        if " " in mood_emoji:
                                            mood_emoji = mood_emoji.split(" ")[0]
                                        
                                        st.markdown(f"""
                                        <div style="
                                            background-color: {bg_color}; 
                                            border-radius: 10px; 
                                            padding: 15px; 
                                            margin-bottom: 15px;
                                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                                        ">
                                            <h3 style="margin-top: 0;">{entry.get(name_col, '匿名用戶')} <span class="mood-emoji {mood_class}">{mood_emoji}</span></h3>
                                            <p style="font-style: italic;">{entry.get(msg_col, '')}</p>
                                            <p style="text-align: right; color: gray; font-size: 0.8em;">
                                                {entry.get(time_col, 'N/A')}
                                            </p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # 讚按鈕
                                        message_id = f"{entry.get(name_col, '')}_{entry.get(time_col, '')}"
                                        if message_id in st.session_state.liked_messages:
                                            if st.button(f"❤️ 已讚", key=f"like_{i+j}"):
                                                st.session_state.liked_messages.remove(message_id)
                                                st.rerun()
                                        else:
                                            if st.button(f"🤍 讚", key=f"like_{i+j}"):
                                                st.session_state.liked_messages.add(message_id)
                                                st.rerun()
                    
                    elif st.session_state.view_mode == "時間軸模式":
                        # 時間軸風格展示
                        st.markdown("### ⏰ 留言時間軸")
                        
                        for i, entry in enumerate(filtered_data):
                            # 左右交替佈局
                            align_right = i % 2 == 0
                            
                            cols = st.columns([2, 6, 2] if align_right else [2, 6, 2])
                            
                            time_col_index = 2 if align_right else 0
                            content_col_index = 1
                            
                            # 時間列
                            with cols[time_col_index]:
                                st.markdown(f"""
                                <div style="
                                    text-align: {'right' if align_right else 'left'};
                                    padding: 10px;
                                    font-size: 0.9em;
                                    color: #555;
                                ">
                                    {entry.get(time_col, 'N/A')}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 內容列
                            with cols[content_col_index]:
                                # 箭頭方向
                                arrow = "◀️" if align_right else "▶️"
                                arrow_style = f"position: absolute; {'left' if align_right else 'right'}: -25px; top: 15px;"
                                
                                # 處理心情表情的動畫
                                mood_emoji = entry.get(mood_col, '😊')
                                mood_class = ""
                                if "😊" in mood_emoji:
                                    mood_class = "mood-happy"
                                elif "😢" in mood_emoji:
                                    mood_class = "mood-sad"
                                elif "😡" in mood_emoji:
                                    mood_class = "mood-angry"
                                elif "😴" in mood_emoji:
                                    mood_class = "mood-tired"
                                elif "🥰" in mood_emoji:
                                    mood_class = "mood-love"
                                elif "🤔" in mood_emoji:
                                    mood_class = "mood-thinking"
                                
                                # 提取純表情符號，避免HTML標籤顯示
                                if " " in mood_emoji:
                                    mood_emoji = mood_emoji.split(" ")[0]
                                
                                st.markdown(f"""
                                <div style="
                                    position: relative;
                                    background-color: {'#E3F2FD' if align_right else '#F5F5F5'}; 
                                    border-radius: 8px; 
                                    padding: 15px; 
                                    margin-bottom: 5px;
                                    border-left: 5px solid {'#2196F3' if align_right else '#9E9E9E'};
                                ">
                                    <div style="{arrow_style}">{arrow}</div>
                                    <h4 style="margin-top: 0;">{entry.get(name_col, '匿名用戶')} <span class="mood-emoji {mood_class}">{mood_emoji}</span></h4>
                                    <p>{entry.get(msg_col, '')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 垂直線
                            if i < len(filtered_data) - 1:
                                st.markdown(f"""
                                <div style="
                                    margin: 0 auto;
                                    width: 2px;
                                    height: 30px;
                                    background-color: #ccc;
                                "></div>
                                """, unsafe_allow_html=True)
                    
                    else:  # 網格模式
                        # 網格風格展示
                        st.markdown("### 🧩 留言牆")
                        
                        # 每行顯示3個網格
                        for i in range(0, len(filtered_data), 3):
                            cols = st.columns(3)
                            
                            for j in range(3):
                                if i + j < len(filtered_data):
                                    entry = filtered_data[i + j]
                                    with cols[j]:
                                        # 隨機顏色和旋轉角度
                                        hue = random.randint(0, 360)
                                        bg_color = f"hsla({hue}, 70%, 85%, 0.9)"
                                        border_color = f"hsla({hue}, 70%, 60%, 1)"
                                        rotation = random.randint(-3, 3)
                                        
                                        # 處理心情表情的動畫
                                        mood_emoji = entry.get(mood_col, '😊')
                                        mood_class = ""
                                        if "😊" in mood_emoji:
                                            mood_class = "mood-happy"
                                        elif "😢" in mood_emoji:
                                            mood_class = "mood-sad"
                                        elif "😡" in mood_emoji:
                                            mood_class = "mood-angry"
                                        elif "😴" in mood_emoji:
                                            mood_class = "mood-tired"
                                        elif "🥰" in mood_emoji:
                                            mood_class = "mood-love"
                                        elif "🤔" in mood_emoji:
                                            mood_class = "mood-thinking"
                                        
                                        # 提取純表情符號，避免HTML標籤顯示
                                        if " " in mood_emoji:
                                            mood_emoji = mood_emoji.split(" ")[0]
                                        
                                        # 便利貼樣式
                                        st.markdown(f"""
                                        <div style="
                                            background-color: {bg_color}; 
                                            border: 1px solid {border_color};
                                            border-radius: 5px; 
                                            padding: 12px; 
                                            margin-bottom: 15px;
                                            transform: rotate({rotation}deg);
                                            min-height: 150px;
                                            display: flex;
                                            flex-direction: column;
                                            justify-content: space-between;
                                            box-shadow: 3px 3px 5px rgba(0,0,0,0.2);
                                        ">
                                            <div>
                                                <div style="font-weight: bold; margin-bottom: 8px;">{entry.get(name_col, '匿名用戶')} <span class="mood-emoji {mood_class}">{mood_emoji}</span></div>
                                                <div style="font-size: 1.0em; word-break: break-word;">{entry.get(msg_col, '')}</div>
                                            </div>
                                            <div style="text-align: right; font-size: 0.7em; margin-top: 8px; color: #555;">
                                                {entry.get(time_col, 'N/A').split(' ')[0] if ' ' in entry.get(time_col, 'N/A') else entry.get(time_col, 'N/A')}
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                    
                    # 重置刷新標記
                    st.session_state.refresh_data = False
                
        else:
            st.error("無法連接到Google Sheets，請檢查您的連接設定。")
    except Exception as e:
        st.error(f"獲取留言時出錯: {e}")

# 頁腳
st.markdown("---")

# 設定CSS樣式美化頁面
st.markdown("""
<style>
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1E88E5;
    }
    h3 {
        margin-top: 1.5rem;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #0D47A1;
    }
    /* 隱藏Streamlit預設頁腳 */
    footer {
        visibility: hidden;
    }
    /* 動畫效果 */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .stMarkdown {
        animation: fadeIn 0.5s ease-in;
    }
</style>
""", unsafe_allow_html=True)

# 添加更多樣式，包括留言廣場的表情動畫
st.markdown("""
<style>
    /* 心情動態效果 - 關鍵幀定義 */
    @keyframes happy-bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    @keyframes sad-shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-2px); }
        75% { transform: translateX(2px); }
    }
    @keyframes angry-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    @keyframes tired-rotate {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(5deg); }
    }
    @keyframes love-float {
        0%, 100% { transform: translateY(0) rotate(0); }
        50% { transform: translateY(-3px) rotate(3deg); }
    }
    @keyframes thinking-tilt {
        0%, 100% { transform: rotate(0); }
        50% { transform: rotate(-10deg); }
    }
    
    /* 留言廣場的表情動畫 - 留言廣場中的表情需要持續播放 */
    .mood-emoji {
        display: inline-block;
        font-size: 1.2em;
        margin-right: 5px;
    }
    .mood-happy {
        animation: happy-bounce 1s ease-in-out infinite;
    }
    .mood-sad {
        animation: sad-shake 1s ease-in-out infinite;
    }
    .mood-angry {
        animation: angry-pulse 0.8s ease-in-out infinite;
    }
    .mood-tired {
        animation: tired-rotate 2s ease-in-out infinite;
    }
    .mood-love {
        animation: love-float 1.5s ease-in-out infinite;
    }
    .mood-thinking {
        animation: thinking-tilt 2s ease-in-out infinite;
    }
    
    /* 表情符號基本樣式 */
    .emoji-happy, .emoji-sad, .emoji-angry, .emoji-tired, .emoji-love, .emoji-thinking {
        display: inline-block;
        font-size: 1.2em;
        animation: none !important; /* 確保默認情況下無動畫 */
    }
    
    /* 發表留言區表情選擇器樣式 */
    div.row-widget.stRadio > div {
        flex-direction: row;
    }
    div.row-widget.stRadio > div[role="radiogroup"] {
        display: flex;
        justify-content: space-between;
        gap: 10px;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        flex: 1;
        text-align: center;
        padding: 10px 5px;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
        background-color: rgba(255, 255, 255, 0.7);
        border: 1px solid #eee;
        margin: 0;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        background-color: rgba(240, 242, 246, 0.7);
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
        background-color: rgba(30, 136, 229, 0.15);
        border-left: 3px solid #1E88E5;
    }
    
    /* 只在懸停時啟用動畫 */
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-happy {
        animation: happy-bounce 1s ease-in-out infinite !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-sad {
        animation: sad-shake 1s ease-in-out infinite !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-angry {
        animation: angry-pulse 0.8s ease-in-out infinite !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-tired {
        animation: tired-rotate 2s ease-in-out infinite !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-love {
        animation: love-float 1.5s ease-in-out infinite !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover .emoji-thinking {
        animation: thinking-tilt 2s ease-in-out infinite !important;
    }
</style>
""", unsafe_allow_html=True)