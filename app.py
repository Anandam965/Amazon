import os
from html import escape
from urllib.parse import quote_plus, urlparse

import streamlit as st
from supabase import Client, create_client


st.set_page_config(page_title="Mana Deals", page_icon="🛍️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Noto+Sans+Telugu:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans','Noto Sans Telugu',sans-serif; }
    .stApp { background: #f7f8fa; }
    .hero { padding: 2.2rem 2.4rem; border-radius: 24px; color: white;
        background: linear-gradient(115deg,#101a2d,#193b48 62%,#e78347); margin: .5rem 0 1.4rem; }
    .hero h1 { font-size: clamp(2rem,4vw,3.1rem); margin: 0 0 .45rem; color: white; }
    .hero p { font-size: 1.05rem; color: #e6eef0; margin: 0; }
    .deal { background: white; border: 1px solid #e8eaee; border-radius: 18px; padding: 1rem;
        margin-bottom: .8rem; min-height: 295px; box-shadow: 0 5px 20px #15233a0a; }
    .deal img { width: 100%; height: 168px; object-fit: contain; border-radius: 12px; background:#f7f8fa; }
    .tag { display:inline-block; padding:3px 9px; border-radius:999px; background:#fff0e7; color:#b94e19; font-size:.78rem; font-weight:700; }
    .price { font-size:1.25rem; font-weight:800; color:#142238; }
    .old { color:#9098a5; text-decoration:line-through; margin-left:7px; font-size:.92rem; }
    .deal h3 { font-size:1rem; line-height:1.4; height:2.8em; overflow:hidden; margin:.7rem 0 .3rem; }
    .fine { color:#606b7b; font-size:.84rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def config_value(key: str):
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key)


@st.cache_resource
def get_supabase() -> Client:
    url = config_value("SUPABASE_URL")
    key = config_value("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase configuration is missing")
    return create_client(url, key)


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_deals():
    return (
        get_supabase()
        .table("deals")
        .select("id,title,category,price,original_price,image_url,affiliate_url,description,featured,created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )


def render_card(deal):
    title = escape(str(deal.get("title", "Deal")))
    image = escape(str(deal.get("image_url") or ""), quote=True)
    category = escape(str(deal.get("category") or "Deals"))
    try:
        price = float(deal.get("price") or 0)
        original = float(deal.get("original_price") or 0)
    except (ValueError, TypeError):
        price, original = 0, 0
    image_html = f'<img src="{image}" alt="{title}" loading="lazy">' if valid_http_url(image) else '<div style="height:168px;background:#f7f8fa;border-radius:12px;display:grid;place-items:center;font-size:3rem">🛍️</div>'
    st.markdown(
        f'<div class="deal">{image_html}<div style="margin-top:10px"><span class="tag">{category}</span>'
        f'{" <span class=tag>⭐ Featured</span>" if deal.get("featured") else ""}</div>'
        f'<h3>{title}</h3><div><span class="price">₹{price:,.0f}</span>'
        f'{f"<span class=old>₹{original:,.0f}</span>" if original > price else ""}</div>'
        f'<p class="fine">{escape(str(deal.get("description") or ""))}</p></div>',
        unsafe_allow_html=True,
    )
    link = deal.get("affiliate_url", "")
    if valid_http_url(link):
        st.caption("Paid link · affiliate link")
        st.link_button("Amazonలో Deal చూడండి ↗", link, use_container_width=True)


st.markdown(
    '<div class="hero"><h1>🛍️ Smart Shopping with Sai</h1><p>Amazonలో ఈరోజు offers వెతకండి · మీకు నచ్చిన category ఎంచుకోండి.</p></div>',
    unsafe_allow_html=True,
)
st.caption("As an Amazon Associate I earn from qualifying purchases.")
st.caption("గమనిక: Amazon‌కు వెళ్లే లింకులు affiliate links కావచ్చు (paid links). ధరలు, stock మారవచ్చు; కొనుగోలు ముందు Amazonలో తనిఖీ చేయండి.")

# Temporary starter links based on the Store ID visible in the supplied screenshot.
tracking_id = "mrvnsai-21"
starter_links = [
    ("📱 మొబైళ్లు", "smartphones"),
    ("🎧 Earbuds", "wireless earbuds"),
    ("💻 Laptops", "laptops"),
    ("🍳 Kitchen", "kitchen appliances"),
    ("🏠 Home", "home essentials"),
    ("⌚ Smart Watches", "smart watches"),
]
st.subheader("Amazon Quick Links")
st.caption("తాత్కాలిక links · Amazon search ఫలితాలు తెరుచుకుంటాయి; ఇవి నిర్దిష్ట deal లేదా ధరకు హామీ కావు.")
for start in range(0, len(starter_links), 3):
    cols = st.columns(3, gap="medium")
    for col, (label, term) in zip(cols, starter_links[start : start + 3]):
        with col:
            amazon_url = f"https://www.amazon.in/s?k={quote_plus(term)}&tag={tracking_id}"
            st.link_button(f"{label} ↗", amazon_url, use_container_width=True)

try:
    deals = load_deals()
except Exception as exc:
    st.error("Supabase‌కు కనెక్ట్ కాలేకపోయాం. Streamlit Secrets మరియు Supabase setup తనిఖీ చేయండి.")
    with st.expander("సాంకేతిక వివరాలు"):
        st.code(str(exc))
    st.stop()

categories = sorted({d.get("category", "Other") or "Other" for d in deals})
left, right = st.columns([3, 1])
with left:
    query = st.text_input("🔎 Deal వెతకండి", placeholder="ఉదా: headphones, phone, kitchen")
with right:
    category_filter = st.selectbox("Category", ["అన్నీ"] + categories)

visible = deals
if query.strip():
    term = query.strip().casefold()
    visible = [d for d in visible if term in (str(d.get("title", "")) + " " + str(d.get("description", ""))).casefold()]
if category_filter != "అన్నీ":
    visible = [d for d in visible if d.get("category") == category_filter]

if visible:
    st.subheader(f"ఈరోజు Deals  ·  {len(visible)}")
    for start in range(0, len(visible), 3):
        cols = st.columns(3, gap="medium")
        for col, deal in zip(cols, visible[start : start + 3]):
            with col:
                render_card(deal)
else:
    st.info("ఇంకా deals లేవు. Admin విభాగం నుంచి మీ మొదటి deal జోడించండి.")

st.divider()
with st.expander("🔐 Admin · Deal జోడించండి లేదా తొలగించండి"):
    admin_pin = config_value("ADMIN_PIN")
    if not admin_pin:
        st.warning("Admin PIN‌ను Streamlit Secrets‌లో సెట్ చేసిన తర్వాత ఈ విభాగం అందుబాటులోకి వస్తుంది.")
    else:
        pin = st.text_input("Admin PIN", type="password", key="admin_pin")
        if pin and pin == str(admin_pin):
            with st.form("add_deal", clear_on_submit=True):
                st.subheader("కొత్త Deal")
                title = st.text_input("Product పేరు *")
                c1, c2 = st.columns(2)
                with c1:
                    category = st.text_input("Category", value="Electronics")
                    price = st.number_input("Deal ధర (₹) *", min_value=0.0, step=100.0)
                with c2:
                    original_price = st.number_input("పాత ధర (₹)", min_value=0.0, step=100.0)
                    featured = st.checkbox("Featured deal")
                image_url = st.text_input("Image URL (ఐచ్ఛికం)")
                affiliate_url = st.text_input("మీ Amazon affiliate link *")
                description = st.text_area("చిన్న వివరణ")
                submitted = st.form_submit_button("Deal జోడించండి", type="primary")
                if submitted:
                    if not title.strip() or price <= 0 or not valid_http_url(affiliate_url):
                        st.error("Product పేరు, సరైన ధర, http/https affiliate link అవసరం.")
                    elif image_url and not valid_http_url(image_url):
                        st.error("Image URL http లేదా https తో మొదలవ్వాలి.")
                    else:
                        payload = {
                            "title": title.strip(), "category": category.strip() or "Other",
                            "price": price, "original_price": original_price or None,
                            "image_url": image_url.strip() or None, "affiliate_url": affiliate_url.strip(),
                            "description": description.strip() or None, "featured": featured,
                        }
                        try:
                            get_supabase().table("deals").insert(payload).execute()
                            st.success("Deal జోడించబడింది.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Deal save కాలేదు: {exc}")
            if deals:
                st.subheader("ప్రస్తుత Deals తొలగించండి")
                choices = {f'{d.get("title", "Deal")} · {d.get("id")}': d.get("id") for d in deals}
                selected = st.selectbox("తొలగించాల్సిన Deal", list(choices))
                if st.button("ఎంచుకున్న Deal తొలగించండి", type="secondary"):
                    try:
                        get_supabase().table("deals").delete().eq("id", choices[selected]).execute()
                        st.success("Deal తొలగించబడింది.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Deal తొలగించలేకపోయాం: {exc}")
        elif pin:
            st.error("PIN సరిపోలలేదు.")

st.markdown("---")
st.caption("Mana Deals · సమాచారం మారవచ్చు. కొనుగోలు నిర్ణయం తీసుకునే ముందు Amazonలో ప్రస్తుత ధర, వివరాలు పరిశీలించండి.")
