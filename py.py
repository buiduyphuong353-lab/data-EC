import streamlit as st
import json
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH GIAO DIỆN TRANG WEB
# ==========================================
st.set_page_config(page_title="Phân tích Mùa Vụ", page_icon="🌱", layout="wide")

st.title("🌱 Bảng Theo Dõi Hệ Thống Tưới Nhỏ Giọt")
st.markdown("*(Phiên bản phân tích bằng Logic cốt lõi)*")
st.markdown("---")

# ==========================================
# KHU VỰC MENU BÊN TRÁI (SIDEBAR)
# ==========================================
st.sidebar.header("⚙️ Cài Đặt Thông Số")
input_file = st.sidebar.text_input("Tên file dữ liệu:", "Lich nho giotj.json")

# Menu chọn STT
STT_CAN_TIM = st.sidebar.selectbox("Chọn STT cần phân tích:", ["1", "2", "3", "4"], index=3) 

# [NÂNG CẤP XỊN]: Thanh kéo chọn số ngày chuyển vụ
SO_NGAY_CHUYEN_VU = st.sidebar.slider(
    "⏳ Số ngày nghỉ để cắt mùa vụ mới:", 
    min_value=1.0, 
    max_value=10.0, 
    value=3.0, 
    step=0.5,
    help="Nếu máy nghỉ tưới lâu hơn số ngày này, hệ thống sẽ tự động tính là chuyển sang vụ mới."
)

# ==========================================
# NÚT BẤM CHẠY CHƯƠNG TRÌNH
# ==========================================
if st.sidebar.button("🚀 Chạy Phân Tích", type="primary"):
    try:
        # 1. ĐỌC FILE VÀ NHẶT DỮ LIỆU
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        du_lieu_da_loc = [] 
        
        for item in data:
            if str(item.get('STT')) == STT_CAN_TIM:
                thoi_gian_str = item.get('Thời gian')
                if not thoi_gian_str:
                    continue
                    
                thoi_gian_obj = datetime.strptime(thoi_gian_str, '%Y-%m-%d %H-%M-%S')
                ec_val = float(item.get('TBEC', 0)) / 100.0
                ph_val = float(item.get('TBPH', 0)) / 100.0
                
                du_lieu_da_loc.append({
                    'Thời gian': thoi_gian_obj,
                    'EC': ec_val,
                    'pH': ph_val
                })

        if not du_lieu_da_loc:
            st.error(f"❌ Không có dữ liệu nào khớp với STT = {STT_CAN_TIM}.")
        else:
            # 2. SẮP XẾP TỪ CŨ ĐẾN MỚI
            du_lieu_da_loc.sort(key=lambda x: x['Thời gian'])

            # 3. TÌM MÙA VỤ BẰNG LOGIC KHOẢNG NGHỈ
            danh_sach_mua_vu = [] 
            mua_hien_tai = [du_lieu_da_loc[0]] 
            
            for i in range(1, len(du_lieu_da_loc)):
                ngay_truoc = du_lieu_da_loc[i-1]['Thời gian']
                ngay_nay = du_lieu_da_loc[i]['Thời gian']
                
                # So sánh với cái thanh kéo bên Sidebar
                if (ngay_nay - ngay_truoc) > timedelta(days=SO_NGAY_CHUYEN_VU):
                    danh_sach_mua_vu.append(mua_hien_tai) 
                    mua_hien_tai = [] 
                
                mua_hien_tai.append(du_lieu_da_loc[i])
            
            if mua_hien_tai:
                danh_sach_mua_vu.append(mua_hien_tai)

            st.success(f"🔍 Hệ thống quét được {len(danh_sach_mua_vu)} đợt chạy máy. Đang tự động dọn dẹp rác/test...")

            so_thu_tu_mua_that = 1
            
            # 4. XỬ LÝ BÁO CÁO TỪNG MÙA ĐỂ HIỂN THỊ LÊN WEB
            for mua_vu in danh_sach_mua_vu:
                ngay_bat_dau = mua_vu[0]['Thời gian']
                ngay_ket_thuc = mua_vu[-1]['Thời gian']
                tong_so_ngay = (ngay_ket_thuc - ngay_bat_dau).days
                
                # Bỏ qua test máy dưới 1 ngày
                if tong_so_ngay < 1:
                    continue
                    
                # Tạo thẻ có thể đóng/mở
                with st.expander(f"🌾 MÙA VỤ SỐ {so_thu_tu_mua_that} (Bấm để xem chi tiết)", expanded=True):
                    
                    # 3 Ô hiển thị nhanh
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Bắt đầu", ngay_bat_dau.strftime('%d/%m/%Y'))
                    col2.metric("Kết thúc", ngay_ket_thuc.strftime('%d/%m/%Y'))
                    col3.metric("Tổng thời gian", f"{tong_so_ngay} ngày")
                    
                    # 5. TÍNH TOÁN THEO TUẦN
                    thong_ke_tuan = {} 
                    
                    for lan_tuoi in mua_vu:
                        so_tuan = ((lan_tuoi['Thời gian'] - ngay_bat_dau).days // 7) + 1
                        if so_tuan not in thong_ke_tuan:
                            thong_ke_tuan[so_tuan] = {'Tong_EC': 0, 'Tong_pH': 0, 'So_Lan': 0}
                            
                        thong_ke_tuan[so_tuan]['Tong_EC'] += lan_tuoi['EC']
                        thong_ke_tuan[so_tuan]['Tong_pH'] += lan_tuoi['pH']
                        thong_ke_tuan[so_tuan]['So_Lan'] += 1

                    bang_in_ra_man_hinh = []
                    
                    for so_tuan in sorted(thong_ke_tuan.keys()):
                        du_lieu = thong_ke_tuan[so_tuan]
                        so_lan = du_lieu['So_Lan']
                        
                        ec_tb = round(du_lieu['Tong_EC'] / so_lan, 2)
                        ph_tb = round(du_lieu['Tong_pH'] / so_lan, 2)
                        
                        tuan_bat = ngay_bat_dau + timedelta(days=(so_tuan - 1) * 7)
                        nhan_hien_thi = f"Tuần {so_tuan} ({tuan_bat.strftime('%d/%m')})"
                        
                        bang_in_ra_man_hinh.append({
                            "Tuần": nhan_hien_thi,
                            "EC Trung Bình": ec_tb,
                            "pH Trung Bình": ph_tb,
                            "Số Lần Tưới": so_lan
                        })

                    # Vẽ Bảng bằng Streamlit (Không cần tabulate nữa)
                    st.markdown("**📋 Bảng dữ liệu chi tiết:**")
                    st.dataframe(bang_in_ra_man_hinh, use_container_width=True)
                    
                    # Vẽ biểu đồ trực tiếp từ danh sách
                    st.markdown("**📈 Biểu đồ xu hướng EC và pH:**")
                    st.line_chart(bang_in_ra_man_hinh, x="Tuần", y=["EC Trung Bình", "pH Trung Bình"])

                so_thu_tu_mua_that += 1

    except FileNotFoundError:
        st.error(f"❌ Không tìm thấy file '{input_file}'. Hãy đảm bảo file để cùng thư mục với code.")
    except Exception as e:
        st.error(f"❌ Có lỗi kỹ thuật: {e}")
