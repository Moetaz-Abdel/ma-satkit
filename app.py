import streamlit as st
import math

# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="Satellite Engineering Tool",
    page_icon="🛰️",
    layout="wide"
)

# ==========================================
# TITLE
# ==========================================

st.title("🛰️ Satellite Engineering Tool")
st.markdown("LEO / GEO Satellite Performance Calculator")

# ==========================================
# SIDEBAR INPUTS
# ==========================================

st.sidebar.header("Ground Station")

gs_lat = st.sidebar.number_input(
    "Latitude (°)",
    value=60.33
)

gs_lon = st.sidebar.number_input(
    "Longitude (°)",
    value=-1.69
)

gs_height = st.sidebar.number_input(
    "Height (m)",
    value=50.0
)

# ==========================================
# LEO INPUTS
# ==========================================

st.sidebar.header("LEO Satellite")

leo_lat = st.sidebar.number_input(
    "LEO Latitude (°)",
    value=62.0
)

leo_lon = st.sidebar.number_input(
    "LEO Longitude (°)",
    value=-3.0
)

leo_alt = st.sidebar.number_input(
    "LEO Altitude (km)",
    value=550.0
)

# ==========================================
# GEO INPUTS
# ==========================================

st.sidebar.header("GEO Satellite")

geo_lon = st.sidebar.number_input(
    "GEO Longitude (°)",
    value=12.0
)

geo_alt = st.sidebar.number_input(
    "GEO Altitude (km)",
    value=35786.0
)

# ==========================================
# RF INPUTS
# ==========================================

st.sidebar.header("RF Parameters")

frequency = st.sidebar.number_input(
    "Frequency (GHz)",
    value=12.0
)

tx_power = st.sidebar.number_input(
    "Tx Power (dBW)",
    value=10.0
)

tx_gain = st.sidebar.number_input(
    "Tx Gain (dBi)",
    value=38.0
)

# ==========================================
# CALCULATIONS
# ==========================================

speed_of_light = 299792.458

eirp = tx_power + tx_gain

wavelength_mm = (
    299792458 /
    (frequency * 1e9)
) * 1000

leo_rtt = (
    leo_alt /
    speed_of_light
) * 1000 * 2

geo_rtt = (
    geo_alt /
    speed_of_light
) * 1000 * 2

leo_fspl = (
    32.45
    + 20 * math.log10(leo_alt)
    + 20 * math.log10(frequency * 1000)
)

geo_fspl = (
    32.45
    + 20 * math.log10(geo_alt)
    + 20 * math.log10(frequency * 1000)
)

# ==========================================
# KPI CARDS
# ==========================================

st.header("Key Results")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Wavelength",
        f"{wavelength_mm:.2f} mm"
    )

with col2:
    st.metric(
        "EIRP",
        f"{eirp:.2f} dBW"
    )

with col3:
    st.metric(
        "LEO RTT",
        f"{leo_rtt:.2f} ms"
    )

with col4:
    st.metric(
        "GEO RTT",
        f"{geo_rtt:.2f} ms"
    )

# ==========================================
# LEO / GEO RESULTS
# ==========================================

st.divider()

col1, col2 = st.columns(2)

with col1:

    st.subheader("LEO Results")

    st.write(
        f"Altitude: **{leo_alt:.0f} km**"
    )

    st.write(
        f"FSPL: **{leo_fspl:.2f} dB**"
    )

    st.write(
        f"RTT Delay: **{leo_rtt:.2f} ms**"
    )

with col2:

    st.subheader("GEO Results")

    st.write(
        f"Altitude: **{geo_alt:.0f} km**"
    )

    st.write(
        f"FSPL: **{geo_fspl:.2f} dB**"
    )

    st.write(
        f"RTT Delay: **{geo_rtt:.2f} ms**"
    )

# ==========================================
# INPUT SUMMARY
# ==========================================

st.divider()

st.subheader("Input Summary")

st.json(
    {
        "Ground Latitude": gs_lat,
        "Ground Longitude": gs_lon,
        "Ground Height": gs_height,
        "LEO Latitude": leo_lat,
        "LEO Longitude": leo_lon,
        "LEO Altitude": leo_alt,
        "GEO Longitude": geo_lon,
        "GEO Altitude": geo_alt,
        "Frequency": frequency,
        "TX Power": tx_power,
        "TX Gain": tx_gain,
    }
)