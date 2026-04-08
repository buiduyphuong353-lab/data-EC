import streamlit as st
import json
import pandas as pd

# ==========================================
# CẤU HÌNH GIAO DIỆN TRANG WEB
# ==========================================
st.set_page_config(page_title="Phân tích Mùa Vụ", page_icon="🌱", layout="wide")

st.title("🌱 Bảng Theo Dõi Hệ Thống Tưới Nhỏ Giọt")
st.markdown("---") # Kẻ đường ngang

# ==========================================
# KHU VỰC MENU BÊN TRÁI (SIDEBAR)
# ==========================================
st.sidebar.header("⚙️ Cài Đặt Thông Số")
input_file = st.sidebar.text_input("Tên file dữ liệu:", "Lich nho giotj.json")

# Tạo một cái menu xổ xuống để chọn STT thay vì phải sửa code
STT_CAN_TIM = st.sidebar.selectbox("Chọn STT cần phân tích:", ["1", "2", "3", "4"], index=3) 

# ==========================================
# NÚT BẤM CHẠY CHƯƠNG TRÌNH
# ==========================================
if st.sidebar.button("🚀 Chạy Phân Tích", type="primary"):
    try:
        # --- ĐOẠN CODE ĐỌC FILE VÀ LỌC DỮ LIỆU GIỮ NGUYÊN ---
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        needed_keys = {'STT', 'Thời gian', 'TBEC', 'TBPH'}
        filtered_data = [
            {k: item.get(k) for k in needed_keys}
            for item in data if str(item.get('STT')) == STT_CAN_TIM
        ]
        del data 

        if not filtered_data:
            # Thay vì in print, dùng st.error để hiện hộp cảnh báo màu đỏ
            st.error(f"❌ Không có dữ liệu nào khớp với STT = {STT_CAN_TIM}.")
        else:
            df = pd.DataFrame(filtered_data)
            df.drop(columns=['STT'], inplace=True, errors='ignore')

            df['Thời gian'] = pd.to_datetime(df['Thời gian'], format='%Y-%m-%d %H-%M-%S', errors='coerce')
            df.dropna(subset=['Thời gian'], inplace=True)
            df.sort_values(by='Thời gian', inplace=True, ignore_index=True)

            if not df.empty:
                gaps = df['Thời gian'].diff() > pd.Timedelta(days=3)
                df['Mùa_Vụ'] = gaps.cumsum() + 1
                
                df['EC'] = pd.to_numeric(df['TBEC'], errors='coerce') / 100.0
                df['pH'] = pd.to_numeric(df['TBPH'], errors='coerce') / 100.0
                df.drop(columns=['TBEC', 'TBPH'], inplace=True, errors='ignore')
                df.dropna(subset=['EC', 'pH'], inplace=True)

                tong_so_mua_phat_hien = df['Mùa_Vụ'].max()
                
                # Hiện thông báo thành công màu xanh lá
                st.success(f"🔍 Hệ thống đã quét {tong_so_mua_phat_hien} đợt máy chạy. Đã tự động lọc nhiễu các đợt test!")

                so_thu_tu_mua_that = 1

                # --- VÒNG LẶP XỬ LÝ VÀ IN BÁO CÁO TRÊN WEB ---
                for id_mua in range(1, tong_so_mua_phat_hien + 1):
                    df_mua = df[df['Mùa_Vụ'] == id_mua].copy()
                    
                    if df_mua.empty: continue
                        
                    start_season = df_mua['Thời gian'].iloc[0]
                    end_season = df_mua['Thời gian'].iloc[-1]
                    season_days = (end_season - start_season).days
                    
                    # BỘ LỌC NHIỄU
                    if season_days < 1: continue 

                    # Tạo một cái thẻ (Expander) có thể đóng/mở cho từng mùa
                    with st.expander(f"🌾 MÙA VỤ SỐ {so_thu_tu_mua_that} (Bấm để xem chi tiết)", expanded=True):
                        
                        # Chia làm 3 cột để hiển thị thông số tổng quan cho đẹp
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Bắt đầu", start_season.strftime('%d/%m/%Y'))
                        col2.metric("Kết thúc", end_season.strftime('%d/%m/%Y'))
                        col3.metric("Tổng thời gian", f"{season_days} ngày")
                        
                        df_mua['Tuần'] = ((df_mua['Thời gian'] - start_season).dt.days // 7) + 1
                        
                        weekly_stats = df_mua.groupby('Tuần').agg(
                            EC_TB=('EC', 'mean'),
                            pH_TB=('pH', 'mean'),
                            So_lan_tuoi=('EC', 'count')
                        ).round(2)
                        
                        def format_week_label(tuan_idx, ngay_bat_dau_mua):
                            ngay_dau_tuan = ngay_bat_dau_mua + pd.Timedelta(days=(tuan_idx - 1) * 7)
                            ngay_cuoi_tuan = ngay_dau_tuan + pd.Timedelta(days=6)
                            return f"Tuần {tuan_idx} ({ngay_dau_tuan.strftime('%d/%m')})"
                        
                        weekly_stats.index = [format_week_label(idx, start_season) for idx in weekly_stats.index]
                        weekly_stats.index.name = 'Thời Gian'
                        weekly_stats.rename(columns={
                            'EC_TB': 'EC Trung Bình', 
                            'pH_TB': 'pH Trung Bình', 
                            'So_lan_tuoi': 'Số Lần Tưới'
                        }, inplace=True)
                        
                        # Hiển thị bảng dữ liệu (Streamlit tự vẽ)
                        st.markdown("**📋 Bảng dữ liệu chi tiết:**")
                        st.dataframe(weekly_stats, use_container_width=True)
                        
                        # VẼ BIỂU ĐỒ ĐƯỜNG TỰ ĐỘNG CHO EC VÀ pH
                        st.markdown("**📈 Biểu đồ xu hướng EC và pH:**")
                        st.line_chart(weekly_stats[['EC Trung Bình', 'pH Trung Bình']])

                    so_thu_tu_mua_that += 1

    except FileNotFoundError:
        st.error(f"❌ Không tìm thấy file '{input_file}'. Hãy đảm bảo file để cùng thư mục với code.")
    except Exception as e:
        st.error(f"❌ Có lỗi kỹ thuật: {e}")