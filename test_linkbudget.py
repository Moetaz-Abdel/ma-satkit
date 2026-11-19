"""Checks the Python engine against the cached values in LEO_Toolkit.xlsx (default inputs)."""
import math
from linkbudget import Inputs, leo_summary, geometry, fspl_db, spreading_db, latency_ms

EXPECTED = {  # Excel cached values, Main sheet
    "elevation_deg": 50.21918180239014, "central_angle_deg": 3.989404314008012,
    "slant_range_km": 758.7419551758904, "azimuth_deg": 190.47742816785978,
    "nadir_deg": 35.79141388360185, "earth_half_angle_deg": 66.06653484004894,
    "footprint_radius_km": 2664.2611545243058, "orbital_speed_kms": 7.557865206532812,
    "period_min": 96.68719643210862,
}
B = {"specific_atten_db_km": 2.759015072931091, "slant_rain_path_km": 3.838657803032715,
     "rain_fade_db": 10.590914738391808, "tsys_rain_k": 550.9983432818747,
     "cloud_loss_db": 0.32, "atmospheric_loss_db": 1.4, "scintillation_db": 0.4233372052425735,
     "rx_peak_gain_dbi": 42.93996344858519, "beamwidth_deg": 1.31159200375,
     "pointing_loss_db": -0.06975634637136156, "noise_clear_dbw": -120.0266750356873,
     "noise_density_dbw_hz": -203.82878745280337, "additional_noise_rain_db": -2.6402903831611155,
     "g_over_t_db": 18.168750901388563, "fspl_db": 176.0724819002839,
     "spreading_loss_db": 128.59398062722522, "rtt_ms": 5.061789208357064, "eirp_dbw": 48,
     "c_rx_dbw": -89.34561200331264, "pfd_dbw_m2": -80.59398062722522,
     "epfd_dbw_m2": -80.66373697359658, "cn_clear_db": 30.681063032374666,
     "cn_rain_db": 17.44985791082174, "cn0_clear_dbhz": 114.48317544949073,
     "cn0_rain_dbhz": 101.25197032793781, "ebn0_clear_db": 32.72226285893392,
     "ebn0_rain_db": 19.49105773738099, "margin_clear_db": 26.222262858933917,
     "margin_rain_db": 12.991057737380991}

def test_matches_workbook():
    s = leo_summary(Inputs())
    bad = []
    for k, v in EXPECTED.items():
        if not math.isclose(s["geometry"][k], v, rel_tol=1e-9): bad.append(k)
    for k, v in B.items():
        if not math.isclose(s["budget"][k], v, rel_tol=1e-9, abs_tol=1e-9): bad.append(k)
    assert not bad, bad
    assert math.isclose(s["doppler_khz"], 294.8781723848581, rel_tol=1e-9)
    assert s["status"] == "Elevation angle is in the accepted range"

if __name__ == "__main__":
    test_matches_workbook(); print("OK - matches workbook")
