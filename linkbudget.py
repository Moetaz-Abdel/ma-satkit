"""LEO satellite link budget engine.

Faithful Python port of the 'Main' sheet of LEO_Toolkit.xlsx. Every formula keeps the
same structure as the workbook so results match its cached values. The optional
path reduction factor is off by default (the workbook does not apply it).
"""
from __future__ import annotations
import math
from dataclasses import dataclass

MU = 398600.4418          # km^3/s^2, Earth gravitational parameter (workbook value)
C_LIGHT = 299792458.0     # m/s
C_KMS = 299792.458        # km/s
K_DB = -228.6             # Boltzmann constant, dBW/K/Hz


@dataclass
class Inputs:
    # Ground station
    gs_lat: float = 60.33
    gs_lon: float = -1.69
    gs_height_m: float = 50.0
    earth_radius_km: float = 6378.137
    freq_ghz: float = 20.0
    # Satellite geometry
    sat_lat: float = 56.4
    sat_lon: float = -3.0
    sat_alt_km: float = 600.0
    # Rain
    rain_height_km: float = 3.0
    rain_rate_mmh: float = 25.0
    rain_k: float = 0.075
    rain_alpha: float = 1.12
    rain_medium_temp_k: float = 275.0
    apply_path_reduction: bool = False   # workbook does NOT apply it
    # Cloud / atmosphere (workbook rules, exposed as parameters)
    cloud_lwc: float = 2.0
    cloud_coeff: float = 0.08            # dB per (g/m3) per km
    cloud_path_km: float = 2.0
    oxygen_db_per_ghz: float = 0.05
    vapour_db_per_ghz: float = 0.02
    scint_coeff: float = 3.0             # scintillation = coeff / sqrt(elevation_deg)
    # Link budget
    ebn0_required_db: float = 6.5
    tx_power_dbw: float = 10.0
    tx_gain_dbi: float = 38.0
    other_loss_db: float = 2.0
    bit_rate_mbps: float = 150.0
    # LEO receiver
    dish_m: float = 0.8
    efficiency: float = 0.7
    pointing_error_deg: float = 0.1
    bandwidth_hz: float = 240e6
    tsys_k: float = 300.0


def _r(x): return math.radians(x)
def _d(x): return math.degrees(x)
def _db(x): return 10.0 * math.log10(x)


def geometry(i: Inputs, sat_lat=None, sat_lon=None) -> dict:
    sat_lat = i.sat_lat if sat_lat is None else sat_lat
    sat_lon = i.sat_lon if sat_lon is None else sat_lon
    Re, h = i.earth_radius_km, i.sat_alt_km
    orbit_r = Re + h
    speed = math.sqrt(MU / orbit_r)
    period_min = 2 * math.pi * math.sqrt(orbit_r ** 3 / MU) / 60
    cosv = (math.sin(_r(i.gs_lat)) * math.sin(_r(sat_lat))
            + math.cos(_r(i.gs_lat)) * math.cos(_r(sat_lat)) * math.cos(_r(sat_lon - i.gs_lon)))
    psi = _d(math.acos(max(-1.0, min(1.0, cosv))))
    # Excel ATAN2(x, y) == math.atan2(y, x)
    el = _d(math.atan2(math.cos(_r(psi)) - Re / orbit_r, math.sin(_r(psi))))
    nadir = 90 - el - psi
    half = _d(math.asin(Re / orbit_r))
    dlon = sat_lon - i.gs_lon
    az = _d(math.atan2(math.sin(_r(dlon)),
                       math.cos(_r(i.gs_lat)) * math.tan(_r(sat_lat))
                       - math.sin(_r(i.gs_lat)) * math.cos(_r(dlon)))) % 360
    footprint = Re * math.acos(Re / orbit_r)
    slant = math.sqrt(Re ** 2 + orbit_r ** 2 - 2 * Re * orbit_r * math.cos(_r(psi)))
    return dict(orbit_radius_km=orbit_r, orbital_speed_kms=speed, period_min=period_min,
                central_angle_deg=psi, elevation_deg=el, nadir_deg=nadir,
                earth_half_angle_deg=half, azimuth_deg=az, footprint_radius_km=footprint,
                slant_range_km=slant)


def fspl_db(d_km, f_ghz): return 32.45 + 20 * math.log10(d_km) + 20 * math.log10(f_ghz * 1000)
def spreading_db(d_km): return _db(4 * math.pi * (d_km * 1000) ** 2)
def latency_ms(d_km): return d_km / 299792 * 1000 * 2


def rx_antenna(f_ghz, dish, eta, perr):
    gain = _db(eta * (math.pi * dish * f_ghz * 1e9 / C_LIGHT) ** 2)
    bw = 70 * (C_LIGHT / (f_ghz * 1e9)) / dish
    ploss = -12 * (perr / bw) ** 2     # negative number (workbook convention)
    return gain, bw, ploss


def rain_path_reduction(i: Inputs, el_deg: float, gamma: float) -> float:
    """ITU-R P.618 horizontal reduction factor r0.01 (used only if apply_path_reduction)."""
    hs = i.gs_height_m / 1000
    ls = (i.rain_height_km - hs) / math.sin(_r(el_deg))
    lg = ls * math.cos(_r(el_deg))
    return 1 / (1 + 0.78 * math.sqrt(lg * gamma / i.freq_ghz) - 0.38 * (1 - math.exp(-2 * lg)))


def atmosphere(i: Inputs, el_deg: float) -> dict:
    cloud = i.cloud_coeff * i.cloud_lwc * i.cloud_path_km
    oxy = i.oxygen_db_per_ghz * i.freq_ghz
    wv = i.vapour_db_per_ghz * i.freq_ghz
    return dict(cloud_loss_db=cloud, oxygen_loss_db=oxy, water_vapour_loss_db=wv,
                atmospheric_loss_db=oxy + wv,
                scintillation_db=i.scint_coeff / math.sqrt(el_deg))


