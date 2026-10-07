from typing import Any
import numpy as np
import pandas as pd
from fastapi import HTTPException
#군집 알고리즘
# DBSCAN : 밀도 기반 군집. 밀집 영역을 묶고, 외딴점은 노이즈(-1) 분류
# AgglomerativeClustering : 계층적 군집 : 가까운 데이터 끼리 묶음
# KMeans : k-평균 군집 : 지정된 k개의 중심점을 기준으로 가까운 데이터 끼리 묶음
from sklearn.cluster import DBSCAN,AgglomerativeClustering, KMeans  #uv add scikit-learn
# 주성분 분석(PCA) : 차원을 축소. 
from sklearn.decomposition import PCA 
# 앙상블 모델 : 여러 결정트리 모델들을 결합하여 성능을 높인 모델
from sklearn.ensemble import (
    GradientBoostingClassifier,  #그래디언트 부스팅 분류
    GradientBoostingRegressor,   #그래디언트 부스팅 회귀
    RandomForestClassifier,      #랜덤 포레스트 분류
    RandomForestRegressor,       #랜덤 포레스트 회귀
)
#결측값을 중앙값, 최빈값등으로 채우기 위한 전처리기
from sklearn.impute import SimpleImputer 
# 성형모델
# LinearRegression : 선형 회귀 분석
# LogisticRegression : 로지스틱회귀분석. 분류모델로 많이 사용됨
# Ridge : 릿지회귀. 가중치가 커지지 않도록 규제 더한 선형 회귀 분석(과적합 완화)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
# 모델 평가 지표
from sklearn.metrics import (
    accuracy_score,            #분류 : 정확도 
    confusion_matrix,          #분류 : 혼동행렬
    f1_score,                  #분류 : 조화평균. 정밀도와 재현율의 조화평균
    mean_absolute_error,       #회귀 : MAE. 오차 절대값의 평균
    mean_squared_error,        #회귀 : MSE. 오차 제곱의 평균 (제곱근을 하면 RMSE)
    precision_score,           #분류 : 정밀도. 예측한 값 중 정답의 비율
    r2_score,                  #회귀 : 결정계수. 모델이 데이터의 변동을 설명하는 수치. -1 ~ 1 사이의 값. 1이 성능이 좋음
    recall_score,              #분류 : 재현율. 실제 값 중 정답의 비율
    silhouette_score,          #군집 : 실루엣 계수. 군집이 얼마나 잘 분리되었는지 평가 (-1 ~ 1 사이의 값. 1에 가까울 수록 성능이 좋음)
)
#학습용, 테스트용 데이터로 분리
from sklearn.model_selection import train_test_split
# 최근접 이웃. 가장 가까운 K개의데이터를 다수결로 분류 예측. 
from sklearn.neighbors import KNeighborsClassifier
#전처리부터 모델까지를 순서대로 연결해서 학습, 예측까지 할 수 있는 파이프라인
from sklearn.pipeline import Pipeline
#전처리
# OneHotEncoder : 원핫인코딩. 범주형을 여러개의 0(F)/1(T)의 값으로 
# StandardScaler : 표준화. 각 수치형 변수를 평균 0, 표준편차 1로 맞춤
from sklearn.preprocessing import OneHotEncoder, StandardScaler
#결정트리 모델
# DecisionTreeClassifier : 결정나무 분류
# DecisionTreeRegressor : 결정나무 회귀
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.compose import ColumnTransformer

ALGORITHMS: dict[str, dict[str, str]] = {
    "regression": {
        "linear": "선형 회귀",
        "ridge": "릿지 회귀",
        "decision_tree": "의사결정나무",
        "random_forest": "랜덤 포레스트",
        "gradient_boosting": "그래디언트 부스팅",
    },
    "classification": {
        "logistic": "로지스틱 회귀",
        "decision_tree": "의사결정나무",
        "random_forest": "랜덤 포레스트",
        "gradient_boosting": "그래디언트 부스팅",
        "knn": "K-최근접 이웃",
    },
    "clustering": {
        "kmeans": "K-평균",
        "agglomerative": "계층적 군집",
        "dbscan": "DBSCAN",
    },
}

RANDOM_STATE = 50
MAX_POINTS = 600
MAX_CLASSES = 30

