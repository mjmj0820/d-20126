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
st.subheader("1. 장르별 영화 편수 (도넛 그래프)")

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
    f"**이 그래프로 알 수 있는 것:**\n\n"
    f"- **그래프 특성:** 도넛 그래프는 전체에서 각 범주(장르)가 차지하는 비중과 비율을 한눈에 파악하고 비교하기에 적합합니다.\n"
    f"- **데이터 분석:** 개봉한 영화 중 **{top_genre}** 장르가 총 {top_count}편({top_ratio:.1f}%)으로 가장 높은 비중을 차지하고 있습니다."
)

st.divider()

# ==========================================
# 두 번째 그래프: 장르 및 영화별 총 관객 수 (트리맵)
# ==========================================
st.subheader("2. 장르 및 영화별 총 관객 수 (트리맵)")

# 트리맵용 데이터 전처리
df_tree = df.dropna(subset=["genre", "movieNm", "total_audi"]).copy()
df_tree["total_audi"] = pd.to_numeric(df_tree["total_audi"], errors="coerce")
df_tree = df_tree[df_tree["total_audi"] > 0]

# 동일 장르/영화명 중복 항목 합산 처리
df_tree = (
    df_tree.groupby(["genre", "movieNm"], as_index=False)["total_audi"].sum()
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
    f"**이 그래프로 알 수 있는 것:**\n\n"
    f"- **그래프 특성:** 트리맵 그래프는 상위 계층(장르)과 하위 계층(영화) 구조를 직관적으로 표현하며, 각 항목의 관객 수 규모를 사각형 면적으로 비교하는 데 유용합니다.\n"
    f"- **데이터 분석:** 총 관객 동원력이 가장 높은 장르는 **{top_audi_genre}**이며, 단일 영화 기준으로는 **{top_movie_name}**(약 {top_movie_audi:,.0f}만 명)이 가장 큰 비중을 차지하고 있습니다."
)

st.divider()

# ==========================================
# 세 번째 그래프: 총 관객 수 분포 (히스토그램)
# ==========================================
st.subheader("3. 총 관객 수 분포 (히스토그램)")

# 히스토그램용 데이터 전처리
df_hist = df.dropna(subset=["total_audi"]).copy()
df_hist["total_audi"] = pd.to_numeric(df_hist["total_audi"], errors="coerce")
df_hist = df_hist[df_hist["total_audi"] > 0]

# 히스토그램 그래프 생성
fig3 = px.histogram(
    df_hist,
    x="total_audi",
    nbins=20,
    labels={"total_audi": "총 관객 수", "count": "영화 편수"},
)

fig3.update_traces(
    hovertemplate="<b>총 관객 수 구간</b>: %{x}명<br><b>영화 편수</b>: %{y}편<extra></extra>"
)

fig3.update_layout(
    xaxis_title="총 관객 수 (명)", yaxis_title="영화 편수 (개)", bargap=0.1
)

st.plotly_chart(fig3, use_container_width=True)

# 인사이트 자동 계산
max_audi = int(df_hist["total_audi"].max())
bin_size = 1000000  # 100만 명
bins = list(range(0, max_audi + bin_size, bin_size))
labels = [f"{i//10000}~{(i+bin_size)//10000}만 명" for i in bins[:-1]]

df_hist["audi_range"] = pd.cut(
    df_hist["total_audi"], bins=bins, labels=labels, include_lowest=True
)
most_frequent_range = df_hist["audi_range"].mode()[0]
most_frequent_count = df_hist["audi_range"].value_counts().max()

top_movie_hist = df_hist.loc[df_hist["total_audi"].idxmax()]
top_movie_hist_name = top_movie_hist["movieNm"]
top_movie_hist_audi = top_movie_hist["total_audi"] / 10000

st.info(
    f"**이 그래프로 알 수 있는 것:**\n\n"
    f"- **그래프 특성:** 히스토그램은 수치형 연속 데이터의 전체적인 분포 형태, 쏠림 정도, 특정 구간으로의 밀집 상태를 확인하기에 적합합니다.\n"
    f"- **데이터 분석:** 대부분의 영화({most_frequent_count}편)가 **{most_frequent_range}** 구간에 몰려 있으며, 가장 많은 관객을 동원한 영화는 **{top_movie_hist_name}**(약 {top_movie_hist_audi:,.0f}만 명)입니다."
)

st.divider()

# ==========================================
# 네 번째 그래프: 개봉일 스크린 수 vs 총 관객 수 (산점도)
# ==========================================
st.subheader("4. 개봉일 스크린 수 vs 총 관객 수 (산점도)")

