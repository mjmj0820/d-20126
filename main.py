import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 페이지 기본 설정
st.set_page_config(
    page_title="다이아몬드 가격 예측 AI (Ridge 회귀)",
    page_icon="💎",
    layout="wide"
)
plt.rcParams['axes.unicode_minus'] = False


# 1. 데이터 로드 및 모델 학습 (최초 1회 실행 후 서버 메모리에 캐싱)
@st.cache_resource
def load_and_train():
    df = pd.read_csv('diamonds_b2_preprocessed.csv')
    feature_cols = [c for c in df.columns if c not in ['price', 'log1p_price']]
    X = df[feature_cols]
    y = df['price']

    # 8:2 가격 10분위수 층화 분할
    price_bins = pd.qcut(y, q=10, labels=False)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=price_bins
    )

    # RidgeCV 파이프라인 학습 (log1p 타겟)
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('reg', RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0], cv=5))
    ])
    pipe.fit(X_train, np.log1p(y_train))

    # 테스트 세트 예측 및 달러($) 역변환
    pred_test_log = pipe.predict(X_test)
    pred_test_usd = np.clip(np.expm1(pred_test_log), 326.0, 18823.0)

    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_test, pred_test_usd))),
        'mae': float(mean_absolute_error(y_test, pred_test_usd)),
        'r2': float(r2_score(y_test, pred_test_usd)),
        'alpha': float(pipe.named_steps['reg'].alpha_)
    }

    # 회귀 계수 정리
    scaler = pipe.named_steps['scaler']
    reg = pipe.named_steps['reg']
    raw_coefs = reg.coef_ / scaler.scale_
    coef_df = pd.DataFrame({
        'feature': feature_cols,
        'std_coef': reg.coef_,
        'raw_coef': raw_coefs,
        'pct_impact': (np.exp(raw_coefs) - 1) * 100
    }).sort_values(by='std_coef', key=abs, ascending=False)

    return pipe, feature_cols, metrics, coef_df, X_test, y_test, pred_test_log, pred_test_usd


pipe, feature_cols, metrics, coef_df, X_test, y_test, pred_test_log, pred_test_usd = load_and_train()

# --- 헤더 영역 ---
st.title("💎 다이아몬드 가격 예측 및 회귀 분석 웹앱")
st.markdown("정제된 **53,772건**의 GIA 다이아몬드 데이터와 **B2 전처리(로그 변환 + 원-핫 인코딩 + RidgeCV)**를 기반으로 실시간 시세를 예측합니다.")

# 핵심 모델 성능 지표 요약 카드
col1, col2, col3, col4 = st.columns(4)
col1.metric("테스트 R² (설명력)", f"{metrics['r2']:.4f}")
col2.metric("테스트 MAE (평균 절대 오차)", f"${metrics['mae']:,.2f}")
col3.metric("테스트 RMSE", f"${metrics['rmse']:,.2f}")
col4.metric("최적 규제 강도 (Alpha)", f"{metrics['alpha']}")

st.divider()

# --- 3개 탭 구성 ---
tab1, tab2, tab3 = st.tabs([
    "🔮 실시간 다이아몬드 가격 예측",
    "📊 회귀 계수(영향력) 분석",
    "🩺 잔차(오차) 진단 리포트"
])