def rain(i: Inputs, el_deg: float, tsys_clear: float) -> dict:
    gamma = i.rain_k * i.rain_rate_mmh ** i.rain_alpha
    path = (i.rain_height_km - i.gs_height_m / 1000) / math.sin(_r(el_deg))
    r = rain_path_reduction(i, el_deg, gamma) if i.apply_path_reduction else 1.0
    a001 = gamma * path * r
    tsys_rain = tsys_clear + i.rain_medium_temp_k * (1 - 10 ** (-a001 / 10))
    return dict(specific_atten_db_km=gamma, slant_rain_path_km=path, path_reduction_factor=r,
                rain_fade_db=a001, tsys_rain_k=tsys_rain)


def link_budget(i: Inputs, el_deg: float, slant_km: float, *, dish, eta, perr, bw_hz, tsys) -> dict:
    """Downlink budget for one receiver at a given elevation / range. Mirrors Main!F21:F41."""
    f = i.freq_ghz
    atm = atmosphere(i, el_deg)
    rn = rain(i, el_deg, tsys)
    gain, beamwidth, ploss = rx_antenna(f, dish, eta, perr)
    n_clear = K_DB + _db(tsys * bw_hz)
    n0 = K_DB + _db(tsys)
    add_noise_rain = n_clear - (K_DB + _db(rn["tsys_rain_k"] * bw_hz))      # C46 (negative)
    fs = fspl_db(slant_km, f)
    eirp = i.tx_power_dbw + i.tx_gain_dbi
    c_dbw = (eirp - i.other_loss_db - fs - atm["cloud_loss_db"] - atm["atmospheric_loss_db"]
             - atm["scintillation_db"] + gain + ploss)                      # F31
    spread = spreading_db(slant_km)
    pfd = eirp - spread
    epfd = pfd + ploss
    cn_clear = c_dbw - n_clear
    cn_rain = cn_clear - rn["rain_fade_db"] + add_noise_rain
    cn0_clear = c_dbw - n0
    cn0_rain = cn0_clear - rn["rain_fade_db"] + add_noise_rain
    ebn0_clear = cn0_clear - _db(i.bit_rate_mbps * 1e6)
    ebn0_rain = ebn0_clear - rn["rain_fade_db"] + add_noise_rain
    return dict(
        fspl_db=fs, spreading_loss_db=spread, rtt_ms=latency_ms(slant_km),
        eirp_dbw=eirp, rx_peak_gain_dbi=gain, beamwidth_deg=beamwidth, pointing_loss_db=ploss,
        noise_clear_dbw=n_clear, noise_density_dbw_hz=n0, additional_noise_rain_db=add_noise_rain,
        g_over_t_db=gain - _db(tsys), c_rx_dbw=c_dbw, pfd_dbw_m2=pfd, epfd_dbw_m2=epfd,
        cn_clear_db=cn_clear, cn_rain_db=cn_rain, cn0_clear_dbhz=cn0_clear, cn0_rain_dbhz=cn0_rain,
        ebn0_clear_db=ebn0_clear, ebn0_rain_db=ebn0_rain,
        margin_clear_db=ebn0_clear - i.ebn0_required_db, margin_rain_db=ebn0_rain - i.ebn0_required_db,
        **atm, **rn)


def doppler_khz(i: Inputs, el_deg: float) -> float:
    Re, h = i.earth_radius_km, i.sat_alt_km
    return (math.sqrt(MU / (Re + h)) / C_KMS) * (Re / (Re + h)) * math.cos(_r(el_deg)) \
        * (i.freq_ghz * 1e9) / 1000


def elevation_status(el: float) -> str:
    if el < 25: return "EDGE OF COVERAGE due to low Elevation Angle"
    if el < 40: return "FAIR Elevation Angle"
    return "Elevation angle is in the accepted range"


def slant_from_elevation(i: Inputs, el_deg: float) -> float:
    """Slant range for a given elevation (spherical Earth), used by the sweep."""
    Re, rs = i.earth_radius_km, i.earth_radius_km + i.sat_alt_km
    s = Re * math.sin(_r(el_deg))
    return -s + math.sqrt(s * s + rs * rs - Re * Re)


def leo_summary(i: Inputs) -> dict:
    g = geometry(i)
    el, d = g["elevation_deg"], g["slant_range_km"]
    lb = link_budget(i, el, d, dish=i.dish_m, eta=i.efficiency, perr=i.pointing_error_deg,
                     bw_hz=i.bandwidth_hz, tsys=i.tsys_k)
    return dict(geometry=g, budget=lb, doppler_khz=doppler_khz(i, el),
                status=elevation_status(el))


def elevation_sweep(i: Inputs, elevations=None):
    elevations = elevations or [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90]
    rows = []
    for el in elevations:
        d = slant_from_elevation(i, el)
        lb = link_budget(i, el, d, dish=i.dish_m, eta=i.efficiency, perr=i.pointing_error_deg,
                         bw_hz=i.bandwidth_hz, tsys=i.tsys_k)
        rows.append(dict(elevation_deg=el, slant_range_km=d, fspl_db=lb["fspl_db"],
                         rain_fade_db=lb["rain_fade_db"], ebn0_clear_db=lb["ebn0_clear_db"],
                         ebn0_rain_db=lb["ebn0_rain_db"], margin_clear_db=lb["margin_clear_db"],
                         margin_rain_db=lb["margin_rain_db"]))
    return rows
