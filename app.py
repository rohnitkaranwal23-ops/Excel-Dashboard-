import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

header_base64 = get_base64_image("header.png.png")

# ─────────────────────────────────────────────
# CONFIGURATION & IMPORTS
# ─────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="DRDO HR Dashboard")


st.markdown("""
<style>

/* Chart containers spacing */
.block-container {
    padding-top: 1rem;
}

/* Titles tighter */
h2, h3 {
    margin-bottom: 5px;
}

/* Reduce white gaps */
[data-testid="column"] {
    padding: 5px;
}

</style>
""", unsafe_allow_html=True)

try:
    from streamlit_echarts import st_echarts
    ECHARTS_AVAILABLE = True
    echarts_import_error = None
except Exception as exc:
    ECHARTS_AVAILABLE = False
    st_echarts = None
    echarts_import_error = exc

# safer rerun helper
def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except Exception:
            st.stop()

# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────
authentication_status = False
name = None
username = None

try:
    import streamlit_authenticator as stauth
    AUTH_AVAILABLE = True
    names = ["Rohnit", "Admin"]
    usernames = ["rohnit", "admin"]
    passwords = ["pass123", "1234"]
    
    try:
        hashed_list = stauth.Hasher.hash_list(passwords)
    except Exception:
        hashed_list = [stauth.Hasher.hash(p) for p in passwords]

    credentials = {"usernames": {}}
    for uname, n, hpw in zip(usernames, names, hashed_list):
        credentials[uname.lower()] = {"name": n, "password": hpw}

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="my_cookie",
        cookie_key="signature_key",
    )

    try:
        name, authentication_status, username = authenticator.login('Login')
    except Exception:
        authenticator.login('Login')
        authentication_status = st.session_state.get('authentication_status')
        name = st.session_state.get('name')
        username = st.session_state.get('username')
except Exception:
    AUTH_AVAILABLE = False
    names = ["Rohnit", "Admin"]
    usernames = ["rohnit", "admin"]
    passwords = ["pass123", "1234"]

# Restore auth from session state if available
if not authentication_status and st.session_state.get('username'):
    authentication_status = True
    name = st.session_state.get('name')
    username = st.session_state.get('username')

