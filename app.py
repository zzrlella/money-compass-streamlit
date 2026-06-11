
import os
import json
import math
import streamlit as st

try:
    import google.generativeai as genai
except Exception:
    genai = None


st.set_page_config(
    page_title="머니나침반 | AI 맞춤형 재테크 코치",
    page_icon="🧭",
    layout="wide"
)

st.markdown("""
<style>
.main-title {
    font-size: 2.35rem;
    font-weight: 900;
    margin-bottom: 0.2rem;
}
.sub-title {
    color: #555;
    font-size: 1.03rem;
    margin-bottom: 1.2rem;
}
.hero {
    background: linear-gradient(135deg, #EEF2FF, #F8FAFC);
    border: 1px solid #E0E7FF;
    border-radius: 1.1rem;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.notice-box {
    background-color: #F7F7F9;
    border-left: 5px solid #4F46E5;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
.warning-box {
    background-color: #FFF7ED;
    border-left: 5px solid #F97316;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
.card {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 0.9rem;
    padding: 1rem 1.1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 5px rgba(0,0,0,0.04);
}
.card-title {
    font-weight: 800;
    font-size: 1.05rem;
    margin-bottom: 0.45rem;
}
.big-badge {
    display: inline-block;
    background-color: #EEF2FF;
    color: #3730A3;
    font-weight: 800;
    padding: 0.45rem 0.7rem;
    border-radius: 999px;
    margin: 0.2rem 0.2rem 0.2rem 0;
}
.small-muted {
    color: #666;
    font-size: 0.9rem;
}
.footer {
    font-size: 0.82rem;
    color: #666;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


def won(n: float) -> str:
    try:
        n = int(round(n))
    except Exception:
        return "0원"
    if n >= 10000:
        man = n // 10000
        rest = n % 10000
        if rest == 0:
            return f"{man:,}만 원"
        return f"{man:,}만 {rest:,}원"
    return f"{n:,}원"


def pct(x: float) -> str:
    if math.isnan(x) or math.isinf(x):
        return "0%"
    return f"{x:.1f}%"


def get_gemini_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


def call_gemini(user_profile: dict, rule_summary: dict, mode: str) -> str:
    api_key = get_gemini_api_key()
    if not api_key or genai is None:
        return ""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        if mode == "coach":
            task = """
사용자에게 'AI 재테크 코치'처럼 말해줘.
결과는 다음 형식으로 작성해:
1. 한 줄 진단
2. 지금 가장 먼저 할 일
3. 이번 달 행동 계획 3개
4. 하지 말아야 할 실수 2개
5. 격려 문장 1개
"""
        elif mode == "habit":
            task = """
사용자의 소비습관을 분석하는 코치처럼 말해줘.
결과는 다음 형식으로 작성해:
1. 소비 패턴 추정
2. 줄이면 효과가 큰 지출
3. 현실적인 절약 방법 3개
4. 너무 무리하지 않는 기준
"""
        elif mode == "goal":
            task = """
사용자의 목표 달성을 위한 계획을 짜줘.
결과는 다음 형식으로 작성해:
1. 목표 달성 가능성
2. 필요한 월 저축액에 대한 조언
3. 목표 기간별 전략
4. 실패 가능성을 줄이는 방법
"""
        else:
            task = "사용자의 재무상황에 맞는 쉬운 조언을 작성해줘."

        prompt = f"""
너는 금융상품을 직접 판매하거나 특정 종목을 추천하지 않는 재무관리 보조 AI야.

중요 제한:
- 특정 은행명, 주식명, ETF명, 펀드명 추천 금지
- 수익률 보장 금지
- '무조건', '반드시' 같은 단정적 투자 권유 금지
- 금융상품 가입 권유가 아니라 재무관리 방향 안내로 작성
- 대학생/사회초년생도 이해할 수 있게 쉬운 한국어 사용
- 너무 길지 않게 작성

{task}

사용자 입력:
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

규칙 기반 분석:
{json.dumps(rule_summary, ensure_ascii=False, indent=2)}
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return ""


def classify_finance(
    income, fixed_expense, variable_expense, savings, investment, debt,
    goal, period, risk_type, experience, target_amount
):
    total_expense = fixed_expense + variable_expense
    surplus = income - total_expense
    expense_ratio = (total_expense / income * 100) if income > 0 else 0
    saving_capacity_ratio = (surplus / income * 100) if income > 0 else 0
    total_assets = savings + investment
    emergency_target = total_expense * 3

    # persona
    if surplus < 0:
        persona = "🚨 새는 돈 차단형"
        persona_desc = "현재는 재테크보다 적자 흐름을 막는 것이 가장 중요합니다."
    elif debt > 0:
        persona = "💳 부채 정리 우선형"
        persona_desc = "투자보다 부채 상환과 비상금 확보 순서를 먼저 잡는 편이 안전합니다."
    elif savings < total_expense:
        persona = "🛟 비상금 구축형"
        persona_desc = "예상치 못한 지출에 대비할 현금성 자산을 먼저 만드는 단계입니다."
    elif risk_type == "안정형":
        persona = "🌱 차근차근 저축형"
        persona_desc = "원금 손실 가능성을 낮추고 목표자금을 안정적으로 모으는 방식이 어울립니다."
    elif risk_type == "중립형":
        persona = "⚖️ 균형 성장형"
        persona_desc = "저축으로 안정성을 확보하면서 일부 여유자금은 장기 분산투자에 활용할 수 있습니다."
    else:
        persona = "🚀 장기 성장 추구형"
        persona_desc = "손실 가능성을 이해한 상태에서 장기적 자산 성장을 노려볼 수 있습니다."

    if income <= 0:
        finance_status = "소득 정보가 부족해 정확한 분석이 어렵습니다."
        status_level = "정보 부족"
    elif surplus < 0:
        finance_status = "월 지출이 소득보다 큰 적자 상태입니다. 투자보다 지출 구조 조정이 가장 우선입니다."
        status_level = "위험"
    elif expense_ratio >= 85:
        finance_status = "소득 대비 지출 비중이 매우 높습니다. 저축 여력을 먼저 확보해야 합니다."
        status_level = "주의"
    elif expense_ratio >= 65:
        finance_status = "지출 비중이 다소 높은 편입니다. 고정지출과 변동지출을 점검하면 저축 여력이 커질 수 있습니다."
        status_level = "보통"
    else:
        finance_status = "소득 대비 지출이 비교적 안정적입니다. 목표에 맞춰 저축과 투자를 병행할 수 있습니다."
        status_level = "양호"

    if total_expense <= 0:
        emergency_msg = "월 지출 정보가 부족해 비상금 목표를 계산하기 어렵습니다."
        emergency_level = "정보 부족"
    elif savings < total_expense:
        emergency_msg = f"현재 저축액이 1개월 생활비보다 적습니다. 우선 최소 {won(total_expense)} 이상을 비상금으로 확보하는 것이 좋습니다."
        emergency_level = "부족"
    elif savings < emergency_target:
        emergency_msg = f"비상금은 어느 정도 있지만 충분하지는 않습니다. 3개월 생활비 기준 목표액은 약 {won(emergency_target)}입니다."
        emergency_level = "보완 필요"
    else:
        emergency_msg = f"3개월 생활비 수준의 비상금이 확보되어 있습니다. 목표에 따라 장기 저축이나 분산투자를 검토할 수 있습니다."
        emergency_level = "양호"

    if debt > 0:
        debt_msg = f"부채가 {won(debt)} 있습니다. 고위험 투자보다 상환 계획과 이자 부담 점검을 우선하는 것이 안전합니다."
    else:
        debt_msg = "입력된 부채가 없습니다. 비상금과 목표자금 계획을 세운 뒤 투자 가능 금액을 검토할 수 있습니다."

    if surplus <= 0:
        invest_msg = "현재는 투자보다 지출 조정과 현금흐름 개선이 우선입니다."
    elif debt > 0:
        invest_msg = "부채가 있으므로 투자 비중을 크게 늘리기보다 상환 계획을 먼저 세우는 편이 좋습니다."
    elif savings < total_expense:
        invest_msg = "비상금이 부족하므로 투자보다 현금성 저축을 먼저 확보하는 것이 좋습니다."
    else:
        if risk_type == "안정형":
            invest_msg = "안정형 성향이므로 예금·적금 등 원금 손실 위험이 낮은 방식 중심으로 시작하는 것이 적합합니다."
        elif risk_type == "중립형":
            invest_msg = "중립형 성향이므로 비상금을 유지하면서 일부 여유자금을 장기 분산투자에 배분할 수 있습니다."
        else:
            invest_msg = "공격형 성향이어도 생활비와 비상금을 먼저 분리하고, 감당 가능한 범위 안에서 장기 분산투자를 고려하는 것이 좋습니다."

    if surplus <= 0:
        product_types = ["가계부/소비관리", "비상금 통장", "부채 상환 계획"]
    elif debt > 0:
        product_types = ["부채 상환 계획", "비상금 통장", "단기 적금"]
    elif savings < emergency_target:
        product_types = ["입출금 통장", "단기 적금", "예금"]
    else:
        if risk_type == "안정형":
            product_types = ["예금", "적금", "청약 등 목적형 저축"]
        elif risk_type == "중립형":
            product_types = ["예금·적금", "분산투자형 상품", "장기 투자 상품"]
        else:
            product_types = ["분산투자형 상품", "장기 투자 상품", "목표자금용 저축"]

    available = max(surplus, 0)
    if available == 0:
        allocation = {
            "소비 조정 목표": max(total_expense - income, 0) + max(income * 0.1, 50000),
            "비상금 저축": 0,
            "목표자금 저축": 0,
            "투자 가능 금액": 0,
        }
    else:
        if debt > 0:
            allocation = {
                "비상금 저축": available * 0.25,
                "부채 상환": available * 0.55,
                "목표자금 저축": available * 0.20,
                "투자 가능 금액": 0,
            }
        elif savings < emergency_target:
            allocation = {
                "비상금 저축": available * 0.60,
                "목표자금 저축": available * 0.30,
                "투자 가능 금액": available * 0.10 if risk_type != "안정형" else 0,
            }
        else:
            if risk_type == "안정형":
                allocation = {
                    "비상금 유지": available * 0.20,
                    "목표자금 저축": available * 0.65,
                    "투자 가능 금액": available * 0.15,
                }
            elif risk_type == "중립형":
                allocation = {
                    "비상금 유지": available * 0.15,
                    "목표자금 저축": available * 0.45,
                    "투자 가능 금액": available * 0.40,
                }
            else:
                allocation = {
                    "비상금 유지": available * 0.10,
                    "목표자금 저축": available * 0.35,
                    "투자 가능 금액": available * 0.55,
                }

    # goal progress
    if target_amount > 0 and surplus > 0:
        months_needed = math.ceil(max(target_amount - savings, 0) / surplus) if target_amount > savings else 0
        goal_msg = f"현재 월 여유자금 {won(surplus)}을 모두 목표에 사용하면 약 {months_needed}개월이 필요합니다."
    elif target_amount > 0:
        goal_msg = "현재 월 여유자금이 부족해 목표 달성 기간을 계산하기 어렵습니다. 먼저 지출 조정이 필요합니다."
    else:
        goal_msg = "목표 금액을 입력하면 예상 달성 기간을 계산할 수 있습니다."

    # stress score
    risk_score = 0
    if surplus < 0: risk_score += 35
    if expense_ratio >= 85: risk_score += 25
    elif expense_ratio >= 65: risk_score += 12
    if savings < total_expense: risk_score += 20
    elif savings < emergency_target: risk_score += 10
    if debt > 0: risk_score += 20
    risk_score = min(risk_score, 100)

    if risk_score >= 70:
        stress_label = "높음"
    elif risk_score >= 40:
        stress_label = "보통"
    else:
        stress_label = "낮음"

    priorities = []
    if income <= 0:
        priorities.append("월 소득과 지출 정보를 먼저 정리하기")
    if surplus < 0:
        priorities.append("적자 원인 파악 및 지출 줄이기")
    if debt > 0:
        priorities.append("부채 상환 계획 세우기")
    if savings < emergency_target:
        priorities.append("비상금 확보하기")
    priorities.append(f"'{goal}' 목표에 맞는 기간별 저축 계획 세우기")
    if surplus > 0 and savings >= total_expense and debt == 0:
        priorities.append("투자 성향에 맞는 분산투자 검토하기")
    else:
        priorities.append("투자는 현금흐름 안정 후 소액부터 검토하기")

    # weekly missions
    missions = []
    if surplus < 0:
        missions = ["최근 1개월 카드/계좌 지출을 고정지출과 변동지출로 나누기", "이번 주 줄일 수 있는 변동지출 1개 정하기", "자동결제 중 사용하지 않는 서비스 해지하기"]
    elif debt > 0:
        missions = ["부채별 이자율과 상환일 정리하기", "월 여유자금 중 상환 가능 금액 정하기", "새로운 할부/대출을 늘리지 않기"]
    elif savings < emergency_target:
        missions = ["비상금 전용 통장 또는 계좌를 따로 구분하기", "이번 달 여유자금의 절반 이상을 비상금으로 옮기기", "비상금 목표액을 휴대폰 메모장에 적어두기"]
    else:
        missions = ["목표별 계좌를 분리해보기", "투자 가능 금액의 상한선을 정하기", "월 1회 자산 점검일 만들기"]

    return {
        "월 소득": income,
        "월 총지출": total_expense,
        "월 여유자금": surplus,
        "지출 비율": expense_ratio,
        "저축 가능 비율": saving_capacity_ratio,
        "총 보유자산": total_assets,
        "비상금 목표액": emergency_target,
        "재무상태": finance_status,
        "상태등급": status_level,
        "비상금 분석": emergency_msg,
        "비상금등급": emergency_level,
        "부채 분석": debt_msg,
        "투자 분석": invest_msg,
        "추천 상품 유형": product_types,
        "월별 배분안": allocation,
        "우선순위": priorities[:5],
        "재테크 유형": persona,
        "유형 설명": persona_desc,
        "재무 스트레스 점수": risk_score,
        "재무 스트레스": stress_label,
        "목표 분석": goal_msg,
        "이번 주 미션": missions,
    }


def show_card(title, body):
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def set_example(kind):
    examples = {
        "student": {
            "income": 600000,
            "fixed_expense": 250000,
            "variable_expense": 200000,
            "savings": 300000,
            "investment": 0,
            "debt": 0,
            "goal": "여행자금 마련",
            "period": "6개월",
            "target_amount": 1000000,
            "risk_type": "안정형",
            "experience": "없음",
            "memo": "아르바이트 수입으로 생활비를 쓰고 남은 돈을 모아 여행자금을 만들고 싶습니다."
        },
        "worker": {
            "income": 2500000,
            "fixed_expense": 900000,
            "variable_expense": 600000,
            "savings": 3000000,
            "investment": 500000,
            "debt": 0,
            "goal": "전세자금/독립자금 마련",
            "period": "3년",
            "target_amount": 30000000,
            "risk_type": "중립형",
            "experience": "조금 있음",
            "memo": "사회초년생이고 월급에서 어느 정도를 저축과 투자로 나눠야 할지 고민입니다."
        },
        "debt": {
            "income": 1800000,
            "fixed_expense": 800000,
            "variable_expense": 700000,
            "savings": 200000,
            "investment": 100000,
            "debt": 3000000,
            "goal": "부채 상환과 비상금 마련",
            "period": "1년",
            "target_amount": 3000000,
            "risk_type": "안정형",
            "experience": "없음",
            "memo": "카드값과 대출이 있어서 투자보다 돈 관리 순서를 알고 싶습니다."
        },
        "aggressive": {
            "income": 3200000,
            "fixed_expense": 800000,
            "variable_expense": 500000,
            "savings": 12000000,
            "investment": 8000000,
            "debt": 0,
            "goal": "장기 자산 증식",
            "period": "5년 이상",
            "target_amount": 50000000,
            "risk_type": "공격형",
            "experience": "많음",
            "memo": "생활비는 안정적인 편이고 장기적으로 자산을 늘리고 싶습니다."
        },
    }
    for k, v in examples[kind].items():
        st.session_state[k] = v


st.markdown("""
<div class="hero">
    <div class="main-title">🧭 머니나침반</div>
    <div class="sub-title">
    나의 소득·지출·자산·성향을 바탕으로 재테크 유형을 진단하고, 이번 달 실천 계획까지 제안하는 AI 맞춤형 재무관리 코치
    </div>
    <span class="big-badge">비상금 분석</span>
    <span class="big-badge">소비 위험도</span>
    <span class="big-badge">저축·투자 배분</span>
    <span class="big-badge">AI 코칭</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="notice-box">
<b>서비스 목적</b><br>
청년과 사회초년생이 자신의 재무 상황을 쉽게 이해하고, 비상금·저축·투자의 우선순위를 정할 수 있도록 돕는 참고용 서비스입니다.
특정 금융상품 가입이나 개별 종목 투자를 권유하지 않습니다.
</div>
""", unsafe_allow_html=True)

with st.expander("💡 예시 데이터로 빠르게 테스트하기", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("대학생 예시", use_container_width=True):
            set_example("student")
    with c2:
        if st.button("사회초년생 예시", use_container_width=True):
            set_example("worker")
    with c3:
        if st.button("부채 보유 예시", use_container_width=True):
            set_example("debt")
    with c4:
        if st.button("공격형 투자자 예시", use_container_width=True):
            set_example("aggressive")

st.divider()

left, right = st.columns([1.05, 1])

with left:
    st.subheader("1. 나의 재무 정보 입력")
    income = st.number_input("월 소득", min_value=0, step=10000, value=st.session_state.get("income", 0), key="income")
    fixed_expense = st.number_input("월 고정지출", min_value=0, step=10000, value=st.session_state.get("fixed_expense", 0), key="fixed_expense")
    variable_expense = st.number_input("월 변동지출", min_value=0, step=10000, value=st.session_state.get("variable_expense", 0), key="variable_expense")

    c1, c2 = st.columns(2)
    with c1:
        savings = st.number_input("현재 저축액", min_value=0, step=10000, value=st.session_state.get("savings", 0), key="savings")
    with c2:
        investment = st.number_input("현재 투자금", min_value=0, step=10000, value=st.session_state.get("investment", 0), key="investment")

    debt = st.number_input("현재 부채", min_value=0, step=10000, value=st.session_state.get("debt", 0), key="debt")

with right:
    st.subheader("2. 목표와 성향 입력")

    goal_options = ["비상금 마련", "여행자금 마련", "등록금/학비 마련", "전세자금/독립자금 마련", "부채 상환과 비상금 마련", "장기 자산 증식", "소비 습관 개선"]
    default_goal = st.session_state.get("goal", "비상금 마련")
    goal = st.selectbox("재무 목표", goal_options, index=goal_options.index(default_goal) if default_goal in goal_options else 0, key="goal")

    period_options = ["3개월", "6개월", "1년", "3년", "5년 이상"]
    default_period = st.session_state.get("period", "1년")
    period = st.selectbox("목표 기간", period_options, index=period_options.index(default_period) if default_period in period_options else 2, key="period")

    target_amount = st.number_input("목표 금액", min_value=0, step=100000, value=st.session_state.get("target_amount", 0), key="target_amount")

    risk_options = ["안정형", "중립형", "공격형"]
    default_risk = st.session_state.get("risk_type", "안정형")
    risk_type = st.radio("투자 성향", risk_options, index=risk_options.index(default_risk) if default_risk in risk_options else 0, horizontal=True, key="risk_type")

    exp_options = ["없음", "조금 있음", "많음"]
    default_exp = st.session_state.get("experience", "없음")
    experience = st.selectbox("투자 경험", exp_options, index=exp_options.index(default_exp) if default_exp in exp_options else 0, key="experience")

    memo = st.text_area("추가 상황 설명", value=st.session_state.get("memo", ""), placeholder="예: 월세가 부담돼요. 카드값이 많아요. 1년 안에 200만 원을 모으고 싶어요.", key="memo")

ai_mode = st.selectbox(
    "AI 코칭 모드",
    ["재테크 코치", "소비습관 분석", "목표 달성 전략"],
    help="Gemini API 키가 설정되어 있을 때 선택한 모드에 맞춰 자연어 코멘트가 생성됩니다."
)

analyze = st.button("🔍 내 재테크 방향 분석하기", type="primary", use_container_width=True)

if analyze:
    if income == 0:
        st.warning("월 소득을 입력해주세요. 소득 정보가 있어야 지출 비율과 여유자금을 분석할 수 있습니다.")
    elif fixed_expense + variable_expense == 0:
        st.warning("월 고정지출과 변동지출 중 하나 이상을 입력해주세요.")
    else:
        result = classify_finance(
            income, fixed_expense, variable_expense, savings, investment, debt,
            goal, period, risk_type, experience, target_amount
        )

        user_profile = {
            "월 소득": income,
            "월 고정지출": fixed_expense,
            "월 변동지출": variable_expense,
            "현재 저축액": savings,
            "현재 투자금": investment,
            "현재 부채": debt,
            "재무 목표": goal,
            "목표 기간": period,
            "목표 금액": target_amount,
            "투자 성향": risk_type,
            "투자 경험": experience,
            "추가 상황": memo,
            "AI 코칭 모드": ai_mode,
        }

        st.divider()
        st.subheader("3. 나의 머니 프로필")

        p1, p2 = st.columns([1, 2])
        with p1:
            st.markdown(f"### {result['재테크 유형']}")
            st.caption(result["유형 설명"])
        with p2:
            st.progress(result["재무 스트레스 점수"] / 100)
            st.write(f"재무 스트레스: **{result['재무 스트레스']}** · 점수 {result['재무 스트레스 점수']} / 100")
            st.caption("점수는 지출 비율, 적자 여부, 비상금 수준, 부채 여부를 바탕으로 계산한 참고용 지표입니다.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("월 여유자금", won(result["월 여유자금"]))
        m2.metric("지출 비율", pct(result["지출 비율"]))
        m3.metric("총 보유자산", won(result["총 보유자산"]))
        m4.metric("비상금 목표", won(result["비상금 목표액"]))

        show_card("📌 현재 재무 상태", result["재무상태"])
        show_card("🎯 목표 분석", result["목표 분석"])
        show_card("🛟 비상금 분석", result["비상금 분석"])
        show_card("💳 부채 점검", result["부채 분석"])
        show_card("📈 투자 가능성", result["투자 분석"])

        st.markdown("#### ✅ 지금 해야 할 우선순위")
        for i, item in enumerate(result["우선순위"], start=1):
            st.write(f"{i}. {item}")

        st.markdown("#### 🏦 추천 금융상품 유형")
        st.write(" · ".join(result["추천 상품 유형"]))

        st.markdown("#### 📅 월별 실천 계획 예시")
        alloc_data = [{"항목": k, "추천 금액": won(v)} for k, v in result["월별 배분안"].items() if v > 0]
        if alloc_data:
            st.table(alloc_data)
        else:
            st.info("현재는 배분 가능한 여유자금이 부족합니다. 먼저 지출을 줄여 월 여유자금을 만드는 것이 우선입니다.")

        st.markdown("#### 🧩 이번 주 미션")
        for mission in result["이번 주 미션"]:
            st.write(f"{i}. {mission}")

        mode_map = {"재테크 코치": "coach", "소비습관 분석": "habit", "목표 달성 전략": "goal"}
        with st.spinner("AI 맞춤 코멘트를 생성하는 중입니다..."):
            ai_comment = call_gemini(user_profile, result, mode_map[ai_mode])

        st.markdown("#### 🤖 AI 맞춤 코멘트")
        if ai_comment:
            st.markdown(ai_comment)
        else:
            st.info(
                "Gemini API 키가 설정되어 있지 않아 규칙 기반 분석만 표시했습니다. "
                "Streamlit Cloud의 Secrets에 GEMINI_API_KEY를 추가하면 선택한 코칭 모드에 맞는 자연어 조언이 생성됩니다."
            )

        st.markdown("""
        <div class="warning-box">
        <b>주의사항</b><br>
        본 서비스는 금융상품 가입이나 투자를 직접 권유하는 서비스가 아닙니다.
        사용자가 입력한 정보를 바탕으로 일반적인 재무관리 방향을 안내하는 참고용 도구입니다.
        실제 금융상품 가입 전에는 상품 설명서와 공식 정보를 확인하고 필요시 전문가와 상담해야 합니다.
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("""
<div class="footer">
<b>머니나침반</b>은 AI needs 기획 과제로 제작된 Streamlit 기반 웹서비스입니다.
청년층과 사회초년생의 금융 정보 격차를 줄이고, 자신의 재무 상태를 쉽게 이해하도록 돕는 것을 목표로 합니다.
</div>
""", unsafe_allow_html=True)
