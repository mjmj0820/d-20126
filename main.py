import streamlit as st
import pandas as pd
import plotly.express as px

# 웹페이지의 제목과 레이아웃 넓게 쓰기 설정
st.set_page_config(page_title="영화 박스오피스 대시보드", layout="wide")

st.title("🎬 영화 박스오피스 데이터 분석")
st.write("원하는 영화를 선택해서 관객수 변화를 확인해 보세요!")

# [1. 데이터 불러오기]
# @st.cache_data 데코레이터: 데이터를 한 번만 불러오고 메모리에 저장(캐싱)해 둡니다.
# 버튼을 누르거나 화면이 새로고침될 때마다 무거운 데이터를 다시 다운로드하지 않게 해줍니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    # pandas를 이용해 URL에 있는 CSV 파일을 읽어옵니다.
    df = pd.read_csv(url)
    return df

# 데이터 불러오기 실행
df = load_data()


# [2. 날짜 전처리]
# 2-1. 결측치(비어있는 값)가 포함된 행은 깔끔하게 삭제합니다.
df = df.dropna()

# 2-2. 글자(문자열)로 되어있는 "기준일자"를 진짜 날짜(datetime) 형식으로 바꿔줍니다. 
# 그래야 그래프에서 시간의 흐름대로 올바르게 그려집니다.
df['기준일자'] = pd.to_datetime(df['기준일자'])

# 2-3. 전체 데이터를 기준일자(과거->최신) 순서대로 정렬합니다.
df = df.sort_values('기준일자')


# [3. 영화 선택 기능]
# 영화 목록을 '누적관객수'가 많은 순서(내림차순)로 보여주기 위해 정렬 기준을 만듭니다.
# 각 영화별로 가장 마지막 날의(가장 큰) 누적관객수를 구합니다.
movie_max_audience = df.groupby('영화명')['누적관객수'].max()

# 누적관객수가 큰 순서대로 정렬한 뒤, 영화 이름만 리스트(목록)로 뽑아냅니다.
sorted_movie_list = movie_max_audience.sort_values(ascending=False).index.tolist()

# 화면에 드롭다운(선택 상자)을 만들고, 정렬된 영화 목록을 넣습니다.
selected_movie = st.selectbox("📊 차트로 확인할 영화를 선택하세요:", sorted_movie_list)

# 사용자가 선택한 영화의 데이터만 골라냅니다 (필터링)
filtered_df = df[df['영화명'] == selected_movie]


# [5. 기타 - 구역 나누기]
st.divider() # 가로줄을 그어 구역을 나눕니다.

# --- 첫 번째 그래프 구역 ---
st.subheader("1. 일별 관객수 변화 추이 (선 그래프)")

# [4. 선그래프 그리기]
# Plotly를 이용해 선 그래프를 만듭니다. x축은 날짜, y축은 해당일 관객수로 설정합니다.
fig1 = px.line(
    filtered_df, 
    x='기준일자', 
    y='해당일관객수', 
    title=f"'{selected_movie}' 해당일관객수 변화",
    markers=True # 꺾이는 부분에 점을 찍어 더 보기 좋게 만듭니다.
)

# 완성된 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig1, use_container_width=True)

# 그래프 아래에 인사이트를 적을 수 있는 문구 자리를 만듭니다.
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 관객수 증감 특징이나 개봉 후 인기도 변화를 한 문장으로 적어주세요)*")


st.divider() # 가로줄

# --- 두 번째 그래프 구역 ---
st.subheader("2. 누적 관객수 변화 추이 (영역 차트)")

# [추가된 영역 차트 그리기]
# Plotly를 이용해 영역 차트를 만듭니다. x축은 날짜, y축은 누적관객수로 설정합니다.
# 선 그래프 아래 공간이 색칠되어 데이터가 쌓여가는 느낌을 시각적으로 잘 보여줍니다.
fig2 = px.area(
    filtered_df, 
    x='기준일자', 
    y='누적관객수', 
    title=f"'{selected_movie}' 누적관객수 변화"
)

# 완성된 두 번째 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig2, use_container_width=True)

# 두 번째 그래프 아래에 인사이트를 적을 수 있는 문구 자리를 만듭니다.
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 개봉 이후 누적관객수가 어떻게 쌓여가는지, 어느 시점에 관객이 크게 늘었는지 한 문장으로 적어주세요)*")
