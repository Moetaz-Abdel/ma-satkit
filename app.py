"""LEO Toolkit - Streamlit app (port of LEO_Toolkit.xlsx)."""
import pandas as pd
import streamlit as st
from linkbudget import Inputs, leo_summary, elevation_sweep

st.set_page_config(page_title="LEO Link Budget Toolkit", page_icon="🛰️", layout="wide")
st.title("🛰️ LEO Link Budget Toolkit")
st.caption("Python port of LEO_Toolkit.xlsx. Change inputs in the sidebar; every result recalculates.")

d = Inputs()


def num(label, value, step=None, fmt=None, minv=None, key=None):
    return st.number_input(label, value=float(value), step=step, format=fmt, min_value=minv, key=key)


with st.sidebar:
    st.header("Inputs")
    with st.expander("Ground station & frequency", expanded=True):
        gs_lat = num("Ground station latitude (°)", d.gs_lat, 0.01, "%.4f")
        gs_lon = num("Ground station longitude (°)", d.gs_lon, 0.01, "%.4f")
        gs_h = num("Ground station height (m)", d.gs_height_m, 1.0, "%.1f")
        re_km = num("Earth radius (km)", d.earth_radius_km, 0.001, "%.3f", 1.0)
        f_ghz = num("Frequency (GHz)", d.freq_ghz, 0.1, "%.3f", 0.1)
    with st.expander("Satellite geometry", expanded=True):
        s_lat = num("Satellite latitude (°)", d.sat_lat, 0.01, "%.4f")
        s_lon = num("Satellite longitude (°)", d.sat_lon, 0.01, "%.4f")
        s_alt = num("Satellite altitude (km)", d.sat_alt_km, 10.0, "%.1f", 1.0)
    with st.expander("Rain"):
        hr = num("Rain height hR (km)", d.rain_height_km, 0.1, "%.2f", 0.0)
        r001 = num("Rain rate R0.01 (mm/h)", d.rain_rate_mmh, 1.0, "%.1f", 0.0)
        rk = num("Rain coefficient k", d.rain_k, 0.001, "%.4f", 0.0)
        ra = num("Rain exponent α", d.rain_alpha, 0.01, "%.3f", 0.0)
        tm = num("Rain medium temperature (K)", d.rain_medium_temp_k, 1.0, "%.1f", 0.0)
        reduction = st.checkbox("Apply ITU-R P.618 path reduction factor",
                                value=d.apply_path_reduction,
                                help="Off = identical to the Excel workbook (conservative: assumes rain "
                                     "uniform along the whole slant path).")
    with st.expander("Cloud & atmosphere"):
        lwc = num("Cloud LWC (g/m³)", d.cloud_lwc, 0.1, "%.2f", 0.0)
        ccoef = num("Cloud coefficient (dB per g/m³ per km)", d.cloud_coeff, 0.01, "%.3f", 0.0)
        cpath = num("Cloud path (km)", d.cloud_path_km, 0.1, "%.2f", 0.0)
        oxy = num("Oxygen loss (dB per GHz)", d.oxygen_db_per_ghz, 0.005, "%.3f", 0.0)
        wv = num("Water vapour loss (dB per GHz)", d.vapour_db_per_ghz, 0.005, "%.3f", 0.0)
        scint = num("Scintillation coeff (dB·√deg)", d.scint_coeff, 0.1, "%.2f", 0.0)
    with st.expander("Link budget", expanded=True):
        req = num("Eb/N₀ required (dB)", d.ebn0_required_db, 0.1, "%.2f")
        ptx = num("Tx power (dBW)", d.tx_power_dbw, 0.5, "%.2f")
        gtx = num("Tx gain (dBi)", d.tx_gain_dbi, 0.5, "%.2f")
        oth = num("Other loss (dB)", d.other_loss_db, 0.1, "%.2f", 0.0)
        rb = num("Carrier bit rate Rb (Mbps)", d.bit_rate_mbps, 1.0, "%.2f", 0.001)
    with st.expander("LEO receiver"):
        dish = num("Dish diameter (m)", d.dish_m, 0.1, "%.2f", 0.05)
        eta = num("Aperture efficiency (0-1)", d.efficiency, 0.01, "%.2f", 0.01)
        perr = num("Antenna pointing error (°)", d.pointing_error_deg, 0.01, "%.3f", 0.0)
        bw = num("Receiver bandwidth (Hz)", d.bandwidth_hz, 1e6, "%.0f", 1.0)
        tsys = num("System noise temperature (K)", d.tsys_k, 5.0, "%.1f", 1.0)

