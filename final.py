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
matplotlib.use('Agg')

# 設定頁面佈局與主題
st.set_page_config(
    page_title="游佳驥很屌的留言板",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

# 留言提交後切換到查看留言標籤
def switch_to_view_tab():
    st.session_state.tab_selection = 1
    st.session_state.refresh_data = True

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
    st.header("分享留言板")
    st.markdown("掃描下方QR碼或分享此連結給朋友！")
    
    # 獲取當前應用URL (在部署後會有實際URL)
    # 本地測試時將使用範例URL
    app_url = st.query_params.get("app_url", ["https://streamlit.io/"])[0]
    
    qr_code = generate_qr_code(app_url)
    st.image(qr_code, caption="掃描此QR碼訪問留言板", width=200)
    st.markdown(f"[留言板連結]({app_url})")

# 主要內容區域
tabs = st.tabs(["發表留言", "留言廣場"])
tab_index = st.session_state.tab_selection

with tabs[0]:
    if tab_index == 0:  # 只有當前標籤被選中時才顯示內容
        # 使用Streamlit表單收集留言信息
        with st.form("留言表單", clear_on_submit=True):
            name = st.text_input("你的名字", placeholder="輸入你的名字...")
            message = st.text_area("留言內容", placeholder="在這裡輸入你想說的話...", height=150)
            mood = st.selectbox("你現在的心情", ["😊 開心", "😢 難過", "😡 生氣", "😴 疲倦", "🥰 感動", "🤔 思考中"])
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
                            
                            # 插入數據到Google Sheets
                            sheet.append_row([display_name, message, mood, current_time])
                            
                            st.success("留言成功發表！")
                            st.balloons()
                            
                            # 設置狀態來切換標籤
                            st.session_state.message_submitted = True
                            # 使用JavaScript代碼自動點擊第二個標籤
                            js = """
                            <script>
                                function sleep(ms) {
                                    return new Promise(resolve => setTimeout(resolve, ms));
                                }
                                async function switchTab() {
                                    await sleep(1500);  // 等待1.5秒讓用戶看到成功訊息
                                    document.querySelector('[data-baseweb="tab-list"] [role="tab"]:nth-child(2)').click();
                                }
                                switchTab();
                            </script>
                            """
                            st.components.v1.html(js, height=0)
                            
                    except Exception as e:
                        st.error(f"發表留言時出錯: {e}")

# 檢查是否需要切換標籤
if st.session_state.message_submitted:
    switch_to_view_tab()
    st.session_state.message_submitted = False
    # 新增留言時重置動畫狀態
    st.session_state.animation_done = False

with tabs[1]:
    # 全新設計的留言廣場
    st.header("✨ 留言廣場 ✨")
    
    # 留言板控制區域
    control_col1, control_col2, control_col3 = st.columns([2, 2, 1])
    
    with control_col1:
        view_options = ["卡片模式", "時間軸模式", "網格模式"]
        selected_view = st.selectbox("顯示方式", view_options, index=view_options.index(st.session_state.view_mode))
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
        st.session_state.show_wordcloud = st.toggle("詞雲", st.session_state.show_wordcloud)
    
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
                    
                    # 心情過濾選項
                    all_moods = ["全部心情"] + sorted(list(set([entry.get(mood_col, '') for entry in data if entry.get(mood_col, '')])))
                    selected_mood = st.selectbox("按心情過濾", all_moods, index=all_moods.index(st.session_state.filter_mood) if st.session_state.filter_mood in all_moods else 0)
                    
                    if selected_mood != st.session_state.filter_mood:
                        st.session_state.filter_mood = selected_mood
                        st.session_state.animation_done = False
                    
                    # 過濾數據
                    filtered_data = data
                    if selected_mood != "全部心情":
                        filtered_data = [entry for entry in data if entry.get(mood_col, '') == selected_mood]
                    
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
                                        st.markdown(f"""
                                        <div style="
                                            background-color: {bg_color}; 
                                            border-radius: 10px; 
                                            padding: 15px; 
                                            margin-bottom: 15px;
                                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                                        ">
                                            <h3 style="margin-top: 0;">{entry.get(name_col, '匿名用戶')} {entry.get(mood_col, '😊')}</h3>
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
                                    <h4 style="margin-top: 0;">{entry.get(name_col, '匿名用戶')} {entry.get(mood_col, '😊')}</h4>
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
                                                <div style="font-weight: bold; margin-bottom: 8px;">{entry.get(name_col, '匿名用戶')} {entry.get(mood_col, '😊')}</div>
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