# 화면에서 받은 독립변수의 값이 실제 dataframe에 존재하는지 판단하고, 원래 값으로 전달함
def _resolve_columns (dataframe : pd.DataFrame, names : list[str]) -> list[Any] :
    # names : 독립변수 목록
    #dataframe에서 컬럼값들만 모아서 저장
    lookup = {str(name) : name for name in dataframe.columns}
    missing = [name for name in names if name not in lookup]  #입력된 독립변수 중  dataframe에 없는 이름 저장
    if missing :  #데이터프레임에 없는 컬럼 목록 존재
        raise HTTPException(status_code=400, detail=f"열을 찾을 수 없습니다 {', '.join(missing)}")
    return [lookup[name] for name in names]


# 데이터 전처리 
def _build_preprocessor(features : pd.DataFrame) -> ColumnTransformer :
    #숫자형 컬럼들
    numeric = [name for name in features.columns if pd.api.types.is_numeric_dtype(features[name])]
    #범주형 컬럼들
    categorical = [name for name in features.columns if name not in numeric]
    transformers = []
    #전처리
    #수치형 : 결측값을 중간값으로
    #범주형 : 결측값을 최빈값으로 저장.
    if numeric:
        transformers.append(
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric)
        )
    if categorical:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        # sparse_output=False: 이후 PCA·실루엣 계산이 밀집 배열을 기대하므로 일반 배열로 출력.
                        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical,
            )
        )
    #ColumnTransformer : 수치형,범주형 전처리 후 결과값을 열로 붙여서 하나의 행렬로 리턴
    # cat_ 접두어 생략 
    return ColumnTransformer(transformers, verbose_feature_names_out=False)

#선택한 알고리즘에 맞는 모델을 생성
def _build_estimator(task: str, algorithm: str, n_clusters: int) -> Any:
    if task == "regression":
        return {
            "linear": lambda: LinearRegression(),
            "ridge": lambda: Ridge(),
            "decision_tree": lambda: DecisionTreeRegressor(random_state=RANDOM_STATE),
            "random_forest": lambda: RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
            "gradient_boosting": lambda: GradientBoostingRegressor(random_state=RANDOM_STATE),
        }[algorithm]()
    if task == "classification":
        return {
            "logistic": lambda: LogisticRegression(max_iter=1000),
            "decision_tree": lambda: DecisionTreeClassifier(random_state=RANDOM_STATE),
            "random_forest": lambda: RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE),
            "gradient_boosting": lambda: GradientBoostingClassifier(random_state=RANDOM_STATE),
            "knn": lambda: KNeighborsClassifier(),
        }[algorithm]()
    return {
        "kmeans": lambda: KMeans(n_clusters=n_clusters, n_init=10, random_state=RANDOM_STATE),
        "agglomerative": lambda: AgglomerativeClustering(n_clusters=n_clusters),
        "dbscan": lambda: DBSCAN(),
    }[algorithm]()

# length 값 까지 균등 분할한 데이터 리턴
def _sample_indices(length: int) -> np.ndarray:
    if length > MAX_POINTS:
        #np.linspace : 균등값 리턴 
        # 0 9사이의값을 10등분 : 0 1 2 3 4 5 6 7 8 9
        return np.linspace(0, length - 1, num=MAX_POINTS, dtype=int)
    return np.arange(length)
# 변수 영향도 
# 학습된 모델에서 최대 20개의 변수만 추출
def _feature_importance(pipeline: Pipeline) -> list[dict[str, Any]]:
    model = pipeline.named_steps["model"] #학습된 모델 
    #모델의 열이름
    names = [str(name) for name in pipeline.named_steps["prep"].get_feature_names_out()]
    # importance : 트리계열의 변수 영향도
    # coefficient : 선형,릿지등에서의 변수 영향도
    # mean_abs_coefficient : 로지스틱회귀의 계수 절댓값 평균으로 변수 영향도
    if hasattr(model, "feature_importances_"):  #트리계열의 변수 영향도
        values = np.asarray(model.feature_importances_, dtype=float)
        kind = "importance"
    elif hasattr(model, "coef_"):  # 선형, 릿지 회귀의 변수 영향도
        coef = np.asarray(model.coef_, dtype=float)
        values = coef if coef.ndim == 1 else np.abs(coef).mean(axis=0)
        kind = "coefficient" if coef.ndim == 1 else "mean_abs_coefficient"
    else:
        return [] #빈목록 반환
    # np.abs(values) : 변수의 영향도를 절대값
    # -np.abs(values) : 변수 영향도가 음수
    # np.argsort : 오름차순으로 정렬 
    order = np.argsort(-np.abs(values))[:20]  #음수 양수 상관 없이 절대값 순으로 정렬
    return [{"feature": names[index], "value": float(values[index]), "kind": kind} for index in order]

