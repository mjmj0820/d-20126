import datetime
import pandas as pd
import requests
import streamlit as st

# 페이지 기본 설정 (타이틀 및 넓은 레이아웃)
st.set_page_config(
    page_title="어제 박스오피스 순위", page_icon="🎬", layout="wide"
)

st.title("🎬 어제 일별 박스오피스")

# 1. 한국 시간(KST, UTC+9) 기준으로 '어제' 날짜 계산하기
# 배포 서버가 해외(UTC)에 있어도 한국 시간 기준으로 작동하도록 설정합니다.
kst_timezone = datetime.timezone(datetime.timedelta(hours=9))
today_kst = datetime.datetime.now(kst_timezone)
yesterday_kst = today_kst - datetime.timedelta(days=1)
target_dt = yesterday_kst.strftime("%Y%m%d")
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")

st.caption(f"기준 일자: {display_date} (한국 표준시 기준)")


# 2. KOBIS API 호출 함수 (결과를 1시간(3600초) 동안 캐싱)
@st.cache_data(ttl=3600)
def get_box_office_data(date_str):
    # Streamlit Secrets에 KOBIS_KEY가 등록되어 있는지 확인
    if "KOBIS_KEY" not in st.secrets:
        return None, "SECRETS_MISSING"

    api_key = st.secrets["KOBIS_KEY"]
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": date_str}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


# API 데이터 가져오기 실행
data, error = get_box_office_data(target_dt)

# 3. 예외 상황 및 오류별 안내 처리
if error == "SECRETS_MISSING":
    st.error(
        "⚠️ [설정 필요] Streamlit Secrets에 'KOBIS_KEY'가 등록되지 않았습니다."
    )
    st.info(
        "💡 **확인할 사항:** Streamlit Cloud 앱 설정의 `Secrets` 항목에 `KOBIS_KEY = \"발급받은키\"` 형태로 등록했는지 확인해 주세요."
    )

elif error:
    st.error("⚠️ [요청 실패] KOBIS API 서버 연결에 실패했습니다.")
    st.info(
        f"💡 **확인할 사항:** 인터넷 연결 상태 또는 KOBIS 서버 상태를 확인해 주세요. (오류 내용: {error})"
    )

elif "faultInfo" in data:
    st.error("⚠️ [API 인증 오류] KOBIS API에서 오류 응답이 도착했습니다.")
    st.warning(f"메시지: {data['faultInfo'].get('message', '알 수 없는 오류')}")
    st.info(
        "💡 **확인할 사항:** Secrets에 등록한 `KOBIS_KEY` 값이 정확한지, API 키 사용 기한이 만료되지 않았는지 확인해 주세요."
    )

else:
    box_office_result = data.get("boxOfficeResult", {})
    daily_list = box_office_result.get("dailyBoxOfficeList", [])

    if not daily_list:
        st.warning("⚠️ 어제 날짜의 영화 목록 데이터가 비어 있습니다.")
        st.info(
            "💡 **확인할 사항:** 영화진흥위원회의 일별 집계 갱신 시간 이전이거나 데이터가 없는 날짜일 수 있습니다. 잠시 후 다시 시도해 주세요."
        )

    else:
        # 4. 데이터프레임 생성 및 문자열 숫자를 정수(int)로 변환
        df = pd.DataFrame(daily_list)

        num_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
        for col in num_columns:
            df[col] = (
                pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            )

        # 5. 1위 영화 지표 카드 3개 크게 보여주기
        top_movie = df.iloc[0]
        st.subheader(f"🥇 1위: {top_movie['movieNm']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("어제 관객수", f"{top_movie['audiCnt']:,} 명")
        with col2:
            st.metric("누적 관객수", f"{top_movie['audiAcc']:,} 명")
        with col3:
            st.metric("스크린수", f"{top_movie['scrnCnt']:,} 개")

        st.divider()

        # 6. 관객수 상위 5편 막대그래프
        st.subheader("📊 상위 5개 영화 관객수 비교")
        top5_df = df.head(5).set_index("movieNm")[["audiCnt"]]
        top5_df.columns = ["어제 관객수"]
        st.bar_chart(top5_df)

        st.divider()

        # 7. 전체 박스오피스 순위 표 작성 및 출력
        st.subheader("📋 전체 박스오피스 순위")

        # 출력용 데이터프레임 정리
        display_df = df[
            ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
        ].copy()
        display_df.columns = [
            "순위",
            "영화명",
            "개봉일",
            "관객수",
            "누적관객",
            "스크린수",
        ]

        # 숫자에 쉼표(천 단위) 및 단위 붙여 보기 좋게 가공
        display_df["관객수"] = display_df["관객수"].map("{:,}명".format)
        display_df["누적관객"] = display_df["누적관객"].map("{:,}명".format)
        display_df["스크린수"] = display_df["스크린수"].map("{:,}개".format)

        st.dataframe(display_df, use_container_width=True, hide_index=True)
