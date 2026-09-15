import streamlit as st
import pandas as pd
import plotly.express as px

# 웹페이지의 제목과 레이아웃 넓게 쓰기 설정
st.set_page_config(page_title="영화 박스오피스 대시보드", layout="wide")

st.title("🎬 영화 박스오피스 데이터 분석")
st.write("원하는 영화를 선택해서 관객수 변화를 확인해 보세요!")

# [1. 데이터 불러오기]
# @st.cache_data 데코레이터: 데이터를 한 번만 불러오고 메모리에 저장(캐싱)해 둡니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    return df

# 데이터 불러오기 실행
df = load_data()


# [2. 날짜 전처리]
# 2-1. 결측치 삭제
df = df.dropna()

# 2-2. "기준일자"를 진짜 날짜(datetime) 형식으로 변경
df['기준일자'] = pd.to_datetime(df['기준일자'])

# 2-3. 과거->최신 순서대로 정렬
df = df.sort_values('기준일자')


# [3. 영화 선택 기능]
# 영화별 누적관객수 최댓값 구하기
movie_max_audience = df.groupby('영화명')['누적관객수'].max()

# 내림차순 정렬 후 영화 이름만 리스트로 추출
sorted_movie_list = movie_max_audience.sort_values(ascending=False).index.tolist()

# 드롭다운 생성
selected_movie = st.selectbox("📊 차트로 확인할 영화를 선택하세요:", sorted_movie_list)

# 선택한 영화 데이터만 필터링
filtered_df = df[df['영화명'] == selected_movie]


# [5. 기타 - 구역 나누기]
st.divider() # 가로줄

# --- 첫 번째 그래프 구역 ---
st.subheader("1. 일별 관객수 변화 추이 (선 그래프)")

fig1 = px.line(
    filtered_df, 
    x='기준일자', 
    y='해당일관객수', 
    title=f"'{selected_movie}' 해당일관객수 변화",
    markers=True 
)
st.plotly_chart(fig1, use_container_width=True)

# 그래프 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 관객수 증감 특징이나 개봉 후 인기도 변화를 한 문장으로 적어주세요)*")


st.divider() # 가로줄

# --- 두 번째 그래프 구역 ---
st.subheader("2. 누적 관객수 변화 추이 (영역 차트)")

fig2 = px.area(
    filtered_df, 
    x='기준일자', 
    y='누적관객수', 
    title=f"'{selected_movie}' 누적관객수 변화"
)
st.plotly_chart(fig2, use_container_width=True)

# 두 번째 그래프 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 개봉 이후 누적관객수가 어떻게 쌓여가는지, 어느 시점에 관객이 크게 늘었는지 한 문장으로 적어주세요)*")


st.divider() # 가로줄

# --- 세 번째 그래프 구역 ---
st.subheader("3. 20일 이상 진입한 흥행작 TOP 5 비교 (다중 선 그래프)")

movie_days_count = df['영화명'].value_counts()
steady_movies = movie_days_count[movie_days_count >= 20].index
steady_movie_max = movie_max_audience[movie_max_audience.index.isin(steady_movies)]
top5_steady_movies = steady_movie_max.sort_values(ascending=False).head(5).index.tolist()
top5_df = df[df['영화명'].isin(top5_steady_movies)]

fig3 = px.line(
    top5_df, 
    x='기준일자', 
    y='누적관객수', 
    color='영화명', 
    title="20일 이상 박스오피스 진입작 중 누적관객수 TOP 5 추이 비교"
)
st.plotly_chart(fig3, use_container_width=True)

# 세 번째 그래프 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 꾸준히 사랑받은 상위 5개 영화들의 관객수 증가 추이가 어떻게 다른지 비교해서 적어주세요)*")


st.divider() # 가로줄

# --- 네 번째 그래프 구역 ---
st.subheader("4. 극장가 전체 관객수 흐름 (7일 이동평균)")

daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()
daily_total['7일_이동평균'] = daily_total['해당일관객수'].rolling(window=7).mean()

fig4 = px.line(
    daily_total, 
    x='기준일자', 
    y=['해당일관객수', '7일_이동평균'],
    title="전체 박스오피스 일일 관객수 및 7일 이동평균선 추이",
    labels={'value': '관객수', 'variable': '그래프 종류'} 
)
fig4.data[0].line.color = 'rgba(100, 149, 237, 0.4)' 
fig4.data[0].name = '일일 총 관객수' 
fig4.data[1].line.color = 'rgba(0, 0, 139, 1.0)'     
fig4.data[1].line.width = 3                          
fig4.data[1].name = '7일 이동평균' 

