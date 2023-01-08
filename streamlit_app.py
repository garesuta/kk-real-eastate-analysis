import leafmap.foliumap as leafmap
import datetime
import pandas as pd
import geopandas as gpd
import streamlit as st
import numpy as np
import os
import plotly.express as px

st.set_page_config(layout="wide")


hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title('Real-Estate Map based on Khon Kaen V1')

with st.expander("วิธีการใช้งาน"):
    st.markdown(""" ชุดข้อมูล อย่างน้อยต้องประกอบไปด้วย latitude,longitude, price, property_type นามสกุลไฟล์ csv,xlsx(excel) เท่านั้น
1. เลือก ข้อมูลที่ใช้ (เลือก columns ที่จะใช้สำหรับแสดงผล ) เช่น property type, price, zone
2. เลือกข้อมูลที่จะแสดงในวงกลมจาก 'เลือกข้อมูลที่จะแสดงในวงกลม'
3. เลือก filter จากความสนใจที่เราสนใจ เช่น property type มี (บ้านเดี่ยว, บ้าน, ทาวน์โฮม, อื่นๆ)
4. ในการเลือก Zone เลือกได้ทีละ 1 zone เท่านั้น
5. ในการกรองด้วยราคา (price) เลือกใช้การกรอง ได้อย่างเดียว เท่านั้น price range, starting-ending price
6. ในการกรองด้วยกรอบ 4 เหลี่ยม ต้องลากกรอบ แล้ว export เป็น geojson file แล้ว re-upload ขึ้น ในช่อง Upload a GeoJSON file as an ROI ถึงจะแสดงผลออกมาให้
 """)
    
# label = 'บ้าน','บ้านเดี่ยว','ที่ดิน','คอนโด','หอพัก/อพาร์ทเม้น','ทาวน์โฮม','อาคารพาณิชย์/สำนักงาน','อื่นๆ' 8 counts

# initiate map
# next map center will be up on province
m = leafmap.Map(center=[16.43966586346399, 102.82847780805886], zoom=12,
                draw_export=True,
                )
m.add_basemap("ROADMAP")

col1, col2,col3,col4 = st.columns(4)

with col1:
    # file management
    st.write('Uploading file ที่นี่!')
    data_upload = st.file_uploader('Upload data file', type=["csv","xlsx"])
    if data_upload is not None:
        if(data_upload.type == 'text/csv'):
            df = pd.read_csv(data_upload)
            list_col = df.columns
        else:
            df = pd.read_excel(data_upload)
            list_col = df.columns
    else :
        st.error("ไม่ต้องสนใจ error ได้โปรด upload file ก่อน")
    # geojson file
    choice = st.selectbox('เลือกกรอบความสนใจ ถ้ามีเลือก "yes"',['no','yes'])
    if choice =='yes':
        data_geo = st.file_uploader('Upload a GeoJSON file as an ROI', type=["geojson"])
        datageo = gpd.read_file(data_geo)

with col2:
    st.write('เลือกข้อมูลที่ใช้')   
    label_prop = st.selectbox('เลือก Property type columns',list_col)
    label = df[label_prop].unique()
    price_col = st.selectbox('เลือก Price columns', list_col)
    zone_col = st.selectbox('เลือก zone columns',list_col)
    popup_list = st.multiselect('เลือกข้อมูลที่จะแสดงในวงกลม', list_col)
    
with col3:
    st.write('เลือกความสนใจ')
    #province = st.selectbox('เลือกจังหวัด (Unavailable)', 'dddd')
    option = st.multiselect('เลือก property type', label)
    zone_use = df[zone_col].unique()
    zone = st.multiselect('เลือก zone ที่สนใจ', zone_use)
    # st.write(zone)
    price_tag = [None, '<1m', '1-2m', '2-3m', '3-5m', '>5m']
    price_fil = st.selectbox('เลือกตาม price range (ช่วงราคา)', price_tag)
with col4:
    st.write('เลือกตามราคา เริ่มต้น,สุดท้าย (Starting-Ending price)')
    first_fil_num = st.number_input('ราคาเริ่มต้น (Starting price)')
    end_fil_num = st.number_input('ราคาสุดท้าย (Ending price)', max_value=1000000000)
    #roi = st.selectbox('Select a ROI by upload your GeoJSON file (Unavailable)', 'G')
    st.write('เลือก columns สำหรับคำนวณ ราคา ต่อ ตารางวา')
    vas_col = st.selectbox('เลือก ตารางวา columns',list_col)
    df['price_per_va'] = df[price_col]/df[vas_col]
st.markdown('''-------''')
with st.expander('ตัวอย่างข้อมูล'):
    st.write(df.sample(10))

# list of hover
# create dict for icon
ic = {'บ้าน': 'home','คอนโด': 'building',
    'อาคารพาณิชย์/สำนักงาน': 'users','ทาวน์โฮม': 'bank',
    'หอพัก/อพาร์ทเม้น': 'bed','อื่นๆ': 'diamond',
    'บ้านเดี่ยว': 'leaf','ที่ดิน': 'map-pin'}

def geo(geodata):
        xx,yy = geodata.geometry[0].exterior.coords.xy
        lon = xx.tolist()
        lat = yy.tolist()
        return min(lon),min(lat),max(lon),max(lat)

def convert_df(df):
    return df.to_csv().encode('utf-8')
   