inp = Inputs(gs_lat=gs_lat, gs_lon=gs_lon, gs_height_m=gs_h, earth_radius_km=re_km, freq_ghz=f_ghz,
             sat_lat=s_lat, sat_lon=s_lon, sat_alt_km=s_alt, rain_height_km=hr, rain_rate_mmh=r001,
             rain_k=rk, rain_alpha=ra, rain_medium_temp_k=tm, apply_path_reduction=reduction,
             cloud_lwc=lwc, cloud_coeff=ccoef, cloud_path_km=cpath, oxygen_db_per_ghz=oxy,
             vapour_db_per_ghz=wv, scint_coeff=scint, ebn0_required_db=req, tx_power_dbw=ptx,
             tx_gain_dbi=gtx, other_loss_db=oth, bit_rate_mbps=rb, dish_m=dish, efficiency=eta,
             pointing_error_deg=perr, bandwidth_hz=bw, tsys_k=tsys)

try:
    res = leo_summary(inp)
except (ValueError, ZeroDivisionError) as exc:
    st.error(f"Cannot compute: {exc}")
    st.stop()

g, b = res["geometry"], res["budget"]
if g["elevation_deg"] <= 0:
    st.error(f"The satellite is below the horizon (elevation {g['elevation_deg']:.1f}°). "
             "Move the satellite closer to the ground station.")
    st.stop()

st.subheader("Summary")
c = st.columns(5)
c[0].metric("Elevation", f"{g['elevation_deg']:.1f}°")
c[1].metric("Slant range", f"{g['slant_range_km']:,.0f} km")
c[2].metric("Eb/N₀ (rain)", f"{b['ebn0_rain_db']:.2f} dB")
c[3].metric("Margin (clear sky)", f"{b['margin_clear_db']:.2f} dB")
c[4].metric("Margin (rain)", f"{b['margin_rain_db']:.2f} dB")
msg = f"Margin in rain: {b['margin_rain_db']:.2f} dB vs required Eb/N₀ {req:.2f} dB."
(st.success if b["margin_rain_db"] > 3 else st.warning if b["margin_rain_db"] >= 0 else st.error)(msg)
elev_msg = res["status"]
(st.info if "accepted" in elev_msg else st.warning)(elev_msg)


def table(rows, fmt="{:,.3f}"):
    df = pd.DataFrame(rows, columns=["Parameter", "Value", "Unit"])
    df["Value"] = df["Value"].map(lambda v: fmt.format(v) if isinstance(v, (int, float)) else v)
    st.dataframe(df, hide_index=True, use_container_width=True)


t1, t2, t3, t4 = st.tabs(["Link budget", "Geometry", "Rain, cloud & atmosphere", "Elevation sweep"])
with t1:
    table([
        ("EIRP", b["eirp_dbw"], "dBW"), ("Free-space path loss", b["fspl_db"], "dB"),
        ("Spreading loss", b["spreading_loss_db"], "dB"), ("Other loss", inp.other_loss_db, "dB"),
        ("Rx peak gain", b["rx_peak_gain_dbi"], "dBi"), ("3 dB beamwidth", b["beamwidth_deg"], "°"),
        ("Pointing loss", b["pointing_loss_db"], "dB"), ("G/T", b["g_over_t_db"], "dB/K"),
        ("C (Rx power)", b["c_rx_dbw"], "dBW"), ("PFD", b["pfd_dbw_m2"], "dBW/m²"),
        ("EPFD", b["epfd_dbw_m2"], "dBW/m²"), ("Noise (clear sky)", b["noise_clear_dbw"], "dBW"),
        ("Noise density N₀", b["noise_density_dbw_hz"], "dBW/Hz"),
        ("Additional noise @rain", b["additional_noise_rain_db"], "dB"),
        ("C/N (clear sky)", b["cn_clear_db"], "dB"), ("C/N (rain)", b["cn_rain_db"], "dB"),
        ("C/N₀ (clear sky)", b["cn0_clear_dbhz"], "dB-Hz"), ("C/N₀ (rain)", b["cn0_rain_dbhz"], "dB-Hz"),
        ("Eb/N₀ (clear sky)", b["ebn0_clear_db"], "dB"), ("Eb/N₀ (rain)", b["ebn0_rain_db"], "dB"),
        ("Eb/N₀ required", inp.ebn0_required_db, "dB"),
        ("Eb/N₀ margin (clear sky)", b["margin_clear_db"], "dB"),
        ("Eb/N₀ margin (rain)", b["margin_rain_db"], "dB"),
    ], "{:,.2f}")