# 회귀모델 학습. 테스트데이터를 활용하여 평가
def _regression(pipeline: Pipeline, features: pd.DataFrame, target: pd.Series, test_size: float) -> dict[str, Any]:
    '''
     반환값
     - metrics : r2,  mae, rmse, 
     - predictions : 테스트데이터의 실제값/예측값. 산점도 그래프용
     - feature_importance : 변수 영향도
    '''
    #종속변수를 숫자형으로 변환
    #errors="coerce" : "N/A", "-" 등의 숫자변경이 불가능한 데이터를 NaN으로 변경
    target = pd.to_numeric(target, errors="coerce")
    valid = target.notna() & np.isfinite(target)  #숫자형 데이터만 추출
    features, target = features[valid], target[valid].astype(float) #종속변수가 숫자인 데이터의 독립변수, 종속변수

    if len(target) < 10:
        raise HTTPException(status_code=400, detail="회귀 분석에는 종속 변수 값이 있는 행이 10개 이상 필요합니다.")

    #학습데이터와 테스트데이터 분리
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=test_size, random_state=RANDOM_STATE)
    pipeline.fit(x_train, y_train) #전처리 + 모델객체 로 학습하기
    predicted = pipeline.predict(x_test)  #테스트 데이터 예측하기
    actual = y_test.to_numpy()  #정답
    indices = _sample_indices(len(actual))
    return {
        "train_count": int(len(x_train)),  #학습데이터 갯수
        "test_count": int(len(x_test)),    #테스트데이터 갯수
        "metrics": {
            "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else None,
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),  #np.sqrt:  root(mse) => RMSE
            "train_r2": float(r2_score(y_train, pipeline.predict(x_train))),  #과적합상태 : train_r2 > r2 
        },
        "predictions": [{"actual": float(actual[index]), "predicted": float(predicted[index])} for index in indices],
        "feature_importance": _feature_importance(pipeline),
    }

# 분류 모델 학습, 테스트 데이터로 평가
def _classification(pipeline: Pipeline, features: pd.DataFrame, target: pd.Series, test_size: float) -> dict[str, Any]:
    '''
    반환값
     - classes : 혼동행렬의 행,열 순서가 같다
     - matrice : accuracy, precision/recall/f1, train_accuracy
     - confusion_matrix : 혼동 행렬
    '''
    valid = target.notna()  #종속변수 중 결측값이 아닌 데이터
    features, target = features[valid], target[valid].astype(str) #독립변수, 종속변수 종속변수의 자료형은 문자열로
    classes = sorted(target.unique().tolist())  #분류 대상의 값
    if len(classes) < 2:
        raise HTTPException(status_code=400, detail="분류 분석에는 종속 변수에 2개 이상의 범주가 필요합니다.")
    if len(classes) > MAX_CLASSES: #30개이상의 범주
        raise HTTPException(
            status_code=400,
            detail=f"종속 변수의 범주가 {len(classes)}개로 너무 많습니다({MAX_CLASSES}개 이하). 연속형 값이라면 회귀 분석을 사용해 주세요.",
        )
    if len(target) < 10:
        raise HTTPException(status_code=400, detail="분류 분석에는 종속 변수 값이 있는 행이 10개 이상 필요합니다.")
    try:
        #훈련,테스트 데이터 분리
        #stratify=target : 학습/테스트 데이터의 범주 비율이 같도록 분리
        x_train, x_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=RANDOM_STATE, stratify=target
        )
    except ValueError:  #데이터 분리시 오류발생. : 무작위 분리
        x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=test_size, random_state=RANDOM_STATE)
    #학습데이터의 정답의 범주는 2개이상이어야 함
    if y_train.nunique() < 2:
        raise HTTPException(status_code=400, detail="학습 데이터에 범주가 하나뿐입니다. 데이터를 늘리거나 테스트 비율을 조정해 주세요.")
    
    model = pipeline.named_steps["model"]  #학습 모델 
    # isinstance(객체,클래스) : 객체가 클래스의 객체?
    if isinstance(model, KNeighborsClassifier):  #학습모델이 KNN인 경우
        model.set_params(n_neighbors=min(5, len(x_train)))  #x_train의 갯수가 5보다 작은경우 근접이웃의 갯수 학습데이터의 행의수, 그외는 5개로
    pipeline.fit(x_train, y_train) #학습하기
    predicted = pipeline.predict(x_test)  #예측하기
    return {
        "train_count": int(len(x_train)),  #학습데이터 건수
        "test_count": int(len(x_test)),    #테스트 데이터 건수
        "classes": classes,                #범주값. 분류의 값
        "metrics": {
            "accuracy": float(accuracy_score(y_test, predicted)),
            "precision": float(precision_score(y_test, predicted, average="macro", zero_division=0)),
            "recall": float(recall_score(y_test, predicted, average="macro", zero_division=0)),
            "f1": float(f1_score(y_test, predicted, average="macro", zero_division=0)),
            "train_accuracy": float(accuracy_score(y_train, pipeline.predict(x_train))),
        },
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=classes).tolist(),  #혼동행렬
        "feature_importance": _feature_importance(pipeline),
    }

