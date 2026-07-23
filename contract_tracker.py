import streamlit as st
import pandas as pd
from datetime import date, timedelta
import random
import io
from urllib.parse import quote

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Contract Expiry Tracker", layout="wide")

REQUIRED_COLUMNS = ["Vendor", "Contract Type", "Start Date", "End Date", "Contract Value (SEK)", "Owner"]

VENDORS = [
    "Nordic Packaging AB", "Baltic Logistics", "Skandinavisk IT-Service",
    "GreenBox Materials", "Helsingborg Fastighetsservice", "Lund Data Solutions",
    "Malmö Transport Group", "Öresund Facility Mgmt", "Svensk Kontorsmaterial",
    "CleanTech Supplies", "Nova Consulting Partners", "Skåne Bygg & Anläggning"
]

CONTRACT_TYPES = [
    "Leveransavtal", "Serviceavtal", "Konsultavtal", "Hyresavtal",
    "Underhållsavtal", "Ramavtal", "Licensavtal"
]

OWNERS = ["Stefan Nguyen", "Anna Berg", "Karim Haddad", "Lisa Ström", "Erik Dahl"]


# ----------------------------
# MOCK DATA
# ----------------------------
def generate_mock_data(n=25):
    random.seed(42)
    rows = []
    today = date.today()

    for i in range(n):
        vendor = random.choice(VENDORS)
        ctype = random.choice(CONTRACT_TYPES)
        owner = random.choice(OWNERS)

        # Spread end dates across past, near future, and far future for realistic demo
        offset_days = random.choice([
            random.randint(-60, -1),      # already expired
            random.randint(1, 30),        # urgent
            random.randint(31, 90),       # soon
            random.randint(91, 365),      # later
        ])
        end = today + timedelta(days=offset_days)
        start = end - timedelta(days=random.choice([365, 730, 1095]))
        value = random.choice([25000, 50000, 120000, 250000, 480000, 750000])

        rows.append({
            "Vendor": vendor,
            "Contract Type": ctype,
            "Start Date": start,
            "End Date": end,
            "Contract Value (SEK)": value,
            "Owner": owner,
        })

    df = pd.DataFrame(rows)
    df["Start Date"] = pd.to_datetime(df["Start Date"])
    df["End Date"] = pd.to_datetime(df["End Date"])
    return df


def get_urgency(days_left):
    if days_left < 0:
        return "Utgånget"
    elif days_left <= 30:
        return "Brådskande (≤30 dagar)"
    elif days_left <= 60:
        return "Snart (31-60 dagar)"
    elif days_left <= 90:
        return "Bevaka (61-90 dagar)"
    else:
        return "OK (>90 dagar)"


URGENCY_ORDER = ["Utgånget", "Brådskande (≤30 dagar)", "Snart (31-60 dagar)", "Bevaka (61-90 dagar)", "OK (>90 dagar)"]

URGENCY_COLOR = {
    "Utgånget": "#7a1f1f",
    "Brådskande (≤30 dagar)": "#d64545",
    "Snart (31-60 dagar)": "#e0a030",
    "Bevaka (61-90 dagar)": "#e8d34a",
    "OK (>90 dagar)": "#4a9e5c",
}


def style_urgency(val):
    color = URGENCY_COLOR.get(val, "#ffffff")
    return f"background-color: {color}; color: white; font-weight: 600;"


# ----------------------------
# EMAIL DRAFT
# ----------------------------
def build_email_draft(row):
    days_left = row["Days Left"]
    vendor = row["Vendor"]
    ctype = row["Contract Type"]
    end_date = row["End Date"].strftime("%Y-%m-%d")
    owner = row["Owner"]

    if days_left < 0:
        status_line = f"OBS: Detta avtal gick ut {end_date} och behöver hanteras omgående."
    else:
        status_line = f"Avtalet löper ut {end_date}, om {days_left} dagar."

    subject = f"Påminnelse: {ctype} med {vendor} går ut snart"

    body = f"""Hej {owner},

Detta är en automatisk påminnelse gällande vårt avtal med {vendor}.

Avtalstyp: {ctype}
Slutdatum: {end_date}
Status: {status_line}

Vänligen bekräfta om avtalet ska:
- Förnyas
- Omförhandlas
- Avslutas

Hör av dig så snart som möjligt så vi hinner agera i tid.

Med vänlig hälsning,
Inköp / Avtalsuppföljning"""

    return subject, body


# ----------------------------
# UI
# ----------------------------
st.title("📋 Contract Expiry Tracker")
st.caption("Portfolio-demo, körs mot mockdata. Ladda upp egen CSV eller använd genererad exempeldata.")

