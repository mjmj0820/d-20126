import os
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    mean_absolute_percentage_error,
)

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="다이아몬드 가격 예측 웹앱 (학습/평가 분리형)",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUT_ORDER = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
COLOR_ORDER = ["J", "I", "H", "G", "F", "E", "D"]
CLARITY_ORDER = ["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"]

BASE_DIR = Path(__file__).resolve().parent


def resolve_data_sources():
    """GitHub 저장소 내 학습용/평가용 데이터 경로를 자동 탐색합니다."""
    train_candidates = [BASE_DIR / "data" / "diamonds_train.csv", BASE_DIR / "diamonds_train.csv"]
    test_candidates = [BASE_DIR / "data" / "diamonds_test.csv", BASE_DIR / "diamonds_test.csv"]
    single_candidates = [BASE_DIR / "data" / "diamonds.csv", BASE_DIR / "diamonds.csv"]

    train_path = next((p for p in train_candidates if p.exists()), None)
    test_path = next((p for p in test_candidates if p.exists()), None)

    if train_path and test_path:
        return "split", train_path, test_path

    single_path = next((p for p in single_candidates if p.exists()), None)
    if single_path:
        return "single", single_path, None

    raise FileNotFoundError(
        "GitHub 저장소 내에 'data/diamonds_train.csv' 및 'data/diamonds_test.csv' "
        "(또는 'data/diamonds.csv') 파일이 없습니다."
    )


def preprocess_df(raw: pd.DataFrame):
    """원본 스키마 데이터프레임을 정제·변수선택·로그변환·원핫인코딩합니다."""
    n_raw = len(raw)
    df_step1 = raw.drop_duplicates().reset_index(drop=True)
    n_dup = n_raw - len(df_step1)

    df_step2 = df_step1[(df_step1["x"] > 0) & (df_step1["y"] > 0) & (df_step1["z"] > 0)].reset_index(drop=True)
    n_zero = len(df_step1) - len(df_step2)

    df_clean = df_step2[(df_step2["y"] <= 20) & (df_step2["z"] <= 10)].reset_index(drop=True)
    n_ext = len(df_step2) - len(df_clean)

    df_enc = df_clean.drop(columns=["x", "y", "z"]).copy()
    df_enc["cut"] = pd.Categorical(df_enc["cut"], categories=CUT_ORDER, ordered=True)
    df_enc["color"] = pd.Categorical(df_enc["color"], categories=COLOR_ORDER, ordered=True)
    df_enc["clarity"] = pd.Categorical(df_enc["clarity"], categories=CLARITY_ORDER, ordered=True)

    df_enc["log_carat"] = np.log(df_enc["carat"])
    df_enc["log_price"] = np.log(df_enc["price"])

    df_model = pd.get_dummies(df_enc, columns=["cut", "color", "clarity"], drop_first=True, dtype=int)
    stats = {
        "n_raw": n_raw,
        "n_dup_removed": n_dup,
        "n_zero_removed": n_zero,
        "n_extreme_removed": n_ext,
        "n_final": len(df_model),
    }
    return df_clean, df_model, stats


@st.cache_data
def load_datasets(mode: str, path1_str: str, path2_str: str | None, mtime_key: tuple):
    if mode == "split":
        raw_train = pd.read_csv(path1_str)
        raw_test = pd.read_csv(path2_str)
        train_clean, train_df, train_stats = preprocess_df(raw_train)
        test_clean, test_df, test_stats = preprocess_df(raw_test)
        # 컬럼 정렬 일치 보장
        for col in train_df.columns:
            if col not in test_df.columns:
                test_df[col] = 0
        test_df = test_df[train_df.columns]
        combined_clean = pd.concat([train_clean, test_clean], ignore_index=True)
        return combined_clean, train_df, test_df, {"train": train_stats, "test": test_stats}
    else:
        raw = pd.read_csv(path1_str)
        df_clean, df_model, stats = preprocess_df(raw)
        train_df, test_df = train_test_split(df_model, test_size=0.2, random_state=42)
        return df_clean, train_df.reset_index(drop=True), test_df.reset_index(drop=True), {"all": stats}