# 군집 분석 실행. 그래프 출력
# pipeline : 데이터전처리 + 모델선택
# features : 독립변수데이터
# n_clusters : 생성할 클러스터 갯수
def _clustering(pipeline: Pipeline, features: pd.DataFrame, n_clusters: int) -> dict[str, Any]:
    '''
    반환값
    1. 클러스터 갯수 : cluster_count
    2. 노이즈 수 : noise_count
    3. 군집별 크기와 수치형 데이터 평균값 : profiles
    4. 산점도 좌표. 군집값 : projection
    5. 실루엣 계수 
    '''
    #데이터의 크기가 클러스터 갯수보다 커야함
    if len(features) < max(3, n_clusters + 1):
        raise HTTPException(status_code=400, detail="군집 분석을 하기에는 데이터 행이 부족합니다.")
    # 데이터 전처리 + 모델 학습 결과를 리턴
    labels = pipeline.fit_predict(features)
    # PCA알고리즘은 표준화 후에 다시 계산해야 함.
    transformed = pipeline.named_steps["prep"].transform(features)
    cluster_ids = sorted(set(labels.tolist()))  #그룹값을 정렬한 정보
    real_clusters = [label for label in cluster_ids if label != -1]  #DBScan 알고리즘인 경우 노이즈값을 제거
    # -1 인 경우는 군집에 속하지 않는 데이터는 제거 
    clustered = labels != -1
    silhouette = None
    # 실루엣 계수는 군집이 2개 이상이고, 군집수 < 표본수 일때만 정의 가능함.
    # 실루엣 계수 : 같은 군집의 평균거리, 
    if 2 <= len(real_clusters) < clustered.sum():
        silhouette = float(silhouette_score(transformed[clustered], labels[clustered]))

    #그래프 작성을 위한 PCA알고리즘 적용. 차원축소방식을 이용하여 그래프 데이터 생성
    if transformed.shape[1] >= 2:
        projection = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(transformed)
    else:
        projection = np.column_stack([transformed[:, 0], np.zeros(len(transformed))])
        # 차트용 점 인덱스를 균등간격으로 추출
    indices = _sample_indices(len(labels))

    numeric = features.select_dtypes(include="number") #데이터의 종류가 숫자형인
    profiles = []
    for label in cluster_ids:
        mask = labels == label
        profiles.append(
            {
                "cluster": int(label),
                "size": int(mask.sum()),
                "means": {str(name): (None if pd.isna(value) else float(value)) for name, value in numeric[mask].mean().items()},
            }
        )
    return {
        "row_count": int(len(features)),
        "cluster_count": len(real_clusters),
        "noise_count": int((labels == -1).sum()),
        "metrics": {"silhouette": silhouette},
        "profiles": profiles,
        "projection": [
            {"x": float(projection[index, 0]), "y": float(projection[index, 1]), "cluster": int(labels[index])}
            for index in indices
        ],
    }


