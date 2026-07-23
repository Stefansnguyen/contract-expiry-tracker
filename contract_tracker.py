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

# Canonical (Swedish) contract types. All internal storage/filtering uses these
# values; display labels are translated via translate_contract_type().
CONTRACT_TYPES = [
    "Leveransavtal", "Serviceavtal", "Konsultavtal", "Hyresavtal",
    "Underhållsavtal", "Ramavtal", "Licensavtal"
]

OWNERS = ["Stefan Nguyen", "Anna Berg", "Karim Haddad", "Lisa Ström", "Erik Dahl"]

# ----------------------------
# TRANSLATIONS
# ----------------------------
TRANSLATIONS = {
    "sv": {
        "language_label": "Språk",
        "app_title": "📋 Contract Expiry Tracker",
        "caption_intro": "Portfolio-demo, körs mot mockdata. Ladda upp egen CSV eller använd genererad exempeldata.",
        "how_it_works_expander": "Hur funkar det?",
        "how_it_works_body": """
1. Ladda upp en CSV med kontrakt, eller klicka på **Generera exempeldata**
2. Dashboarden visar hur många kontrakt som går ut inom 30/60/90 dagar
3. Filtrera på leverantör, avtalstyp eller brådska
4. Klicka på ett kontrakt för att få ett färdigt utkast till påminnelsemail

**Förväntat CSV-format:** Vendor, Contract Type, Start Date, End Date, Contract Value (SEK), Owner
""",
        "upload_label": "Ladda upp kontrakts-CSV",
        "generate_button": "🎲 Generera exempeldata",
        "csv_missing_cols": "CSV saknar kolumner: {cols}",
        "csv_read_error": "Kunde inte läsa CSV-filen. Kontrollera formatet.",
        "technical_detail": "Teknisk detalj",
        "no_data_info": "👆 Ladda upp en CSV eller klicka på 'Generera exempeldata' för att komma igång.",
        "metric_total": "Totalt antal kontrakt",
        "metric_urgent": "Brådskande (≤30 dagar)",
        "metric_soon": "Snart (31-90 dagar)",
        "metric_expired": "Redan utgångna",
        "filter_vendor": "Leverantör",
        "filter_type": "Avtalstyp",
        "filter_urgency": "Brådska",
        "table_subheader": "Kontrakt ({n})",
        "download_filtered_csv": "⬇️ Ladda ner filtrerad lista (CSV)",
        "email_subheader": "✉️ Generera påminnelsemail",
        "no_contracts_warning": "Inga kontrakt matchar filtren.",
        "select_contract_label": "Välj kontrakt",
        "option_template": "{vendor} - {ctype} (går ut {date})",
        "subject_label": "Ämnesrad",
        "body_label": "Meddelande",
        "copy_caption": "Kopiera texten ovan till ditt mailprogram.",
        "open_mail_button": "📧 Öppna i mailprogram",
        "mailto_caption": "Öppnar ditt standardmailprogram med färdigifyllt utkast — inget skickas automatiskt.",
        # email draft
        "email_greeting": "Hej {owner},",
        "email_intro": "Detta är en automatisk påminnelse gällande vårt avtal med {vendor}.",
        "email_contract_type_line": "Avtalstyp: {ctype}",
        "email_end_date_line": "Slutdatum: {end_date}",
        "email_status_line": "Status: {status}",
        "email_status_expired": "OBS: Detta avtal gick ut {end_date} och behöver hanteras omgående.",
        "email_status_active": "Avtalet löper ut {end_date}, om {days_left} dagar.",
        "email_confirm_line": "Vänligen bekräfta om avtalet ska:",
        "email_option_renew": "Förnyas",
        "email_option_renegotiate": "Omförhandlas",
        "email_option_terminate": "Avslutas",
        "email_closing_line": "Hör av dig så snart som möjligt så vi hinner agera i tid.",
        "email_signature_greeting": "Med vänlig hälsning,",
        "email_signature_role": "Inköp / Avtalsuppföljning",
        "email_subject": "Påminnelse: {ctype} med {vendor} går ut snart",
    },
    "en": {
        "language_label": "Language",
        "app_title": "📋 Contract Expiry Tracker",
        "caption_intro": "Portfolio demo, running on mock data. Upload your own CSV or use generated example data.",
        "how_it_works_expander": "How does it work?",
        "how_it_works_body": """
1. Upload a CSV with contracts, or click **Generate example data**
2. The dashboard shows how many contracts expire within 30/60/90 days
3. Filter by vendor, contract type, or urgency
4. Click a contract to get a ready-made reminder email draft

**Expected CSV format:** Vendor, Contract Type, Start Date, End Date, Contract Value (SEK), Owner
""",
        "upload_label": "Upload contract CSV",
        "generate_button": "🎲 Generate example data",
        "csv_missing_cols": "CSV is missing columns: {cols}",
        "csv_read_error": "Could not read the CSV file. Check the format.",
        "technical_detail": "Technical detail",
        "no_data_info": "👆 Upload a CSV or click 'Generate example data' to get started.",
        "metric_total": "Total contracts",
        "metric_urgent": "Urgent (≤30 days)",
        "metric_soon": "Soon (31-90 days)",
        "metric_expired": "Already expired",
        "filter_vendor": "Vendor",
        "filter_type": "Contract Type",
        "filter_urgency": "Urgency",
        "table_subheader": "Contracts ({n})",
        "download_filtered_csv": "⬇️ Download filtered list (CSV)",
        "email_subheader": "✉️ Generate reminder email",
        "no_contracts_warning": "No contracts match the filters.",
        "select_contract_label": "Select contract",
        "option_template": "{vendor} - {ctype} (expires {date})",
        "subject_label": "Subject",
        "body_label": "Message",
        "copy_caption": "Copy the text above into your mail client.",
        "open_mail_button": "📧 Open in mail client",
        "mailto_caption": "Opens your default mail client with a pre-filled draft — nothing is sent automatically.",
        # email draft
        "email_greeting": "Hi {owner},",
        "email_intro": "This is an automatic reminder regarding our agreement with {vendor}.",
        "email_contract_type_line": "Contract type: {ctype}",
        "email_end_date_line": "End date: {end_date}",
        "email_status_line": "Status: {status}",
        "email_status_expired": "NOTE: This agreement expired on {end_date} and needs to be handled immediately.",
        "email_status_active": "The agreement expires on {end_date}, in {days_left} days.",
        "email_confirm_line": "Please confirm whether the agreement should be:",
        "email_option_renew": "Renewed",
        "email_option_renegotiate": "Renegotiated",
        "email_option_terminate": "Terminated",
        "email_closing_line": "Please get back to us as soon as possible so we have time to act.",
        "email_signature_greeting": "Best regards,",
        "email_signature_role": "Procurement / Contract Management",
        "email_subject": "Reminder: {ctype} with {vendor} expires soon",
    },
}