st.plotly_chart(fig4, use_container_width=True)

# 네 번째 그래프 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**💡 이 그래프로 알 수 있는 것:** *(여기에 특정 시기(예: 명절, 연휴, 방학)에 극장가 전체에 관객이 어떻게 몰렸는지 추세를 한 문장으로 적어주세요)*")


st.divider() # 가로줄

# --- 다섯 번째 그래프 구역 ---
st.subheader("5. 월별 극장가 총 관객수 (막대그래프)")

daily_total['연월'] = daily_total['기준일자'].dt.strftime('%Y-%m')
monthly_total = daily_total.groupby('연월')['해당일관객수'].sum().reset_index()

fig5 = px.bar(
    monthly_total,
    x='연월',
    y='해당일관객수',
    title="월별 전체 박스오피스 관객수 합계",
    text_auto='.2s' 
)

st.plotly_chart(fig5, use_container_width=True)

# 다섯 번째 막대그래프 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**🔍 막대 그래프로 알 수 있는 것:** *(여기에 월별 성수기와 비수기의 차이나 전체적인 흐름을 한 문장으로 적어주세요)*")


st.divider() # 가로줄

# --- 여섯 번째 그래프 구역 (새로 추가된 캘린더 히트맵) ---
st.subheader("6. 요일/주차별 관객수 히트맵")

# [추가된 캘린더 히트맵 데이터 처리 및 그리기]
# 6-1. 날짜에서 요일 정보 추출 (월=0 ~ 일=6)
day_mapping = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
daily_total['요일번호'] = daily_total['기준일자'].dt.weekday
daily_total['요일'] = daily_total['요일번호'].map(day_mapping)

# 6-2. 날짜에서 주차 정보 추출 (예: 2023-W01)
iso_cal = daily_total['기준일자'].dt.isocalendar()
daily_total['연도_주차'] = iso_cal['year'].astype(str) + "-W" + iso_cal['week'].astype(str).str.zfill(2)

# 6-3. 마우스 오버(hover) 시 띄워줄 'yyyy-mm-dd' 문자열 생성
daily_total['날짜문자열'] = daily_total['기준일자'].dt.strftime('%Y-%m-%d')

# 6-4. 2차원 표(피벗 테이블) 생성 - 관객수(z값)용 데이터
heatmap_data = daily_total.pivot(index='요일', columns='연도_주차', values='해당일관객수')

# 6-5. 2차원 표(피벗 테이블) 생성 - 툴팁(마우스 오버)용 텍스트 데이터
heatmap_text = daily_total.pivot(index='요일', columns='연도_주차', values='날짜문자열')

# 6-6. 요일이 월~일 순서대로 나오도록 정렬 축 재배치
day_order = ['월', '화', '수', '목', '금', '토', '일']
heatmap_data = heatmap_data.reindex(day_order)
heatmap_text = heatmap_text.reindex(day_order)

# 6-7. Plotly의 imshow()를 사용해 히트맵 그리기
fig6 = px.imshow(
    heatmap_data,
    labels=dict(x="연도-주차", y="요일", color="일일 관객수"),
    x=heatmap_data.columns,
    y=heatmap_data.index,
    color_continuous_scale="Blues", # 색이 진할수록 관객이 많음을 표현
    aspect="auto",
    title="요일 및 주차별 전체 관객수 분포 (캘린더 히트맵)"
)

# 6-8. 마우스 올렸을 때 표시할 내용(호버 템플릿) 사용자 정의
# customdata에 미리 만들어둔 날짜문자열(yyyy-mm-dd) 표를 넣어서 불러옵니다.
fig6.update_traces(
    customdata=heatmap_text,
    hovertemplate="날짜: %{customdata}<br>요일: %{y}<br>관객수: %{z:,.0f}명<extra></extra>"
)

# 완성된 여섯 번째 그래프 화면 출력
st.plotly_chart(fig6, use_container_width=True)

# 여섯 번째 히트맵 아래에 인사이트를 적을 수 있는 문구 자리 (빈칸)
st.markdown("**💡 이 히트맵으로 알 수 있는 것:** *(여기에 어떤 요일에 관객이 가장 집중되는지, 연휴가 있던 주간의 패턴 변화 등을 한 문장으로 적어주세요)*")
