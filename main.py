import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 데이터 그래프", layout="wide")

st.title("영화 데이터 그래프")


# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)

    # 장르 전처리: 세로막대(|) 기호로 여러 개 적힌 경우 첫 번째 장르만 추출
    df["genre"] = df["genre"].apply(
        lambda x: str(x).split("|")[0] if pd.notnull(x) else x
    )

    return df


# 데이터 불러오기
df = load_data()

# ==========================================
# 첫 번째 그래프: 장르별 영화 편수 (도넛 그래프)
# ==========================================
st.subheader("1. 장르별 영화 편수")

# 장르별 편수 집계
genre_counts = df["genre"].value_counts().reset_index()
genre_counts.columns = ["장르", "편수"]

# 플롯리 도넛 그래프 생성 (hole 파라미터로 도넛 형태 구현)
fig1 = px.pie(
    genre_counts,
    values="편수",
    names="장르",
    hole=0.4,
)

# 마우스를 올렸을 때(Hover) 편수와 비율이 보이도록 툴팁 템플릿 설정
fig1.update_traces(
    textposition="inside",
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>",
)

# 그래프 출력
st.plotly_chart(fig1, use_container_width=True)

# 인사이트 작성란
st.info(
    "**이 그래프로 알 수 있는 것:** (이곳에 그래프에서 얻을 수 있는 핵심 인사이트 한 문장을 적어주세요.)"
)

# 구역 나누기
st.divider()
