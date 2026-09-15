# 필요한 라이브러리를 불러옵니다.
import streamlit as st
import pandas as pd
import plotly.express as px

# 앱의 제목을 설정합니다.
st.title("🎬 영화 박스오피스 데이터 분석")

# [1. 데이터 불러오기 및 2. 날짜 전처리]
# @st.cache_data를 사용하면 데이터를 한 번만 불러와서 저장해두고 계속 재사용합니다. (앱 속도 향상)
@st.cache_data
def load_data():
    # CSV 파일이 있는 웹 주소
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    
    # pandas를 사용해 주소에서 CSV 파일을 읽어옵니다.
    df = pd.read_csv(url)
    
    # 결측치(비어있는 값)가 포함된 행을 삭제합니다.
    df = df.dropna()
    
    # "기준일자" 컬럼을 텍스트에서 날짜(datetime) 형식으로 바꿔줍니다.
    df['기준일자'] = pd.to_datetime(df['기준일자'])
    
    # 전체 데이터를 "기준일자" 순서대로 정렬합니다. (과거 -> 최신)
    df = df.sort_values(by='기준일자')
    
    return df

# 함수를 실행하여 데이터를 가져옵니다.
df = load_data()


# [3. 영화 선택 기능]
# 영화별로 가장 높은 누적관객수를 구한 뒤, 내림차순(관객수가 많은 순)으로 정렬합니다.
movie_audience_max = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False)

# 정렬된 영화 이름만 뽑아서 리스트(목록)로 만듭니다. 중복도 자동으로 제거됩니다.
movie_list = movie_audience_max.index.tolist()

# 사용자가 영화를 선택할 수 있는 드롭다운 메뉴를 만듭니다.
selected_movie = st.selectbox("👇 분석할 영화를 선택해 주세요:", movie_list)

# 전체 데이터에서 사용자가 선택한 영화의 데이터만 추려냅니다.
filtered_df = df[df['영화명'] == selected_movie]


st.divider() # 화면에 가로줄을 그어 구역을 나눕니다.


# [4. 선그래프 그리기 및 5. 기타 (구역 나누기, 문구 자리)]
st.header("📈 1. 일별 관객수 변화 그래프")

# Plotly를 이용해 선 그래프를 그립니다. (x축: 날짜, y축: 해당일관객수)
fig1 = px.line(
    filtered_df, 
    x='기준일자', 
    y='해당일관객수', 
    title=f"[{selected_movie}] 일별 관객수 추이",
    markers=True # 꺾이는 부분에 점을 찍어줍니다.
)

# 화면에 그래프를 출력합니다.
st.plotly_chart(fig1, use_container_width=True)

# 그래프 아래에 '이 그래프로 알 수 있는 것' 문구를 넣을 자리를 마련합니다.
st.info("💡 **이 그래프로 알 수 있는 것:** (예: 개봉 첫 주말에 관객수가 가장 많았으며, 이후 점차 감소하는 추세를 보입니다.)")


st.divider() # 화면에 가로줄을 그어 구역을 나눕니다.


# [앞으로 추가할 그래프 구역]
st.header("📊 2. 추가 분석 그래프 (예정)")

st.write("이곳에 새로운 그래프를 추가할 수 있습니다. (예: 누적관객수 변화, 매출액 비교 등)")

# 임시 그래프 자리 안내
# fig2 = px.bar(...)
# st.plotly_chart(fig2, use_container_width=True)

st.info("💡 **이 그래프로 알 수 있는 것:** (새로운 그래프에 대한 해석을 여기에 적어주세요.)")