# 산점도용 데이터 전처리
df_scatter = df.dropna(
    subset=["first_scrn", "total_audi", "genre", "movieNm"]
).copy()
df_scatter["first_scrn"] = pd.to_numeric(
    df_scatter["first_scrn"], errors="coerce"
)
df_scatter["total_audi"] = pd.to_numeric(
    df_scatter["total_audi"], errors="coerce"
)
df_scatter = df_scatter[
    (df_scatter["first_scrn"] > 0) & (df_scatter["total_audi"] > 0)
]

# 산점도 그래프 생성
fig4 = px.scatter(
    df_scatter,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "genre": "장르",
    },
)

fig4.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린 수: %{x:,}개<br>총 관객 수: %{y:,}명<extra></extra>"
)

fig4.update_layout(
    xaxis_title="개봉일 스크린 수 (개)",
    yaxis_title="총 관객 수 (명)",
)

st.plotly_chart(fig4, use_container_width=True)

# 인사이트 자동 계산
corr = df_scatter["first_scrn"].corr(df_scatter["total_audi"])
corr_text = (
    "강한 양의 상관관계"
    if corr > 0.7
    else "뚜렷한 양의 상관관계"
    if corr > 0.4
    else "약한 상관관계"
)

st.info(
    f"**이 그래프로 알 수 있는 것:**\n\n"
    f"- **그래프 특성:** 산점도(Scatter Plot)는 두 연속형 변수 간의 관계(상관관계, 경향성, 아웃라이어)를 시각화하고 그룹별(장르별) 분포 차이를 파악하는 데 적합합니다.\n"
    f"- **데이터 분석:** 개봉일 스크린 수와 총 관객 수 간에는 **{corr_text}(상관계수 r ≈ {corr:.2f})**가 관찰되며, 초기 스크린 수를 많이 확보할수록 최종 관객 수가 증가하는 경향이 있음을 보여줍니다."
)

st.divider()

# ==========================================
# 다섯 번째 그래프: 주요 장르별 총 관객 수 분포 (상자 그림)
# ==========================================
st.subheader("5. 주요 장르별 총 관객 수 분포 (상자 그림)")

# 영화가 10편 이상인 장르만 필터링
genre_counts_all = df["genre"].value_counts()
valid_genres = genre_counts_all[genre_counts_all >= 10].index

df_box = df[df["genre"].isin(valid_genres)].copy()
df_box["total_audi"] = pd.to_numeric(df_box["total_audi"], errors="coerce")
df_box = df_box.dropna(subset=["genre", "total_audi", "movieNm"])

# 상자 그림 생성 (hover_name에 영화명 지정하여 이상치 점에 마우스 올릴 때 표출)
fig5 = px.box(
    df_box,
    x="genre",
    y="total_audi",
    hover_name="movieNm",
    points="outliers",
    labels={
        "genre": "장르",
        "total_audi": "총 관객 수",
    },
)

fig5.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>총 관객 수: %{y:,}명<extra></extra>"
)

fig5.update_layout(
    xaxis_title="장르 (10편 이상 개봉)",
    yaxis_title="총 관객 수 (명)",
)

st.plotly_chart(fig5, use_container_width=True)

# 인사이트 자동 계산
median_by_genre = (
    df_box.groupby("genre")["total_audi"].median().sort_values(ascending=False)
)
top_median_genre = median_by_genre.index[0]
top_median_val = median_by_genre.iloc[0] / 10000

top_outlier_row = df_box.loc[df_box["total_audi"].idxmax()]
top_outlier_movie = top_outlier_row["movieNm"]
top_outlier_genre = top_outlier_row["genre"]
top_outlier_audi = top_outlier_row["total_audi"] / 10000

st.info(
    f"**이 그래프로 알 수 있는 것:**\n\n"
    f"- **그래프 특성:** 상자 그림(Box Plot)은 범주별 데이터의 중앙값, 사분위수(분포 범위), 그리고 평균적인 범위를 크게 벗어난 이상치(Outlier)를 비교하기에 적합합니다.\n"
    f"- **데이터 분석:** 10편 이상 개봉한 장르 중 중앙값 기준 관객 동원력이 가장 높은 장르는 **{top_median_genre}**(중앙값 약 {top_median_val:,.0f}만 명)이며, **{top_outlier_genre}** 장르의 **{top_outlier_movie}**(약 {top_outlier_audi:,.0f}만 명)가 가장 두드러진 아웃라이어로 나타납니다."
)

st.divider()