CONTRACT_TYPE_TRANSLATIONS = {
    "sv": {ctype: ctype for ctype in CONTRACT_TYPES},
    "en": {
        "Leveransavtal": "Supply Agreement",
        "Serviceavtal": "Service Agreement",
        "Konsultavtal": "Consulting Agreement",
        "Hyresavtal": "Lease Agreement",
        "Underhållsavtal": "Maintenance Agreement",
        "Ramavtal": "Framework Agreement",
        "Licensavtal": "License Agreement",
    },
}

COLUMN_LABELS = {
    "sv": {
        "Vendor": "Leverantör",
        "Contract Type": "Avtalstyp",
        "End Date": "Slutdatum",
        "Days Left": "Dagar kvar",
        "Urgency": "Brådska",
        "Contract Value (SEK)": "Kontraktsvärde (SEK)",
        "Owner": "Ansvarig",
    },
    "en": {
        "Vendor": "Vendor",
        "Contract Type": "Contract Type",
        "End Date": "End Date",
        "Days Left": "Days Left",
        "Urgency": "Urgency",
        "Contract Value (SEK)": "Contract Value (SEK)",
        "Owner": "Owner",
    },
}


def t(key, **kwargs):
    text = TRANSLATIONS[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text


def translate_contract_type(ctype):
    return CONTRACT_TYPE_TRANSLATIONS[st.session_state.lang].get(ctype, ctype)


def translate_urgency(urgency):
    return URGENCY_TRANSLATIONS[st.session_state.lang].get(urgency, urgency)


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


# Canonical (Swedish) urgency labels. All internal storage/filtering/sorting
# uses these values; display labels are translated via translate_urgency().
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

URGENCY_TRANSLATIONS = {
    "sv": {u: u for u in URGENCY_ORDER},
    "en": {
        "Utgånget": "Expired",
        "Brådskande (≤30 dagar)": "Urgent (≤30 days)",
        "Snart (31-60 dagar)": "Soon (31-60 days)",
        "Bevaka (61-90 dagar)": "Watch (61-90 days)",
        "OK (>90 dagar)": "OK (>90 days)",
    },
}


def style_urgency(val, color_map):
    color = color_map.get(val, "#ffffff")
    return f"background-color: {color}; color: white; font-weight: 600;"


# ----------------------------
# EMAIL DRAFT
# ----------------------------
def build_email_draft(row):
    days_left = row["Days Left"]
    vendor = row["Vendor"]
    ctype = translate_contract_type(row["Contract Type"])
    end_date = row["End Date"].strftime("%Y-%m-%d")
    owner = row["Owner"]

    if days_left < 0:
        status_line = t("email_status_expired", end_date=end_date)
    else:
        status_line = t("email_status_active", end_date=end_date, days_left=days_left)

    subject = t("email_subject", ctype=ctype, vendor=vendor)

    body = "\n".join([
        t("email_greeting", owner=owner),
        "",
        t("email_intro", vendor=vendor),
        "",
        t("email_contract_type_line", ctype=ctype),
        t("email_end_date_line", end_date=end_date),
        t("email_status_line", status=status_line),
        "",
        t("email_confirm_line"),
        f"- {t('email_option_renew')}",
        f"- {t('email_option_renegotiate')}",
        f"- {t('email_option_terminate')}",
        "",
        t("email_closing_line"),
        "",
        t("email_signature_greeting"),
        t("email_signature_role"),
    ])

    return subject, body


# ----------------------------
# LANGUAGE SELECTOR
# ----------------------------
LANG_OPTIONS = {"Svenska": "sv", "English": "en"}

if "lang" not in st.session_state:
    st.session_state.lang = "sv"

lang_labels = list(LANG_OPTIONS.keys())
current_index = list(LANG_OPTIONS.values()).index(st.session_state.lang)
chosen_label = st.selectbox("Språk / Language", lang_labels, index=current_index)
st.session_state.lang = LANG_OPTIONS[chosen_label]

# ----------------------------
# UI
# ----------------------------
st.title(t("app_title"))
st.caption(t("caption_intro"))

with st.expander(t("how_it_works_expander"), expanded=False):
    st.markdown(t("how_it_works_body"))

col_a, col_b = st.columns([2, 1])

with col_a:
    uploaded = st.file_uploader(t("upload_label"), type=["csv"])
with col_b:
    st.write("")
    st.write("")
    generate = st.button(t("generate_button"))

if "df" not in st.session_state:
    st.session_state.df = None

if generate:
    st.session_state.df = generate_mock_data()

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded, parse_dates=["Start Date", "End Date"])
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(t("csv_missing_cols", cols=", ".join(missing)))
        else:
            st.session_state.df = df
    except Exception as e:
        st.error(t("csv_read_error"))
        with st.expander(t("technical_detail")):
            st.write(e)