# AUTH CHECK: if not authenticated, provide a fallback login form
if not authentication_status:
    st.warning("Please sign in")
    with st.form("fallback_login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        try:
            idx = usernames.index(u)
            if passwords[idx] == p:
                st.session_state['name'] = names[idx]
                st.session_state['username'] = u
                authentication_status = True
                safe_rerun()
            else:
                st.error("Invalid username or password")
        except ValueError:
            st.error("Invalid username or password")
    st.stop()

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "cluster_drilldown" not in st.session_state:
    st.session_state.cluster_drilldown = None

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_excel("drdo_100_employees_dataset excel 2.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR STYLE & CONTENT
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1925, #0f2a3f);
    padding-top: 20px;
}
[data-testid="stSidebar"] * {
    color: #e6edf3;
}
.sidebar-title {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 20px;
    margin-bottom: 10px;
    color: #9fb3c8;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    # Clock
    now = datetime.now()
    st.markdown(f"<div style='text-align:center; font-weight:bold;'>{now.strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)
    if st.button("Refresh Time", key="refresh_time", use_container_width=True):
        safe_rerun()
    st.markdown("---")

    #refresh button for dataset
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        safe_rerun()

    st.markdown("---")

    # Logo + Title
    st.markdown(f"""
    <div style="text-align:center;">
        <img src="data:image/png;base64,{header_base64}" width="80">
        <h3>DRDO Dashboard</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Filters
    st.markdown('<div class="sidebar-title">Filters</div>', unsafe_allow_html=True)
    
    cluster_sel = st.selectbox("Select Cluster", sorted(df["Cluster"].unique()))
    df_cluster = df[df["Cluster"] == cluster_sel]
    
    dept_sel = st.selectbox("Select Department", sorted(df_cluster["Department"].unique()))
    df_dept = df_cluster[df_cluster["Department"] == dept_sel]
    
    lab_sel = st.selectbox("Select Lab", sorted(df_dept["Lab_Name"].unique()))
    
    st.markdown("---")

    # System info
    st.markdown('<div class="sidebar-title">System Status</div>', unsafe_allow_html=True)
    st.success("🟢 Operational")
    st.info(f"Records: {len(df)}")

    # Dataset info
    with st.expander("Dataset Info"):
        st.write(f"Total employees: {len(df)}")
        st.write(f"Clusters: {df['Cluster'].nunique()}")
        st.write(f"Departments: {df['Department'].nunique()}")
        st.write(f"Labs: {df['Lab_Name'].nunique()}")

# ─────────────────────────────────────────────
# MAIN DISPLAY
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
.header-img {{
    width: 100%;
    border-radius: 12px;
    margin-bottom: 20px;
}}
</style>

<img class="header-img" src="data:image/png;base64,{header_base64}">
""", unsafe_allow_html=True)
st.title("DRDO Workforce Overview")

# Filtered data display
filtered_df = df[
    (df["Cluster"] == cluster_sel) &
    (df["Department"] == dept_sel) &
    (df["Lab_Name"] == lab_sel)
]
st.dataframe(filtered_df, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# CONSTANTS & CONFIGURATION FOR CHARTS
# ─────────────────────────────────────────────
EXCLUDE_CLUSTERS = set()
DIFFERENT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

# ─────────────────────────────────────────────
# DRILLDOWN CHARTS
# ─────────────────────────────────────────────
st.header("Cluster — Click to Drill Down")

if not ECHARTS_AVAILABLE:
    st.warning("streamlit-echarts not available. Using Altair fallback.")
    sel_cluster_chart = st.selectbox("Select cluster to explore", ["All"] + sorted([c for c in df["Cluster"].unique() if c not in EXCLUDE_CLUSTERS]))

    if sel_cluster_chart == "All":
        counts = df.groupby("Cluster").size().reset_index(name="count")
        cluster_palette = {name: DIFFERENT_COLORS[i % len(DIFFERENT_COLORS)] for i, name in enumerate(counts["Cluster"]) }
        counts["color"] = counts["Cluster"].map(cluster_palette)
        chart = alt.Chart(counts).mark_bar().encode(
            x=alt.X("Cluster:N"),
            y=alt.Y("count:Q"),
            tooltip=["Cluster", "count"],
            color=alt.Color("color:N", scale=None, legend=None),
        ).properties(title="Clusters — Employee Counts")
        st.altair_chart(chart, use_container_width=True)
    else:
        dept_counts = df[df["Cluster"] == sel_cluster_chart].groupby("Department").size().reset_index(name="count")
        dept_palette = {name: DIFFERENT_COLORS[i % len(DIFFERENT_COLORS)] for i, name in enumerate(dept_counts["Department"]) }
        dept_counts["color"] = dept_counts["Department"].map(dept_palette)
        chart = alt.Chart(dept_counts).mark_bar().encode(
            x=alt.X("Department:N"),
            y=alt.Y("count:Q"),
            tooltip=["Department", "count"],
            color=alt.Color("color:N", scale=None, legend=None),
        ).properties(title=f"{sel_cluster_chart} — Departments")
        st.altair_chart(chart, use_container_width=True)
else:
    group = st.session_state.cluster_drilldown
    drilldown_data = {}
    cluster_counts = []
    
    for i, (clus, g) in enumerate(df.groupby("Cluster")):
        if clus in EXCLUDE_CLUSTERS: continue
        dept_items = []
        for j, (dept, cnt) in enumerate(g.groupby("Department").size().items()):
            color = DIFFERENT_COLORS[(i + j) % len(DIFFERENT_COLORS)]
            dept_items.append({"name": dept, "value": int(cnt), "itemStyle": {"color": color}})
        drilldown_data[clus] = dept_items
        cluster_color = DIFFERENT_COLORS[i % len(DIFFERENT_COLORS)]
        cluster_counts.append({"name": clus, "value": int(len(g)), "groupId": clus, "itemStyle": {"color": cluster_color}})

    if group is None:
        options = {
            "title": {"text": "Clusters — Employee Counts"},
            "xAxis": {"data": [c["name"] for c in cluster_counts]},
            "yAxis": {},
            "series": {"type": "bar", "data": cluster_counts},
        }
    else:
        sub = drilldown_data.get(group, [])
        options = {
            "title": {"text": f"{group} — Departments"},
            "xAxis": {"data": [item["name"] for item in sub]},
            "yAxis": {},
            "series": {"type": "bar", "data": sub},
        }

    events = {"click": "function(params) { return (params.data && params.data.groupId) ? params.data.groupId : params.name }"}

    if group is not None:
        if st.button("Back"):
            st.session_state.cluster_drilldown = None
            safe_rerun()

    result = st_echarts(options=options, events=events, height="420px", key="cluster_drilldown_chart")

    if result:
        
        evt = result if isinstance(result, str) else getattr(result, "chart_event", None)
        if group is None and evt in drilldown_data:
            st.session_state.cluster_drilldown = evt
            safe_rerun()
        elif group is not None:
            dept_names = [item["name"] for item in drilldown_data.get(group, [])]
            if evt in dept_names:
                df_emps = df[(df["Cluster"] == group) & (df["Department"] == evt)]
                st.subheader(f"Employees — {group} / {evt}")
                st.dataframe(df_emps, use_container_width=True)
                
                # MORE CHARTS INFORMATIONAL 
                df = filtered_df.copy()

st.markdown("## 📊 Quick Insights")

# 4 equal columns
col1, col2, col3, col4 = st.columns(4)

# ---------- BAR CHART ----------
with col1:
    st.markdown("**Department Count**")
    bar = alt.Chart(df).mark_bar(color="#4CAF50").encode(
        x=alt.X('count():Q', title=''),
        y=alt.Y('Department:N', sort='-x', title=''),
        tooltip=['Department', 'count()']
    ).properties(height=250)
    st.altair_chart(bar, use_container_width=True)

# ---------- LINE CHART ----------
with col2:
    st.markdown("**Employees by Cluster**")
    cluster_df = df['Cluster'].value_counts().reset_index()
    cluster_df.columns = ['Cluster', 'Count']

    line = alt.Chart(cluster_df).mark_line(point=True, color="#2196F3").encode(
        x='Cluster:N',
        y='Count:Q',
        tooltip=['Cluster', 'Count']
    ).properties(height=250)

    st.altair_chart(line, use_container_width=True)

# ---------- PIE CHART ----------
with col3:
    st.markdown("**Role Distribution**")
    role_df = df['Role'].value_counts().reset_index()
    role_df.columns = ['Role', 'Count']

    pie = alt.Chart(role_df).mark_arc().encode(
        theta='Count:Q',
        color='Role:N',
        tooltip=['Role', 'Count']
    ).properties(height=250)

    st.altair_chart(pie, use_container_width=True)

# ---------- HISTOGRAM ----------
with col4:
    st.markdown("**Age Distribution**")

    hist = alt.Chart(df).mark_bar(color="#FF9800").encode(
        x=alt.X('Age:Q', bin=True),
        y='count()',
        tooltip=['count()']
    ).properties(height=250)

    st.altair_chart(hist, use_container_width=True)

    st.markdown("##                              📈 Deep Insights")

col5, col6, col7, col8 = st.columns(4)

# ---------- 1. TOP LABS ----------
with col5:
    st.markdown("**Top Labs (Headcount)**")
    top_labs = df['Lab_Name'].value_counts().head(5).reset_index()
    top_labs.columns = ['Lab', 'Count']

    chart = alt.Chart(top_labs).mark_bar(color="#673AB7").encode(
        x='Count:Q',
        y=alt.Y('Lab:N', sort='-x'),
        tooltip=['Lab', 'Count']
    ).properties(height=250)

    st.altair_chart(chart, use_container_width=True)

# ---------- 2. GENDER DISTRIBUTION ----------
with col6:
    st.markdown("**Gender Distribution**")

    gender_df = df['Gender'].value_counts().reset_index()
    gender_df.columns = ['Gender', 'Count']

    chart = alt.Chart(gender_df).mark_arc(innerRadius=50).encode(
        theta='Count:Q',
        color='Gender:N',
        tooltip=['Gender', 'Count']
    ).properties(height=250)

    st.altair_chart(chart, use_container_width=True)

# ---------- 3. EXPERIENCE HISTOGRAM ----------
with col7:
    st.markdown("**Experience Distribution**")

    chart = alt.Chart(df).mark_bar(color="#009688").encode(
        x=alt.X('Experience:Q', bin=True, title="Years"),
        y='count()',
        tooltip=['count()']
    ).properties(height=250)

    st.altair_chart(chart, use_container_width=True)

# ---------- 4. CLUSTER vs ROLE ----------
with col8:
    st.markdown("**Roles by Cluster**")

    chart = alt.Chart(df).mark_bar().encode(
        x='Cluster:N',
        y='count()',
        color='Role:N',
        tooltip=['Cluster', 'Role', 'count()']
    ).properties(height=250)

    st.altair_chart(chart, use_container_width=True)