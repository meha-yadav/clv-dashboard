import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CLV & Churn Dashboard", page_icon="📊", layout="wide")

#load data

@st.cache_data
def load_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file, index_col=0)
    else:
        df = pd.read_excel(file, index_col=0)
    return df

st.title("📊 CLV & Churn Intelligence Dashboard")
uploaded = st.file_uploader("Upload your clv_churn_output file", type=['csv', 'xlsx'])

if uploaded is None:
    st.info("👆 Upload your Excel or CSV file to get started.")
    st.stop()

df = load_data(uploaded)
df.index = df.index.astype(str)

#required columns 

with st.expander("🔍 Click to see columns in your file"):
    st.write(list(df.columns))

df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
st.sidebar.write("Detected columns:", list(df.columns))

#detecting columns 

def find(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

action_col  = find(df, ['action_plan', 'action', 'segment'])
clv_col     = find(df, ['predicted_clv', 'clv', 'predicted_clv_6mo'])
churn_col   = find(df, ['churn_risk_score', 'churn_risk', 'churn'])
freq_col    = find(df, ['frequency', 'freq'])
monetary_col= find(df, ['monetary_value', 'monetary', 'avg_monetary_value'])
recency_col = find(df, ['recency'])
t_col       = find(df, ['t', 'customer_age'])

st.sidebar.markdown("**Column mapping:**")
st.sidebar.write({
    'action': action_col, 'clv': clv_col, 'churn': churn_col,
    'frequency': freq_col, 'monetary': monetary_col
})

#sidebar filters

st.sidebar.header("Filters")

filtered = df.copy()

if action_col:
    action_filter = st.sidebar.multiselect(
        "Action Plan",
        options=df[action_col].unique().tolist(),
        default=df[action_col].unique().tolist()
    )
    filtered = filtered[filtered[action_col].isin(action_filter)]

if churn_col:
    churn_range = st.sidebar.slider(
        "Churn Risk Score",
        min_value=0.0, max_value=100.0,
        value=(0.0, 100.0), step=1.0
    )
    filtered = filtered[
        (filtered[churn_col] >= churn_range[0]) &
        (filtered[churn_col] <= churn_range[1])
    ]

if clv_col:
    clv_range = st.sidebar.slider(
        "Predicted CLV (£)",
        min_value=float(df[clv_col].min()),
        max_value=float(df[clv_col].max()),
        value=(float(df[clv_col].min()), float(df[clv_col].max()))
    )
    filtered = filtered[
        (filtered[clv_col] >= clv_range[0]) &
        (filtered[clv_col] <= clv_range[1])
    ]

st.sidebar.markdown(f"**Showing {len(filtered):,} of {len(df):,} customers**")

color_map = {
    'CRITICAL: High Value at Risk': '#E24B4A',
    'At Risk: Send Discount':       '#EF9F27',
    'Loyal: Standard':              '#1D9E75'
}

#tabs
tab1, tab2 = st.tabs(["📈 Overview", "🔍 Customer Drill Down"])

#1

with tab1:

    # KPI Cards
    cols = st.columns(4)
    cols[0].metric("Total Customers", f"{len(filtered):,}")

    if clv_col:
        cols[1].metric("Avg CLV (6mo)", f"£{filtered[clv_col].mean():.2f}")
    if churn_col:
        cols[2].metric("Avg Churn Risk", f"{filtered[churn_col].mean():.1f}%")
    if action_col:
        critical = filtered[action_col].str.contains('CRITICAL', na=False).sum()
        cols[3].metric("Critical Customers", f"{critical:,}",
                       delta=f"{critical/len(filtered)*100:.1f}% of total",
                       delta_color="inverse")

    st.divider()

    # Action Plan donut
    if action_col:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Action Plan Distribution")
            ac = filtered[action_col].value_counts().reset_index()
            ac.columns = ['Action Plan', 'Count']
            fig1 = px.pie(ac, names='Action Plan', values='Count',
                          color='Action Plan', color_discrete_map=color_map, hole=0.45)
            fig1.update_traces(textposition='outside', textinfo='percent+label')
            fig1.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        if churn_col:
            with col2:
                st.subheader("Churn Risk Distribution")
                fig2 = px.histogram(filtered, x=churn_col, nbins=30,
                                    color_discrete_sequence=['#378ADD'],
                                    labels={churn_col: 'Churn Risk Score'})
                fig2.update_layout(margin=dict(t=20, b=20), bargap=0.1)
                st.plotly_chart(fig2, use_container_width=True)

    # Scatter: CLV vs Churn
    if clv_col and churn_col:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("CLV vs Churn Risk")
            fig3 = px.scatter(
                filtered, x=churn_col, y=clv_col,
                color=action_col if action_col else None,
                color_discrete_map=color_map, opacity=0.6,
                labels={churn_col: 'Churn Risk Score', clv_col: 'Predicted CLV (£)'}
            )
            st.plotly_chart(fig3, use_container_width=True)

        if action_col:
            with col4:
                st.subheader("CLV by Action Plan")
                fig4 = px.box(filtered, x=action_col, y=clv_col,
                              color=action_col, color_discrete_map=color_map,
                              labels={clv_col: 'Predicted CLV (£)', action_col: 'Action Plan'})
                fig4.update_layout(showlegend=False)
                st.plotly_chart(fig4, use_container_width=True)

    # Bubble: Frequency vs Monetary
    if freq_col and monetary_col and churn_col:
        st.subheader("Purchase Frequency vs Avg Order Value")
        fig5 = px.scatter(
            filtered, x=freq_col, y=monetary_col,
            color=churn_col, color_continuous_scale='RdYlGn_r',
            size=clv_col if clv_col else None, size_max=20, opacity=0.7,
            labels={freq_col: 'Frequency', monetary_col: 'Avg Monetary Value (£)',
                    churn_col: 'Churn Risk Score'}
        )
        st.plotly_chart(fig5, use_container_width=True)

    # Full table
    st.subheader(f"Full Customer Table ({len(filtered):,} customers)")
    st.dataframe(filtered, use_container_width=True, height=400)

    csv = filtered.to_csv().encode('utf-8')
    st.download_button("⬇️ Download Filtered Data as CSV",
                       data=csv, file_name='clv_filtered.csv', mime='text/csv')

#2
with tab2:
    st.subheader("Customer Drill Down")
    customer_id = st.text_input("Enter Customer ID", placeholder="e.g. 12345")

    if customer_id:
        if customer_id in df.index:
            row = df.loc[customer_id]

            action = row[action_col] if action_col else "N/A"
            risk   = row[churn_col]  if churn_col  else 0
            clv    = row[clv_col]    if clv_col    else 0

            color = '#E24B4A' if 'CRITICAL' in str(action) else \
                    ('#EF9F27' if 'Risk' in str(action) else '#1D9E75')

            st.markdown(f"""
            <div style="border:2px solid {color}; border-radius:12px;
                        padding:1.5rem; margin-bottom:1rem;">
                <h3 style="margin:0 0 0.5rem;">Customer {customer_id}</h3>
                <span style="background:{color}22; color:{color}; padding:4px 12px;
                      border-radius:6px; font-size:0.85rem; font-weight:600;">
                    {action}
                </span>
            </div>
            """, unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            if churn_col:  m1.metric("Churn Risk",       f"{risk:.1f}%")
            if clv_col:    m2.metric("Predicted CLV",    f"£{clv:.2f}")
            if freq_col:   m3.metric("Frequency",        int(row[freq_col]))
            if monetary_col: m4.metric("Avg Order Value",f"£{row[monetary_col]:.2f}")

            if recency_col and t_col:
                m5, m6 = st.columns(2)
                m5.metric("Recency (days)",      int(row[recency_col]))
                m6.metric("Customer Age (days)", int(row[t_col]))

            # Gauge
            if churn_col:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=risk,
                    title={'text': "Churn Risk Score"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0,  25], 'color': '#EAF3DE'},
                            {'range': [25, 50], 'color': '#FAEEDA'},
                            {'range': [50, 80], 'color': '#FAECE7'},
                            {'range': [80,100], 'color': '#FCEBEB'},
                        ],
                        'threshold': {'line': {'color': '#E24B4A', 'width': 3},
                                      'thickness': 0.75, 'value': 80}
                    }
                ))
                fig_gauge.update_layout(height=300, margin=dict(t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            # Percentile charts
            col_a, col_b = st.columns(2)
            if clv_col:
                with col_a:
                    fig_c = px.histogram(df, x=clv_col, nbins=40,
                                         color_discrete_sequence=['#B5D4F4'],
                                         title="CLV Distribution")
                    fig_c.add_vline(x=clv, line_color='#E24B4A', line_width=2,
                                    annotation_text=f"Customer {customer_id}",
                                    annotation_position="top right")
                    st.plotly_chart(fig_c, use_container_width=True)

            if churn_col:
                with col_b:
                    fig_r = px.histogram(df, x=churn_col, nbins=40,
                                         color_discrete_sequence=['#B5D4F4'],
                                         title="Churn Risk Distribution")
                    fig_r.add_vline(x=risk, line_color='#E24B4A', line_width=2,
                                    annotation_text=f"Customer {customer_id}",
                                    annotation_position="top right")
                    st.plotly_chart(fig_r, use_container_width=True)

            if clv_col and churn_col:
                clv_pct  = (df[clv_col] < clv).mean() * 100
                risk_pct = (df[churn_col] < risk).mean() * 100
                st.info(f"""
                **Customer {customer_id} is in the:**
                - **{clv_pct:.0f}th percentile** for CLV
                - **{risk_pct:.0f}th percentile** for churn risk
                """)

        else:
            st.error(f"Customer ID `{customer_id}` not found.")
            st.markdown("**Sample IDs from your data:**")
            st.write(df.index[:10].tolist())
    else:
        st.markdown("Enter a Customer ID above to see their full profile.")