'''
  1. 입력검증
  2. 전처리 
  3. 모델 생성
  4. 학습,평가
  5. 결과값 : JSON데이터 리턴 
'''
def run_model(
    dataframe: pd.DataFrame,  # 업로드 파일
    task: str,                # 회귀(regression),분류(classification),군집(clustering) 선택
    algorithm: str,           # 알고리즘의 종류. ALGORITHMS[task]로 조회한 딕셔너리의 키값
    features: list[str],      # 독립변수값들. features 쿼리값이 여러개를 list로 저장
    target: str | None,       # 종속변수. 회귀,분류은 필수, 군집 사용안함
    test_size: float,         # 테스트 데이터의 비율. (0.1 ~ 0.5). 군집에서는 필요 없음
    n_clusters: int,          # 군집 수(2 ~ 20). 회귀,분류 사용안함
) -> dict[str, Any]:
    #=====  1. 입력값 검증 ==========
    if task not in ALGORITHMS:
        raise HTTPException(status_code=400, detail="분석 유형은 regression, classification, clustering 중 하나여야 합니다.")
    
    if algorithm not in ALGORITHMS[task]:
        raise HTTPException(status_code=400, detail="선택한 분석 유형에서 지원하지 않는 알고리즘입니다.")

   #list 값을 dict 데이터로 변경함. {"weight":None, "origin" : None}
    features = list(dict.fromkeys(features))
    if not features:  #선택된 독립변수가 없음
        raise HTTPException(status_code=400, detail="독립 변수를 1개 이상 선택해 주세요.")
    
    # 군집 선택한 경우 종속변수가 존재
    if task == "clustering" and target:
        raise HTTPException(status_code=400, detail="군집 분석에서는 종속 변수를 지정할 수 없습니다.")
    # 회귀,분류인 경우 종속변수가 필수
    if task != "clustering":
        if not target:
            raise HTTPException(status_code=400, detail="회귀·분류 분석에는 종속 변수를 선택해야 합니다.")
        # 독립변수에 종속변수가 포함되는 경우
        if target in features:
            raise HTTPException(status_code=400, detail="종속 변수는 독립 변수에 포함될 수 없습니다.")
        
    if not 0.1 <= test_size <= 0.5:  # test_size의 값의 범위는 0.1 ~ 0.5 사이만 가능
        raise HTTPException(status_code=400, detail="테스트 비율은 0.1 이상 0.5 이하여야 합니다.")
    #군집의 클러스터 갯수는 2 ~ 20사이만 가능
    if not 2 <= n_clusters <= 20:
        raise HTTPException(status_code=400, detail="군집 개수는 2 이상 20 이하여야 합니다.")

#============ 2. 데이터 전처리 하기 : 독립변수 검증 =============================
    # dataframe중 독립변수 컬럼만 feature_frame객체에 저장
    # features의 데이터가 dataframe에 없는 경우 예외 발생함
    feature_frame = dataframe[_resolve_columns(dataframe, features)].copy()
    feature_frame.columns = features

    for name in feature_frame.columns:
        series = feature_frame[name]  #시리즈 데이터
        if not pd.api.types.is_numeric_dtype(series):  #범주형
            feature_frame[name] = series.astype(str).where(series.notna(), np.nan).astype(object)

    #값이 없는 컬럼
    empty = [name for name in feature_frame.columns if feature_frame[name].notna().sum() == 0]
    if empty:
        raise HTTPException(status_code=400, detail=f"값이 모두 비어 있는 독립 변수입니다: {', '.join(empty)}")
    #============  3. 데이터 전처리 + 모델 선택 
    pipeline = Pipeline(
        #prep : 전처리된 Dataframe 데이터
        #model : 모델 선택 
        [("prep", _build_preprocessor(feature_frame)), ("model", _build_estimator(task, algorithm, n_clusters))]
    )
    result: dict[str, Any] = {
        "task": task,
        "algorithm": algorithm,
        "algorithm_label": ALGORITHMS[task][algorithm],
        "features": features,
        "target": target if task != "clustering" else None,  #군집인 경우는 종속변수는 None
    }

    if task == "clustering":
        result.update(_clustering(pipeline, feature_frame, n_clusters))
    else:
        target_series = dataframe[_resolve_columns(dataframe, [target])[0]] #종속변수 값들
        if task == "regression":
            if not pd.api.types.is_numeric_dtype(target_series):
                raise HTTPException(status_code=400, detail="회귀 분석의 종속 변수는 수치형 열이어야 합니다.")
            result.update(_regression(pipeline, feature_frame, target_series, test_size))
        else:
            result.update(_classification(pipeline, feature_frame, target_series, test_size))
    return result