df = st.session_state.df

if df is None:
    st.info(t("no_data_info"))
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
m1.metric(t("metric_total"), len(df))
m2.metric(t("metric_urgent"), int((df["Days Left"].between(0, 30)).sum()))
m3.metric(t("metric_soon"), int((df["Days Left"].between(31, 90)).sum()))
m4.metric(t("metric_expired"), int((df["Days Left"] < 0).sum()))

st.markdown("---")

# ----------------------------
# FILTERS
# ----------------------------
f1, f2, f3 = st.columns(3)

with f1:
    vendor_filter = st.multiselect(t("filter_vendor"), sorted(df["Vendor"].unique()))
with f2:
    type_filter = st.multiselect(
        t("filter_type"),
        sorted(df["Contract Type"].unique()),
        format_func=translate_contract_type,
    )
with f3:
    urgency_filter = st.multiselect(
        t("filter_urgency"),
        URGENCY_ORDER,
        format_func=translate_urgency,
    )

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
st.subheader(t("table_subheader", n=len(filtered)))

display_df = filtered[["Vendor", "Contract Type", "End Date", "Days Left", "Urgency", "Contract Value (SEK)", "Owner"]].copy()
display_df["End Date"] = display_df["End Date"].dt.strftime("%Y-%m-%d")
display_df["Contract Type"] = display_df["Contract Type"].map(translate_contract_type)
display_df["Urgency"] = display_df["Urgency"].map(translate_urgency)
display_df = display_df.rename(columns=COLUMN_LABELS[st.session_state.lang])

urgency_column_label = COLUMN_LABELS[st.session_state.lang]["Urgency"]
urgency_color_map = {translate_urgency(k): v for k, v in URGENCY_COLOR.items()}

st.dataframe(
    display_df.style.map(lambda v: style_urgency(v, urgency_color_map), subset=[urgency_column_label]),
    use_container_width=True,
    hide_index=True,
)

# Download filtered data
csv_buffer = io.StringIO()
display_df.to_csv(csv_buffer, index=False)
st.download_button(t("download_filtered_csv"), csv_buffer.getvalue(), "contracts_filtered.csv", "text/csv")

st.markdown("---")

# ----------------------------
# EMAIL DRAFT GENERATOR
# ----------------------------
st.subheader(t("email_subheader"))

if len(filtered) == 0:
    st.warning(t("no_contracts_warning"))
else:
    options = [
        t(
            "option_template",
            vendor=row["Vendor"],
            ctype=translate_contract_type(row["Contract Type"]),
            date=row["End Date"].strftime("%Y-%m-%d"),
        )
        for _, row in filtered.iterrows()
    ]
    choice = st.selectbox(t("select_contract_label"), options)
    selected_idx = options.index(choice)
    selected_row = filtered.iloc[selected_idx]

    subject, body = build_email_draft(selected_row)

    contract_key = f"{selected_row['Vendor']}_{selected_row['End Date'].strftime('%Y-%m-%d')}_{st.session_state.lang}"
    edited_subject = st.text_input(t("subject_label"), value=subject, key=f"email_subject_{contract_key}")
    edited_body = st.text_area(t("body_label"), value=body, height=280, key=f"email_body_{contract_key}")

    st.caption(t("copy_caption"))

    mailto_url = f"mailto:?subject={quote(edited_subject)}&body={quote(edited_body)}"
    st.link_button(t("open_mail_button"), mailto_url)
    st.caption(t("mailto_caption"))