with st.expander("Hur funkar det?", expanded=False):
    st.markdown("""
1. Ladda upp en CSV med kontrakt, eller klicka på **Generera exempeldata**
2. Dashboarden visar hur många kontrakt som går ut inom 30/60/90 dagar
3. Filtrera på leverantör, avtalstyp eller brådska
4. Klicka på ett kontrakt för att få ett färdigt utkast till påminnelsemail

**Förväntat CSV-format:** Vendor, Contract Type, Start Date, End Date, Contract Value (SEK), Owner
""")

col_a, col_b = st.columns([2, 1])

with col_a:
    uploaded = st.file_uploader("Ladda upp kontrakts-CSV", type=["csv"])
with col_b:
    st.write("")
    st.write("")
    generate = st.button("🎲 Generera exempeldata")

if "df" not in st.session_state:
    st.session_state.df = None

if generate:
    st.session_state.df = generate_mock_data()

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded, parse_dates=["Start Date", "End Date"])
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(f"CSV saknar kolumner: {', '.join(missing)}")
        else:
            st.session_state.df = df
    except Exception as e:
        st.error("Kunde inte läsa CSV-filen. Kontrollera formatet.")
        with st.expander("Teknisk detalj"):
            st.write(e)

df = st.session_state.df

if df is None:
    st.info("👆 Ladda upp en CSV eller klicka på 'Generera exempeldata' för att komma igång.")
    st.stop()

# ----------------------------
# PROCESS DATA
# ----------------------------
today = pd.Timestamp(date.today())
df = df.copy()
df["Days Left"] = (df["End Date"] - today).dt.days
df["Urgency"] = df["Days Left"].apply(get_urgency)

# ----------------------------
# METRICS
# ----------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Totalt antal kontrakt", len(df))
m2.metric("Brådskande (≤30 dagar)", int((df["Days Left"].between(0, 30)).sum()))
m3.metric("Snart (31-90 dagar)", int((df["Days Left"].between(31, 90)).sum()))
m4.metric("Redan utgångna", int((df["Days Left"] < 0).sum()))

st.markdown("---")

# ----------------------------
# FILTERS
# ----------------------------
f1, f2, f3 = st.columns(3)

with f1:
    vendor_filter = st.multiselect("Leverantör", sorted(df["Vendor"].unique()))
with f2:
    type_filter = st.multiselect("Avtalstyp", sorted(df["Contract Type"].unique()))
with f3:
    urgency_filter = st.multiselect("Brådska", URGENCY_ORDER)

filtered = df.copy()
if vendor_filter:
    filtered = filtered[filtered["Vendor"].isin(vendor_filter)]
if type_filter:
    filtered = filtered[filtered["Contract Type"].isin(type_filter)]
if urgency_filter:
    filtered = filtered[filtered["Urgency"].isin(urgency_filter)]

filtered = filtered.sort_values("Days Left")

# ----------------------------
# TABLE
# ----------------------------
st.subheader(f"Kontrakt ({len(filtered)})")

display_df = filtered[["Vendor", "Contract Type", "End Date", "Days Left", "Urgency", "Contract Value (SEK)", "Owner"]].copy()
display_df["End Date"] = display_df["End Date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    display_df.style.map(style_urgency, subset=["Urgency"]),
    use_container_width=True,
    hide_index=True,
)

# Download filtered data
csv_buffer = io.StringIO()
display_df.to_csv(csv_buffer, index=False)
st.download_button("⬇️ Ladda ner filtrerad lista (CSV)", csv_buffer.getvalue(), "contracts_filtered.csv", "text/csv")

st.markdown("---")

# ----------------------------
# EMAIL DRAFT GENERATOR
# ----------------------------
st.subheader("✉️ Generera påminnelsemail")

if len(filtered) == 0:
    st.warning("Inga kontrakt matchar filtren.")
else:
    options = [
        f"{row['Vendor']} - {row['Contract Type']} (går ut {row['End Date'].strftime('%Y-%m-%d')})"
        for _, row in filtered.iterrows()
    ]
    choice = st.selectbox("Välj kontrakt", options)
    selected_idx = options.index(choice)
    selected_row = filtered.iloc[selected_idx]

    subject, body = build_email_draft(selected_row)

    contract_key = f"{selected_row['Vendor']}_{selected_row['End Date'].strftime('%Y-%m-%d')}"
    edited_subject = st.text_input("Ämnesrad", value=subject, key=f"email_subject_{contract_key}")
    edited_body = st.text_area("Meddelande", value=body, height=280, key=f"email_body_{contract_key}")

    st.caption("Kopiera texten ovan till ditt mailprogram.")

    mailto_url = f"mailto:?subject={quote(edited_subject)}&body={quote(edited_body)}"
    st.link_button("📧 Öppna i mailprogram", mailto_url)
    st.caption("Öppnar ditt standardmailprogram med färdigifyllt utkast — inget skickas automatiskt.")