# [탭 1] 사용자 입력 기반 실시간 예측
with tab1:
    st.subheader("다이아몬드 4C 스펙을 입력하세요")
    c1, c2, c3 = st.columns(3)

    with c1:
        carat = st.slider("중량 (Carat)", min_value=0.20, max_value=4.00, value=1.00, step=0.01)
        cut = st.selectbox("연마 등급 (Cut)", ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair'], index=0)

    with c2:
        color = st.selectbox("색상 등급 (Color, D가 최고)", ['D', 'E', 'F', 'G', 'H', 'I', 'J'], index=3)
        clarity = st.selectbox(
            "투명도 등급 (Clarity, IF가 최고)",
            ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1'],
            index=3
        )

    with c3:
        depth = st.number_input("깊이 비율 (Depth %)", min_value=43.0, max_value=79.0, value=61.7, step=0.1)
        table = st.number_input("상단 평면 비율 (Table %)", min_value=43.0, max_value=95.0, value=57.0, step=0.1)

    # 입력값을 B2 전처리 피처 벡터(21열)로 변환
    input_dict = {col: 0.0 for col in feature_cols}
    input_dict['carat'] = carat
    input_dict['log_carat'] = np.log(carat)
    input_dict['depth'] = depth
    input_dict['table'] = table

    if f"cut_{cut}" in input_dict:
        input_dict[f"cut_{cut}"] = 1.0
    if f"color_{color}" in input_dict:
        input_dict[f"color_{color}"] = 1.0
    if f"clarity_{clarity}" in input_dict:
        input_dict[f"clarity_{clarity}"] = 1.0

    input_df = pd.DataFrame([input_dict])[feature_cols]
    pred_log = pipe.predict(input_df)[0]
    pred_usd = float(np.clip(np.expm1(pred_log), 326.0, 18823.0))

    st.success(f"### 예상 감정가: **${pred_usd:,.2f} USD**")
    st.caption(f"로그 스케일 예측값: `{pred_log:.4f}` | 역변환(`np.expm1`) 및 데이터 상·하한 클리핑 적용 결과")

# [탭 2] 회귀 계수 분석
with tab2:
    st.subheader("표준화 회귀 계수 및 등급별 가격 영향률")
    st.markdown("- **기준(Baseline) 등급:** `Cut = Fair`, `Color = D(최상위)`, `Clarity = I1(최하위)`")

    fig_coef, ax = plt.subplots(figsize=(10, 6))
    coef_plot = coef_df.sort_values(by='std_coef', ascending=True)
    colors = ['#d95f02' if c < 0 else '#1b9e77' for c in coef_plot['std_coef']]
    ax.barh(coef_plot['feature'], coef_plot['std_coef'], color=colors)
    ax.axvline(0, color='black', lw=1)
    ax.set_title('Standardized Ridge Coefficients (Feature Impact)')
    ax.set_xlabel('Standardized Coefficient (Beta)')
    ax.grid(True, axis='x', alpha=0.3)
    st.pyplot(fig_coef)

    st.dataframe(
        coef_df.style.format({
            'std_coef': '{:.4f}',
            'raw_coef': '{:.4f}',
            'pct_impact': '{:+.2f}%'
        }),
        use_container_width=True
    )

# [탭 3] 잔차 분석
with tab3:
    st.subheader("테스트 세트(10,755건) 잔차(Residual) 진단")
    y_test_log = np.log1p(y_test)
    resid_log = y_test_log - pred_test_log
    resid_usd = y_test - pred_test_usd

    fig_res, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # 1. Actual vs Predicted
    axes[0].scatter(y_test, pred_test_usd, alpha=0.15, s=10, color='#2b5c8f')
    axes[0].plot([0, 20000], [0, 20000], 'r--', lw=1.5)
    axes[0].set_title('Actual vs. Predicted ($)')
    axes[0].set_xlabel('Actual Price ($)')
    axes[0].set_ylabel('Predicted Price ($)')
    axes[0].grid(True, alpha=0.3)

    # 2. Log Residual Histogram
    sns.histplot(resid_log, bins=50, stat='density', color='#2ca02c', alpha=0.5, ax=axes[1])
    x_norm = np.linspace(resid_log.min(), resid_log.max(), 200)
    axes[1].plot(x_norm, stats.norm.pdf(x_norm, resid_log.mean(), resid_log.std()), 'r--')
    axes[1].set_title('Log Residual Normality')
    axes[1].set_xlabel('Log Residual')
    axes[1].grid(True, alpha=0.3)

    # 3. USD Residuals vs Carat
    axes[2].scatter(X_test['carat'], resid_usd, alpha=0.15, s=10, color='#d95f02')
    axes[2].axhline(0, color='black', linestyle='--')
    axes[2].set_ylim(-8000, 8000)
    axes[2].set_title('USD Residuals vs. Carat')
    axes[2].set_xlabel('Carat')
    axes[2].set_ylabel('Residual ($)')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig_res)
