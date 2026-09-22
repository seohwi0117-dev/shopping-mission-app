import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
from html import escape


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="장보기 미션",
    page_icon="🛒",
    layout="wide"
)

# 미션과 예산
MISSIONS = {
    "🍛 카레 만들기": 15000,
    "⛺ 여름캠핑 준비하기": 50000,
    "🎂 친구 생일 파티 준비하기": 30000
}


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .sub-title {
        text-align: center;
        font-size: 20px;
        color: #555;
        margin-bottom: 30px;
    }

    .mission-card {
        padding: 25px;
        border-radius: 20px;
        border: 2px solid #e5e7eb;
        background-color: #ffffff;
        text-align: center;
        min-height: 180px;
    }

    .product-card {
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #dddddd;
        background-color: white;
        margin-bottom: 10px;
    }

    .price {
        font-size: 20px;
        font-weight: bold;
    }

    .cart-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #f5f7fa;
        border: 2px solid #dfe3e8;
    }

    .budget-good {
        color: #16803c;
        font-weight: bold;
    }

    .budget-warning {
        color: #d93025;
        font-weight: bold;
    }

    .result-title {
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# Session State 초기화
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "start"

if "mission" not in st.session_state:
    st.session_state.mission = None

if "budget" not in st.session_state:
    st.session_state.budget = 0

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "reason" not in st.session_state:
    st.session_state.reason = ""


# =========================================================
# 상품 CSV 불러오기
# =========================================================

@st.cache_data
def load_products():
    try:
        df = pd.read_csv("products.csv", encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv("products.csv", encoding="cp949")

    required_columns = ["품명", "가격", "이미지 url"]

    for col in required_columns:
        if col not in df.columns:
            st.error(
                f"products.csv에 '{col}' 열이 필요합니다."
            )
            st.stop()

    df["가격"] = pd.to_numeric(
        df["가격"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["품명"] = df["품명"].astype(str)
    df["이미지 url"] = df["이미지 url"].fillna("").astype(str)

    return df


products = load_products()


# =========================================================
# 금액 표시
# =========================================================

def money(value):
    return f"{int(value):,}원"


# =========================================================
# 장바구니 총액
# =========================================================

def get_cart_total():
    total = 0

    for product_name, quantity in st.session_state.cart.items():

        product_row = products[
            products["품명"] == product_name
        ]

        if not product_row.empty:
            price = int(product_row.iloc[0]["가격"])
            total += price * quantity

    return total


# =========================================================
# 시작 화면
# =========================================================

def show_start():

    st.markdown(
        '<div class="main-title">🛒 장보기 미션</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        '어떤 미션을 해결할까요?'
        '</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)

    for index, (mission, budget) in enumerate(MISSIONS.items()):

        with cols[index]:

            st.markdown(
                f"""
                <div class="mission-card">
                    <h2>{mission}</h2>
                    <p style="font-size:18px;">
                        사용할 수 있는 돈
                    </p>
                    <h2>{money(budget)}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            if st.button(
                "이 미션 선택하기",
                key=f"mission_{index}",
                use_container_width=True
            ):
                st.session_state.mission = mission
                st.session_state.budget = budget
                st.session_state.cart = {}
                st.session_state.reason = ""
                st.session_state.page = "shopping"

                st.rerun()


# =========================================================
# 장바구니 추가
# =========================================================

def add_to_cart(product_name, quantity):

    if quantity <= 0:
        return

    if product_name not in st.session_state.cart:
        st.session_state.cart[product_name] = 0

    st.session_state.cart[product_name] += quantity


# =========================================================
# 쇼핑 화면
# =========================================================

def show_shopping():

    mission = st.session_state.mission
    budget = st.session_state.budget

    st.markdown(
        f"""
        <div class="main-title">🛍️ 장보기</div>
        <div class="sub-title">
            미션: <b>{mission}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # 예산 정보
    # -----------------------------------------------------

    total = get_cart_total()
    remaining = budget - total

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🎯 미션 예산",
            money(budget)
        )

    with col2:
        st.metric(
            "🛒 사용 금액",
            money(total)
        )

    with col3:
        st.metric(
            "💰 남은 돈",
            money(remaining)
        )

    if total > budget:
        st.error(
            f"⚠️ 예산을 {money(total - budget)} 초과했습니다!"
            " 물건을 줄여 주세요."
        )
    else:
        st.success(
            f"예산 안에서 {money(remaining)}이 남았습니다."
        )

    st.divider()

    # -----------------------------------------------------
    # 상품 진열
    # -----------------------------------------------------

    st.subheader("🛒 상품을 골라 보세요!")

    # 4개씩 상품 표시
    product_rows = [
        products.iloc[i:i + 4]
        for i in range(0, len(products), 4)
    ]

    for row in product_rows:

        cols = st.columns(4)

        for col, (_, product) in zip(cols, row.iterrows()):

            with col:

                product_name = product["품명"]
                price = int(product["가격"])
                image_url = product["이미지 url"]

                st.markdown(
                    '<div class="product-card">',
                    unsafe_allow_html=True
                )

                # 상품 이미지
                if image_url and image_url != "nan":
                    try:
                        st.image(
                            image_url,
                            use_container_width=True
                        )
                    except Exception:
                        st.write("🛍️")

                st.markdown(
                    f"### {product_name}"
                )

                st.markdown(
                    f'<div class="price">{money(price)}</div>',
                    unsafe_allow_html=True
                )

                quantity = st.number_input(
                    "수량",
                    min_value=0,
                    max_value=99,
                    value=0,
                    step=1,
                    key=f"quantity_{product_name}"
                )

                if st.button(
                    "🛒 장바구니 담기",
                    key=f"add_{product_name}",
                    use_container_width=True
                ):

                    if quantity > 0:
                        add_to_cart(
                            product_name,
                            quantity
                        )

                        st.success(
                            f"{product_name} {quantity}개 담았어요!"
                        )

                        st.rerun()

                    else:
                        st.warning(
                            "수량을 먼저 선택해 주세요."
                        )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

    # -----------------------------------------------------
    # 장바구니
    # -----------------------------------------------------

    st.divider()

    st.subheader("🛒 장바구니")

    if not st.session_state.cart:

        st.info(
            "아직 장바구니에 담은 물건이 없어요."
        )

    else:

        for product_name in list(
            st.session_state.cart.keys()
        ):

            quantity = st.session_state.cart[
                product_name
            ]

            product_row = products[
                products["품명"] == product_name
            ]

            if product_row.empty:
                continue

            price = int(
                product_row.iloc[0]["가격"]
            )

            subtotal = price * quantity

            col1, col2, col3, col4 = st.columns(
                [3, 1, 2, 1]
            )

            with col1:
                st.write(
                    f"**{product_name}**"
                )

            with col2:
                st.write(
                    f"{quantity}개"
                )

            with col3:
                st.write(
                    money(subtotal)
                )

            with col4:

                if st.button(
                    "삭제",
                    key=f"delete_{product_name}"
                ):

                    del st.session_state.cart[
                        product_name
                    ]

                    st.rerun()

        # 최신 금액
        total = get_cart_total()
        remaining = budget - total

        st.markdown(
            '<div class="cart-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            ### 💰 장보기 계산

            - 미션 예산: **{money(budget)}**
            - 사용 금액: **{money(total)}**
            - 남은 돈: **{money(remaining)}**
            """,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        st.write("")

        # -------------------------------------------------
        # 제출
        # -------------------------------------------------

        if total > budget:

            st.error(
                "⚠️ 예산을 초과했어요. "
                "물건을 줄인 뒤 제출해 주세요."
            )

            st.button(
                "제출하기",
                disabled=True,
                use_container_width=True
            )

        elif total == 0:

            st.warning(
                "물건을 하나 이상 장바구니에 담아 주세요."
            )

            st.button(
                "제출하기",
                disabled=True,
                use_container_width=True
            )

        else:

            if st.button(
                "✅ 장보기 결과 제출하기",
                type="primary",
                use_container_width=True
            ):

                st.session_state.page = "result"

                st.rerun()


# =========================================================
# SVG용 이미지 다운로드
# =========================================================

@st.cache_data(show_spinner=False)
def image_to_data_uri(url):

    if not url or url == "nan":
        return None

    try:

        response = requests.get(
            url,
            timeout=5
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "image/jpeg"
        )

        encoded = base64.b64encode(
            response.content
        ).decode("utf-8")

        return (
            f"data:{content_type};base64,{encoded}"
        )

    except Exception:
        return None


# =========================================================
# 결과 이미지 SVG 만들기
# =========================================================

def create_result_svg():

    mission = st.session_state.mission
    budget = st.session_state.budget
    reason = st.session_state.reason

    total = get_cart_total()
    remaining = budget - total

    width = 1000

    # 상품 하나당 높이
    item_height = 150

    header_height = 260

    footer_height = 100

    height = (
        header_height
        + len(st.session_state.cart) * item_height
        + footer_height
    )

    svg = []

    svg.append(
        f"""
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="{width}"
            height="{height}"
            viewBox="0 0 {width} {height}"
        >
        <rect
            width="100%"
            height="100%"
            fill="#ffffff"
        />

        <text
            x="50%"
            y="70"
            text-anchor="middle"
            font-size="38"
            font-weight="bold"
            font-family="Arial, sans-serif"
        >
            🛒 장보기 미션 결과
        </text>

        <text
            x="50%"
            y="125"
            text-anchor="middle"
            font-size="30"
            font-weight="bold"
            font-family="Arial, sans-serif"
        >
            미션: {escape(mission)}
        </text>

        <text
            x="50%"
            y="180"
            text-anchor="middle"
            font-size="24"
            font-family="Arial, sans-serif"
        >
            예산 {money(budget)}
            · 사용 {money(total)}
            · 남은 돈 {money(remaining)}
        </text>

        <line
            x1="50"
            y1="215"
            x2="950"
            y2="215"
            stroke="#cccccc"
            stroke-width="2"
        />
        """
    )

    y = 250

    for product_name, quantity in st.session_state.cart.items():

        product_row = products[
            products["품명"] == product_name
        ]

        if product_row.empty:
            continue

        product = product_row.iloc[0]

        price = int(product["가격"])
        subtotal = price * quantity
        image_url = product["이미지 url"]

        data_uri = image_to_data_uri(
            image_url
        )

        # 상품 이미지
        if data_uri:

            svg.append(
                f"""
                <image
                    href="{data_uri}"
                    x="60"
                    y="{y}"
                    width="100"
                    height="100"
                    preserveAspectRatio="xMidYMid slice"
                />
                """
            )

        else:

            svg.append(
                f"""
                <rect
                    x="60"
                    y="{y}"
                    width="100"
                    height="100"
                    fill="#eeeeee"
                    rx="10"
                />

                <text
                    x="110"
                    y="{y + 60}"
                    text-anchor="middle"
                    font-size="30"
                >
                    🛍️
                </text>
                """
            )

        svg.append(
            f"""
            <text
                x="200"
                y="{y + 35}"
                font-size="26"
                font-weight="bold"
                font-family="Arial, sans-serif"
            >
                {escape(product_name)}
            </text>

            <text
                x="200"
                y="{y + 75}"
                font-size="22"
                font-family="Arial, sans-serif"
            >
                {quantity}개 × {money(price)}
                = {money(subtotal)}
            </text>
            """
        )

        y += item_height

    # 구매 이유
    svg.append(
        f"""
        <line
            x1="50"
            y1="{y}"
            x2="950"
            y2="{y}"
            stroke="#cccccc"
            stroke-width="2"
        />

        <text
            x="60"
            y="{y + 50}"
            font-size="25"
            font-weight="bold"
            font-family="Arial, sans-serif"
        >
            💡 내가 이렇게 장바구니를 구성한 이유
        </text>

        <text
            x="60"
            y="{y + 90}"
            font-size="21"
            font-family="Arial, sans-serif"
        >
            {escape(reason)}
        </text>
        """
    )

    y += 130

    svg.append(
        f"""
        <text
            x="50%"
            y="{y}"
            text-anchor="middle"
            font-size="22"
            font-family="Arial, sans-serif"
        >
            나의 장보기 미션 완료!
        </text>

        </svg>
        """
    )

    return "".join(svg)


# =========================================================
# 결과 화면
# =========================================================

def show_result():

    mission = st.session_state.mission
    budget = st.session_state.budget

    total = get_cart_total()
    remaining = budget - total

    st.markdown(
        '<div class="result-title">'
        '🎉 장보기 미션 결과'
        '</div>',
        unsafe_allow_html=True
    )

    st.info(
        f"미션: **{mission}**"
    )

    # -----------------------------------------------------
    # 구매 목록
    # -----------------------------------------------------

    st.subheader("🛍️ 내가 구매한 물건")

    for product_name, quantity in st.session_state.cart.items():

        product_row = products[
            products["품명"] == product_name
        ]

        if product_row.empty:
            continue

        product = product_row.iloc[0]

        price = int(product["가격"])
        subtotal = price * quantity
        image_url = product["이미지 url"]

        col1, col2, col3, col4 = st.columns(
            [1, 3, 1, 2]
        )

        with col1:

            if image_url:
                st.image(
                    image_url,
                    width=80
                )

        with col2:

            st.write(
                f"**{product_name}**"
            )

        with col3:

            st.write(
                f"{quantity}개"
            )

        with col4:

            st.write(
                money(subtotal)
            )

    st.divider()

    # -----------------------------------------------------
    # 금액
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🎯 예산",
            money(budget)
        )

    with col2:
        st.metric(
            "💳 사용 금액",
            money(total)
        )

    with col3:
        st.metric(
            "💰 남은 돈",
            money(remaining)
        )

    st.divider()

    # -----------------------------------------------------
    # 구매 이유
    # -----------------------------------------------------

    st.subheader(
        "💡 왜 이 물건들을 골랐나요?"
    )

    reason = st.text_area(
        "구매 이유를 적어 보세요.",
        value=st.session_state.reason,
        placeholder=(
            "예: 카레를 만들기 위해 필요한 재료를 "
            "중심으로 골랐어요."
        ),
        height=150,
        key="reason_input"
    )

    st.session_state.reason = reason.strip()

    if st.session_state.reason:

        st.success(
            "구매 이유를 작성했어요! "
            "이제 나의 장보기 결과를 그림으로 저장할 수 있어요."
        )

        svg_data = create_result_svg()

        st.download_button(
            label="🖼️ 그림으로 저장",
            data=svg_data.encode("utf-8"),
            file_name="장보기_미션_결과.svg",
            mime="image/svg+xml",
            use_container_width=True
        )

    else:

        st.info(
            "구매 이유를 작성하면 "
            "'그림으로 저장' 버튼이 나타납니다."
        )


# =========================================================
# 화면 실행
# =========================================================

if st.session_state.page == "start":

    show_start()

elif st.session_state.page == "shopping":

    show_shopping()

elif st.session_state.page == "result":

    show_result()
