# 💎 다이아몬드 가격 예측 웹앱 (GitHub 학습/평가 분리형)

GitHub 저장소 내 `data/diamonds_train.csv`와 `data/diamonds_test.csv` 파일을 직접 읽어 **학습용 데이터로 모델을 학습하고 평가용 데이터로 성능을 검증**하는 Streamlit 웹 애플리케이션입니다.

## 저장소 구조
```text
├── app.py                       # 학습/평가 분리 데이터 자동 로드·학습·평가·예측 웹앱
├── data/
│   ├── diamonds_train.csv       # 학습용 데이터 (80%, 43,017행)
│   └── diamonds_test.csv        # 평가용 데이터 (20%, 10,755행)
├── requirements.txt             # 필수 파이썬 패키지
└── README.md                    # 프로젝트 안내
```