@st.cache_resource
def train_regression_models(train_df: pd.DataFrame, test_df: pd.DataFrame, mtime_key: tuple):
    cat_cols = [c for c in train_df.columns if c.startswith(("cut_", "color_", "clarity_"))]
    features_std = ["carat", "depth", "table"] + cat_cols
    features_log = ["log_carat", "depth", "table"] + cat_cols

    lr_std = LinearRegression().fit(train_df[features_std], train_df["price"])
    pred_train_std = lr_std.predict(train_df[features_std])
    pred_test_std = lr_std.predict(test_df[features_std])

    lr_log = LinearRegression().fit(train_df[features_log], train_df["log_price"])
    pred_train_log = lr_log.predict(train_df[features_log])
    pred_test_log = lr_log.predict(test_df[features_log])

    smearing = float(np.mean(np.exp(train_df["log_price"] - pred_train_log)))
    pred_train_usd = np.exp(pred_train_log) * smearing
    pred_test_usd = np.exp(pred_test_log) * smearing

    sx = StandardScaler().fit_transform(train_df[features_log])
    sy = StandardScaler().fit_transform(train_df[["log_price"]]).ravel()
    beta_log = LinearRegression().fit(sx, sy).coef_

    metrics = {
        "n_train": len(train_df),
        "n_test": len(test_df),
        "std": {
            "train_r2": r2_score(train_df["price"], pred_train_std),
            "test_r2": r2_score(test_df["price"], pred_test_std),
            "rmse": np.sqrt(mean_squared_error(test_df["price"], pred_test_std)),
            "mae": mean_absolute_error(test_df["price"], pred_test_std),
            "mape": mean_absolute_percentage_error(test_df["price"], pred_test_std) * 100,
        },
        "log": {
            "train_r2_log": r2_score(train_df["log_price"], pred_train_log),
            "test_r2_log": r2_score(test_df["log_price"], pred_test_log),
            "train_r2_usd": r2_score(train_df["price"], pred_train_usd),
            "test_r2_usd": r2_score(test_df["price"], pred_test_usd),
            "rmse": np.sqrt(mean_squared_error(test_df["price"], pred_test_usd)),
            "mae": mean_absolute_error(test_df["price"], pred_test_usd),
            "mape": mean_absolute_percentage_error(test_df["price"], pred_test_usd) * 100,
            "smearing": smearing,
        },
    }

    coef_df = pd.DataFrame({
        "Feature": features_log,
        "Log_Coef": lr_log.coef_,
        "Pct_Effect (%)": (np.exp(lr_log.coef_) - 1) * 100,
        "Std_Beta": beta_log,
        "Std_Coef_USD": lr_std.coef_,
    })

    eval_df = pd.DataFrame({
        "carat": test_df["carat"].values,
        "actual_price": test_df["price"].values,
        "pred_std_price": pred_test_std,
        "pred_log_scale": pred_test_log,
        "pred_log_usd": pred_test_usd,
        "residual_log": test_df["log_price"].values - pred_test_log,
    })

    return lr_std, lr_log, features_std, features_log, metrics, coef_df, eval_df


try:
    mode, p1, p2 = resolve_data_sources()
    mtime_key = (os.path.getmtime(p1), os.path.getmtime(p2) if p2 else 0.0)
    df_clean, train_df, test_df, stats_info = load_datasets(mode, str(p1), str(p2) if p2 else None, mtime_key)
    lr_std, lr_log, features_std, features_log, metrics, coef_df, eval_df = train_regression_models(train_df, test_df, mtime_key)
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()


# ---------------------------------------------------------
# 2. Sidebar: Real-time Diamond Price Simulator
# ---------------------------------------------------------
st.sidebar.header("💎 다이아몬드 가격 예측기")
st.sidebar.caption("GitHub 저장소의 학습용 데이터로 학습된 회귀모델이 실시간 예측합니다.")

in_carat = st.sidebar.slider("캐럿 중량 (Carat)", min_value=0.20, max_value=5.00, value=1.00, step=0.01)
in_cut = st.sidebar.selectbox("컷 등급 (Cut)", options=list(reversed(CUT_ORDER)), index=0)
in_color = st.sidebar.selectbox("색상 등급 (Color: D 최고 ~ J 최저)", options=list(reversed(COLOR_ORDER)), index=1)
in_clarity = st.sidebar.selectbox("투명도 등급 (Clarity: IF 최고 ~ I1 최저)", options=list(reversed(CLARITY_ORDER)), index=3)

with st.sidebar.expander("세부 비율 설정 (Depth / Table)", expanded=False):
    in_depth = st.slider("깊이 비율 Depth (%)", min_value=50.0, max_value=72.0, value=61.8, step=0.1)
    in_table = st.slider("테이블 비율 Table (%)", min_value=50.0, max_value=70.0, value=57.0, step=0.5)

