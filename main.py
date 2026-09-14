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

# 그래프 아래에 인사이트를 적습니다. (채워진 문구)
st.markdown("**💡 이 그래프로 알 수 있는 것:** 개봉 직후 관객이 얼마나 몰렸는지, 그리고 평일보다 주말에 관객수가 솟아오르는 특정한 패턴을 눈으로 직접 확인할 수 있습니다.")


st.divider() # 가로줄

# --- 두 번째 그래프 구역 ---
st.subheader("2. 누적 관객수 변화 추이 (영역 차트)")

# 영역 차트를 만듭니다. x축은 날짜, y축은 누적관객수로 설정합니다.
fig2 = px.area(
    filtered_df, 
    x='기준일자', 
    y='누적관객수', 
    title=f"'{selected_movie}' 누적관객수 변화"
)

# 완성된 두 번째 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig2, use_container_width=True)

# 두 번째 그래프 아래에 인사이트를 적습니다. (채워진 문구)
st.markdown("**💡 이 그래프로 알 수 있는 것:** 누적 관객수가 가파르게 오르다가 어느 시점부터 그래프가 평평해지는지를 통해, 이 영화의 흥행 열기가 언제쯤 식었는지 파악할 수 있습니다.")


st.divider() # 가로줄

# --- 세 번째 그래프 구역 ---
st.subheader("3. 20일 이상 진입한 흥행작 TOP 5 비교 (다중 선 그래프)")

# 3-1. 영화별로 데이터에 몇 번(며칠) 등장했는지 횟수를 셉니다.
movie_days_count = df['영화명'].value_counts()

# 3-2. 등장 횟수가 20일 이상인 영화들의 이름만 골라냅니다 (20일 미만 제외)
steady_movies = movie_days_count[movie_days_count >= 20].index

# 3-3. 앞에서 구했던 '영화별 최대 누적관객수' 데이터 중에서 20일 이상 등장한 영화들만 남깁니다.
steady_movie_max = movie_max_audience[movie_max_audience.index.isin(steady_movies)]

# 3-4. 그 중에서 누적관객수가 가장 높은 상위 5개 영화의 이름을 뽑아냅니다.
top5_steady_movies = steady_movie_max.sort_values(ascending=False).head(5).index.tolist()

# 3-5. 전체 데이터 중에서 이 5개 영화에 해당하는 데이터만 걸러냅니다.
top5_df = df[df['영화명'].isin(top5_steady_movies)]

# 3-6. Plotly를 이용해 여러 영화의 선을 동시에 그립니다.
fig3 = px.line(
    top5_df, 
    x='기준일자', 
    y='누적관객수', 
    color='영화명', 
    title="20일 이상 박스오피스 진입작 중 누적관객수 TOP 5 추이 비교"
)

# 완성된 세 번째 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig3, use_container_width=True)

# 세 번째 그래프 아래에 인사이트를 적습니다. (채워진 문구)
st.markdown("**💡 이 그래프로 알 수 있는 것:** 꾸준히 사랑받은 상위 5개 영화들의 최종 스코어 차이와, 초반에 빠르게 흥행했는지 아니면 뒷심을 발휘했는지 흥행 속도를 비교할 수 있습니다.")


st.divider() # 가로줄

# --- 네 번째 그래프 구역 ---
st.subheader("4. 극장가 전체 관객수 흐름 (7일 이동평균)")

# 4-1. '기준일자'별로 모든 영화의 '해당일관객수'를 더해서 그날 극장에 온 총 관객수를 구합니다.
daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()

# 4-2. 날짜별 총 관객수의 '7일 이동평균'을 구합니다. (최근 7일간의 평균값)
daily_total['7일_이동평균'] = daily_total['해당일관객수'].rolling(window=7).mean()

# 4-3. Plotly로 그래프를 그립니다. y축에 두 개의 값(원본, 이동평균)을 리스트로 넣어 동시에 그립니다.
fig4 = px.line(
    daily_total, 
    x='기준일자', 
    y=['해당일관객수', '7일_이동평균'],
    title="전체 박스오피스 일일 관객수 및 7일 이동평균선 추이",
    labels={'value': '관객수', 'variable': '그래프 종류'} # 범례 이름 변경
)

# 4-4. 원본 선은 연하게, 이동평균선은 진하고 두껍게 색상과 굵기를 수정합니다.
fig4.data[0].line.color = 'rgba(100, 149, 237, 0.4)' # 연한 파란색(투명도 0.4) 지정
fig4.data[0].name = '일일 총 관객수' # 범례 이름 변경

fig4.data[1].line.color = 'rgba(0, 0, 139, 1.0)'     # 진한 네이비색 지정
fig4.data[1].line.width = 3                          # 선을 조금 더 두껍게
fig4.data[1].name = '7일 이동평균' # 범례 이름 변경

# 완성된 네 번째 그래프를 스트림릿 화면에 출력합니다.
st.plotly_chart(fig4, use_container_width=True)

# 네 번째 그래프 아래에 인사이트를 적습니다. (채워진 문구)
st.markdown("**💡 이 그래프로 알 수 있는 것:** 삐쭉삐쭉한 일일 변동(주말 효과)을 걷어낸 진한 이동평균선을 통해, 1년 중 어느 시기(방학, 연휴 등)에 극장가 전체가 붐볐는지 진짜 추세를 알 수 있습니다.")