with t2:
    table([
        ("Orbit radius", g["orbit_radius_km"], "km"), ("Orbital speed", g["orbital_speed_kms"], "km/s"),
        ("Orbital period", g["period_min"], "min"), ("Central angle ψ", g["central_angle_deg"], "°"),
        ("Elevation ε", g["elevation_deg"], "°"), ("Nadir angle φ", g["nadir_deg"], "°"),
        ("Earth-disk half angle α", g["earth_half_angle_deg"], "°"), ("Azimuth", g["azimuth_deg"], "°"),
        ("Footprint radius", g["footprint_radius_km"], "km"), ("Slant range", g["slant_range_km"], "km"),
        ("RTT propagation delay", b["rtt_ms"], "ms"), ("Doppler shift", res["doppler_khz"], "kHz"),
        ("Wavelength", 299792458 / (inp.freq_ghz * 1e6), "mm"),
    ])
with t3:
    table([
        ("Specific rain attenuation γR", b["specific_atten_db_km"], "dB/km"),
        ("Slant rain path", b["slant_rain_path_km"], "km"),
        ("Path reduction factor applied", b["path_reduction_factor"], ""),
        ("Rain fade A0.01", b["rain_fade_db"], "dB"),
        ("System noise temperature @rain", b["tsys_rain_k"], "K"),
        ("Cloud loss", b["cloud_loss_db"], "dB"), ("Oxygen loss", b["oxygen_loss_db"], "dB"),
        ("Water vapour loss", b["water_vapour_loss_db"], "dB"),
        ("Atmospheric loss (oxygen + vapour)", b["atmospheric_loss_db"], "dB"),
        ("Scintillation fade", b["scintillation_db"], "dB"),
    ])
with t4:
    sweep = pd.DataFrame(elevation_sweep(inp))
    sweep.columns = ["Elevation (°)", "Slant range (km)", "FSPL (dB)", "Rain fade (dB)",
                     "Eb/N₀ clear (dB)", "Eb/N₀ rain (dB)", "Margin clear (dB)", "Margin rain (dB)"]
    st.line_chart(sweep.set_index("Elevation (°)")[["Margin clear (dB)", "Margin rain (dB)"]])
    st.dataframe(sweep.round(2), hide_index=True, use_container_width=True)
    st.download_button("Download sweep as CSV", sweep.to_csv(index=False), "elevation_sweep.csv",
                       "text/csv")
    st.caption("Sweep keeps the satellite altitude and all other inputs, varying only elevation.")

with st.expander("Notes & assumptions"):
    st.markdown("""
- Formulas are ported 1:1 from the workbook; at default inputs the results match its cached values.
- Rain fade is `γR × slant path` as in the workbook. Tick the P.618 option in the sidebar to add the
  path reduction factor.
- Cloud, oxygen, water-vapour and scintillation formulas are the workbook's simple rules (exposed as
  parameters). Replace with ITU-R P.840 / P.676 / P.618 values for a formal design.
- Eb/N₀ margin = Eb/N₀ available − Eb/N₀ required, evaluated for clear sky and rain.
""")