def map_by_price(df, option, zone, price_fil):
    # [None,'<1m','1-2m','2-3m','3-5m','>5m']

    if (price_fil == None):
        map_by_zone(df, option, zone)
    elif(price_fil == '<1m'):
        info = df[df[price_col] < 1000000]
        st.write('ราคาที่สนใจ ', price_fil)
        st.write('ทรัพย์ ในราคา', price_fil, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

    elif(price_fil == '1-2m'):
        info = df[(df[price_col] >= 1000000) & (df[price_col] <= 2000000)]
        st.write('ราคาที่สนใจ ', price_fil)
        st.write('ทรัพย์ ในราคา', price_fil, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

    elif(price_fil == '2-3m'):
        info = df[(df[price_col] > 2000000) & (df[price_col] <= 3000000)]
        st.write('ราคาที่สนใจ ', price_fil)
        st.write('ทรัพย์ ในราคา', price_fil, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

    elif(price_fil == '3-5m'):
        info = df[(df[price_col] > 3000000) & (df[price_col] <= 5000000)]
        st.write('ราคาที่สนใจ ', price_fil)
        st.write('ทรัพย์ ในราคา', price_fil, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

    elif(price_fil == '>5m'):
        info = df[df[price_col] > 5000000]
        st.write('ราคาที่สนใจ ', price_fil)
        st.write('ทรัพย์ ในราคา', price_fil, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

def map_by_zone(df, option, zone):
    if(zone == []):
        zone = zone_use
        for i in zone:
            info = df[df.zone == i]
            map_by_type(info, option)

    elif(zone != []):
        for i in zone:
            info = df[df.zone == i]
            map_by_type(info, option)
            st.write('ทรัพย์ทั้งหมดในโซน ', i, 'ตามเงื่อนไขที่เลือก ', len(info), ' ทรัพย์')

            st.write('ทรัพย์ทั้งหมดในโซน ตามเงื่อนไขที่เลือก', info[popup_list])
            st.markdown('''----''')

            co1, co2 = st.columns([2, 1])
            with co1:
                st.write('สัดส่วนทรัพย์แต่ละประเภทในโซน ตามเงื่อนไข')
                st.write(info[label_prop].value_counts())
                st.write('Pie chart')
                df = info
                val_key = df[label_prop].value_counts()
                fig = px.pie(df, values=val_key,
                             names = val_key.index)
                st.plotly_chart(fig, theme="streamlit")
            with co2:
                st.write('Bar chart')
                st.bar_chart(info[label_prop].value_counts())

def map_by_type(df, option):
    if(option == []):
        option = label
        for i in option:
            m.add_points_from_xy(
                df[df[label_prop] == i],
                x="longitude",
                y="latitude",
                color_column=label_prop,
                popup=popup_list,
                icon_names=[ic[i]],
                add_legend=False,
                layer_name=i
            )

    elif(option != []):
        for i in option:
            m.add_points_from_xy(
                df[df[label_prop] == i],
                x="longitude",
                y="latitude",
                color_column=label_prop,
                popup=popup_list,
                icon_names=[ic[i]],
                add_legend=False,
                layer_name=i
            )
            st.write(i, 'ตามเงื่อนไขที่เลือก มีทั้งหมด', len(df[df[label_prop] == i]), ' ทรัพย์')
            st.write(df[df[label_prop] == i])

st.markdown('''-------''')
# processing zone
# function for interest ROI
if (first_fil_num != 0)&(end_fil_num ==0):
        info = df[df[price_col] >= first_fil_num]
        st.write('ราคาเริ่มต้นที่กำหนด',first_fil_num)
        st.write('ทรัพย์ ในราคาเริ่มต้นที่กำหนด', first_fil_num, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

elif (first_fil_num == 0)&(end_fil_num !=0):
        info = df[df[price_col] <= end_fil_num]
        st.write('ราคาสุดท้ายที่กำหนด',end_fil_num)
        st.write('ทรัพย์ ในช่วงราคาสุดท้ายที่กำหนด', end_fil_num, 'ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)
elif (first_fil_num != 0)&(end_fil_num !=0):
        info = df[(df[price_col] <= end_fil_num) & (df[price_col] >= first_fil_num)]
        st.write('ช่วงราคาที่กำหนด',first_fil_num,' - ',end_fil_num)
        st.write('ทรัพย์ ในช่วงราคาที่กำหนด ทั้งหมด ', len(info), ' ทรัพย์')
        map_by_zone(info, option, zone)

elif (choice =='yes'):
    x = geo(datageo)    
    filt_data = df[(df.longitude >= x[0]) & (df.longitude <= x[2])]
    roi_data = filt_data[(filt_data.latitude >= x[1]) & (filt_data.latitude <= x[3])]
    #write data in ROI
    st.write("ทรัพย์ทั้งหมดในกรอบที่สนใจ")
    st.write(roi_data)
    map_by_price(roi_data, option, zone, price_fil)
    m.add_gdf(datageo,layer_name="box")

else:
    map_by_price(df, option, zone, price_fil)

#st.write(geo(datageo))
m.to_streamlit()

st.markdown('''-------''')
st.write('Calculator Section')

def price_to_ppv():
        st.session_state.pricepv = st.session_state.price/st.session_state.vas
def ppv_to_price():
        st.session_state.price = st.session_state.pricepv * st.session_state.vas

colu1,colu2,colu3 = st.columns(3)
with colu1:
    vas = st.number_input("Vas :",key="vas")
    
with colu2:
    price = st.number_input("Price :",key ='price',on_change=price_to_ppv)
with colu3:
    pricepsq = st.number_input("Price per Vas:",key='pricepv',on_change=ppv_to_price)

st.markdown('''-------''')





