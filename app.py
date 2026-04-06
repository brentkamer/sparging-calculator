import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ── Model constants ────────────────────────────────────────────────────────────
K_REF   = 4.8046e-5   # decay constant calibrated from batch data
T_REF_F = 99.73       # reference temperature (Batch 1)
DH      = 33_830      # benzene Henry's Law enthalpy (J/mol)
R_GAS   = 8.314
C0         = 1.4         # starting benzene (mg/L)
C_LIM      = 0.5         # regulatory limit (mg/L)
BUFFER_SCF = 2_000       # standard safety buffer added to model result

BATCHES = [
    ('Batch 1', 99.73,  21_430 + BUFFER_SCF, '#4da6ff'),
    ('Batch 2', 101.76, 22_358 + BUFFER_SCF, '#ffaa44'),
    ('Batch 3', 105.68, 25_280 + BUFFER_SCF, '#44cc88'),
]

def F_to_K(f):
    return (f - 32.0) * 5.0 / 9.0 + 273.15

def calc_scfm(temp_f):
    T_K = F_to_K(temp_f)
    T_r = F_to_K(T_REF_F)
    k   = K_REF * np.exp(DH / R_GAS * (1.0 / T_r - 1.0 / T_K))
    return np.log(C0 / C_LIM) / k

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='LA Sparging SCFM Calculator',
    page_icon='💨',
    layout='centered',
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title('💨 LA Sparging — SCFM Calculator')
st.caption(
    f'Starting benzene C\u2080 = **{C0} mg/L**  →  '
    f'Regulatory target = **{C_LIM} mg/L**  |  Henry\'s Law model  |  +2,000 SCF safety buffer'
)
st.divider()

# ── Input ──────────────────────────────────────────────────────────────────────
col_slider, col_num = st.columns([3, 1])

with col_slider:
    temp = st.slider(
        'Oil Temperature (F)',
        min_value=70.0, max_value=150.0,
        value=100.0, step=0.5,
        format='%.1f F',
    )

with col_num:
    temp_typed = st.number_input(
        'Or type:', min_value=70.0, max_value=150.0,
        value=float(temp), step=0.5, format='%.1f',
        label_visibility='visible',
    )

# Number input overrides slider if changed
active_temp = temp_typed if temp_typed != temp else temp
q_model     = calc_scfm(active_temp)
q           = q_model + BUFFER_SCF

st.divider()

# ── Result ─────────────────────────────────────────────────────────────────────
st.metric(
    label=f'Required Cumulative SCF at {active_temp:.1f} F  (incl. 2,000 SCF buffer)',
    value=f'{q:,.0f} SCF',
    help=f'Model: {q_model:,.0f} SCF + 2,000 SCF safety buffer = {q:,.0f} SCF total',
)

st.divider()

# ── Chart ──────────────────────────────────────────────────────────────────────
T_arr = np.linspace(70, 150, 400)
Q_arr = np.array([calc_scfm(t) + BUFFER_SCF for t in T_arr])

fig = go.Figure()

# Model curve
fig.add_trace(go.Scatter(
    x=T_arr, y=Q_arr,
    mode='lines',
    name='Model curve',
    line=dict(color='#4da6ff', width=2.5),
    hovertemplate='Temp: %{x:.1f} F<br>SCFM: %{y:,.0f} SCF<extra></extra>',
))



# User's current selection
fig.add_trace(go.Scatter(
    x=[active_temp], y=[q],
    mode='markers',
    name=f'Your input ({active_temp:.1f} F)',
    marker=dict(color='#ff4444', size=14, symbol='circle',
                line=dict(color='white', width=1.5)),
    hovertemplate=f'Your temp: {active_temp:.1f} F<br>Required: {q:,.0f} SCF<extra></extra>',
))

fig.add_vline(
    x=active_temp,
    line_dash='dash', line_color='#ff4444', opacity=0.45,
    annotation_text=f'{active_temp:.1f} F',
    annotation_font_color='#ff4444',
    annotation_position='top',
)

fig.update_layout(
    xaxis_title='Oil Temp (F)',
    yaxis_title='Required Cumulative SCFM',
    plot_bgcolor='#1a2535',
    paper_bgcolor='#1a2535',
    font=dict(color='#aabbcc', size=11),
    xaxis=dict(gridcolor='#2e3f55', zerolinecolor='#2e3f55'),
    yaxis=dict(gridcolor='#2e3f55', zerolinecolor='#2e3f55',
               tickformat=',.0f'),
    legend=dict(bgcolor='#263347', bordercolor='#445566', borderwidth=1,
                font=dict(size=10)),
    height=400,
    margin=dict(t=30, b=50, l=70, r=20),
    hovermode='x unified',
)

st.plotly_chart(fig, use_container_width=True)

# ── Reference table ────────────────────────────────────────────────────────────
st.divider()
st.caption('**Batch reference points** (from fitted model, C\u2080 = 1.4 mg/L, incl. 2,000 SCF buffer):')
cols = st.columns(3)
for i, (name, t_b, q_b, color) in enumerate(BATCHES):
    with cols[i]:
        st.metric(label=f'{name} — {t_b} F', value=f'{q_b:,} SCF')