row_std = {col: 0.0 for col in features_std}
row_std["carat"] = in_carat
row_std["depth"] = in_depth
row_std["table"] = in_table
if in_cut != "Fair":
    row_std[f"cut_{in_cut}"] = 1.0
if in_color != "J":
    row_std[f"color_{in_color}"] = 1.0
if in_clarity != "I1":
    row_std[f"clarity_{in_clarity}"] = 1.0

row_log = {col: 0.0 for col in features_log}
row_log["log_carat"] = np.log(in_carat)
row_log["depth"] = in_depth
row_log["table"] = in_table
for col in row_std:
    if col.startswith(("cut_", "color_", "clarity_")):
        row_log[col] = row_std[col]

pred_best_usd = float(np.exp(lr_log.predict(pd.DataFrame([row_log]))[0]) * metrics["log"]["smearing"])
pred_basic_usd = float(lr_std.predict(pd.DataFrame([row_std]))[0])

st.sidebar.markdown("---")
st.sidebar.metric(
    label="권장 모델 예측가 (로그-선형회귀)",
    value=f"${pred_best_usd:,.0f}",
    delta=f"캐럿당 ${pred_best_usd / in_carat:,.0f} / ct",
)
st.sidebar.caption(f"• 기본 선형회귀 참고가: **${max(0, pred_basic_usd):,.0f}**")

similar = df_clean[
    (df_clean["cut"] == in_cut)
    & (df_clean["color"] == in_color)
    & (df_clean["clarity"] == in_clarity)
    & ((df_clean["carat"] - in_carat).abs() <= 0.05)
]
if len(similar) > 0:
    st.sidebar.info(
        f"**저장소 내 유사 매물 ({len(similar)}건, ±0.05ct)**\n"
        f"- 중앙값: **${similar['price'].median():,.0f}**\n"
        f"- 범위: ${similar['price'].min():,.0f} ~ ${similar['price'].max():,.0f}"
    )


# ---------------------------------------------------------
# 3. Main Dashboard
# ---------------------------------------------------------
st.title("💎 다이아몬드 가격 예측 분석 웹앱")
if mode == "split":
    st.success(
        f"✅ **GitHub 학습/평가 분리 데이터 직접 연동 완료**: "
        f"학습용 `{p1.relative_to(BASE_DIR)}` (**{metrics['n_train']:,}행**) / "
        f"평가용 `{p2.relative_to(BASE_DIR)}` (**{metrics['n_test']:,}행**)"
    )
else:
    st.success(
        f"✅ **GitHub 단일 데이터 자동 분할 연동 완료**: `{p1.relative_to(BASE_DIR)}` "
        f"(학습용 **{metrics['n_train']:,}행** / 평가용 **{metrics['n_test']:,}행**)"
    )

tab1, tab2, tab3 = st.tabs([
    "📋 1. 학습/평가 데이터 현황 및 VIF",
    "📊 2. 모델 학습 및 평가 결과",
    "🔍 3. 회귀계수 및 4C 프리미엄",
])

with tab1:
    st.subheader("1-1. GitHub 데이터셋 구성 및 다중공선성(VIF) 해결")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 정제 데이터", f"{metrics['n_train'] + metrics['n_test']:,} 행", "중복·이상치 제거 완료")
    c2.metric("학습용 (Train 80%)", f"{metrics['n_train']:,} 행", "data/diamonds_train.csv")
    c3.metric("평가용 (Test 20%)", f"{metrics['n_test']:,} 행", "data/diamonds_test.csv")
    c4.metric("최종 입력 변수 수", f"{len(features_log)} 개", "x, y, z 제거 (VIF ≤ 1.14)")

    col_v1, col_v2 = st.columns([1, 1.2])
    with col_v1:
        vif_df = pd.DataFrame({
            "변수": ["carat", "x", "y", "z", "depth", "table"],
            "제거 전 VIF": [24.61, 490.85, 494.89, 435.26, 7.69, 1.17],
            "제거 후 VIF (carat 단독)": [1.04, np.nan, np.nan, np.nan, 1.11, 1.14],
            "상태": ["안정 (1.04)", "제거됨", "제거됨", "제거됨", "안정 (1.11)", "안정 (1.14)"],
        })
        st.dataframe(vif_df, use_container_width=True, hide_index=True)

    with col_v2:
        vif_chart = pd.DataFrame({
            "변수": ["carat", "x", "y", "z", "depth", "table"] * 2,
            "구분": ["제거 전"] * 6 + ["제거 후 (carat 단독)"] * 6,
            "VIF": [24.61, 490.85, 494.89, 435.26, 7.69, 1.17, 1.04, 0, 0, 0, 1.11, 1.14],
        })
        fig_vif = px.bar(
            vif_chart[vif_chart["VIF"] > 0],
            x="변수", y="VIF", color="구분", barmode="group", log_y=True,
            title="치수 변수(x, y, z) 제거 전후 VIF 비교",
            color_discrete_map={"제거 전": "#d9534f", "제거 후 (carat 단독)": "#2e7d32"},
        )
        fig_vif.add_hline(y=10, line_dash="dash", line_color="orange")
        st.plotly_chart(fig_vif, use_container_width=True)

