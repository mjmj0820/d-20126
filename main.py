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

# 플롯리 도넛 그래프 생성
fig1 = px.pie(
    genre_counts,
    values="편수",
    names="장르",
    hole=0.4,
)

fig1.update_traces(
    textposition="inside",
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>",
)

st.plotly_chart(fig1, use_container_width=True)

# 인사이트 자동 계산 및 출력
top_genre = genre_counts.iloc[0]["장르"]
top_count = genre_counts.iloc[0]["편수"]
total_count = genre_counts["편수"].sum()
top_ratio = (top_count / total_count) * 100

st.info(
    f"**이 그래프로 알 수 있는 것:** 개봉한 영화 중 **{top_genre}** 장르가 총 {top_count}편({top_ratio:.1f}%)으로 가장 높은 비중을 차지하고 있습니다."
)

st.divider()

# ==========================================
# 두 번째 그래프: 장르 및 영화별 총 관객 수 (트리맵)
# ==========================================
st.subheader("2. 장르 및 영화별 총 관객 수")

# 트리맵용 데이터 전처리 (결측치 제거, 숫자 변환, 0 초과 값만 선택)
df_tree = df.dropna(subset=["genre", "movieNm", "total_audi"]).copy()
df_tree["total_audi"] = pd.to_numeric(df_tree["total_audi"], errors="coerce")
df_tree = df_tree[df_tree["total_audi"] > 0]

# 동일 장르/영화명 중복 항목 합산 처리
df_tree = (
    df_tree.groupby(["genre", "movieNm"], as_index=False)["total_audi"]
    .sum()
)

# 트리맵 그래프 생성
fig2 = px.treemap(
    df_tree,
    path=["genre", "movieNm"],
    values="total_audi",
)

fig2.update_traces(
    hovertemplate="<b>%{label}</b><br>총 관객 수: %{value:,}명<extra></extra>"
)

st.plotly_chart(fig2, use_container_width=True)

# 인사이트 자동 계산 및 출력
top_audi_genre = df_tree.groupby("genre")["total_audi"].sum().idxmax()
top_movie_row = df_tree.loc[df_tree["total_audi"].idxmax()]
top_movie_name = top_movie_row["movieNm"]
top_movie_audi = top_movie_row["total_audi"] / 10000

st.info(
    f"**이 그래프로 알 수 있는 것:** 총 관객 동원력이 가장 높은 장르는 **{top_audi_genre}**이며, 단일 영화 기준으로는 **{top_movie_name}**(약 {top_movie_audi:,.0f}만 명)이 가장 큰 비중을 차지하고 있습니다."
)

st.divider()