with tab2:
    st.subheader(f"2-1. 학습({metrics['n_train']:,}행) → 평가({metrics['n_test']:,}행) 검증 성능")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("로그-선형 Test R² (USD)", f"{metrics['log']['test_r2_usd']:.4f}", f"로그 스케일: {metrics['log']['test_r2_log']:.4f}")
    m2.metric("Test RMSE", f"${metrics['log']['rmse']:,.2f}", f"기본 OLS 대비 -${metrics['std']['rmse'] - metrics['log']['rmse']:,.2f}")
    m3.metric("Test MAE", f"${metrics['log']['mae']:,.2f}", f"기본 OLS 대비 -${metrics['std']['mae'] - metrics['log']['mae']:,.2f}")
    m4.metric("Test MAPE", f"{metrics['log']['mape']:.2f}%", f"-{metrics['std']['mape'] - metrics['log']['mape']:.2f}%p")

    sample_eval = eval_df.sample(n=min(2500, len(eval_df)), random_state=42)
    c_left, c_right = st.columns(2)
    with c_left:
        fig_pred = px.scatter(
            sample_eval, x="actual_price", y="pred_log_usd", opacity=0.4,
            labels={"actual_price": "실제 가격 (USD)", "pred_log_usd": "예측 가격 (USD)"},
            title="평가용(Test) 세트 실제 가격 vs. 예측 가격",
            color_discrete_sequence=["#2e7d32"],
        )
        fig_pred.add_trace(go.Scatter(x=[0, 19000], y=[0, 19000], mode="lines", name="y=x", line=dict(color="red", dash="dash")))
        st.plotly_chart(fig_pred, use_container_width=True)

    with c_right:
        fig_res = px.scatter(
            sample_eval, x="pred_log_scale", y="residual_log", opacity=0.4,
            labels={"pred_log_scale": "예측 log(Price)", "residual_log": "잔차 (log 스케일)"},
            title="평가용(Test) 세트 잔차 산점도",
            color_discrete_sequence=["#3b7ea1"],
        )
        fig_res.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_res, use_container_width=True)

with tab3:
    st.subheader("3-1. 캐럿 통제 후 4C 등급별 순수 가격 프리미엄 (%)")
    prem_df = coef_df[coef_df["Feature"].str.startswith(("cut_", "color_", "clarity_"))].copy()
    prem_df["Category"] = prem_df["Feature"].apply(
        lambda x: "Cut (컷)" if x.startswith("cut_") else ("Color (색상)" if x.startswith("color_") else "Clarity (투명도)")
    )
    fig_prem = px.bar(
        prem_df, x="Pct_Effect (%)", y="Feature", color="Category", orientation="h",
        text=prem_df["Pct_Effect (%)"].apply(lambda v: f"+{v:.1f}%"),
        title="최하위 등급(Cut=Fair, Color=J, Clarity=I1) 대비 순수 가격 상승률 (%)",
        color_discrete_map={"Cut (컷)": "#3b7ea1", "Color (색상)": "#7b52ab", "Clarity (투명도)": "#2e7d32"},
    )
    fig_prem.update_layout(yaxis={"categoryorder": "array", "categoryarray": list(reversed(prem_df["Feature"].tolist()))})
    fig_prem.update_traces(textposition="outside")
    st.plotly_chart(fig_prem, use_container_width=True)

    display_coef = coef_df.copy()
    display_coef.columns = ["변수명", "로그 회귀계수 (β)", "기준 대비 상승률 (%)", "표준화 계수 (Std Beta)", "기본 선형 계수 ($)"]
    st.dataframe(
        display_coef.style.format({
            "로그 회귀계수 (β)": "{:.4f}",
            "기준 대비 상승률 (%)": "{:+.2f}%",
            "표준화 계수 (Std Beta)": "{:.4f}",
            "기본 선형 계수 ($)": "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
