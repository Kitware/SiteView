from types import SimpleNamespace

FIELD_GROUPS = [
    SimpleNamespace(
        key="surface",
        label="Surface Fields",
        icon="mdi-layers-outline",
        color="primary",
        state_name="field_surface",
    ),
    SimpleNamespace(
        key="volume",
        label="Atmospheric Fields",
        icon="mdi-cube-outline",
        color="secondary",
        state_name="field_midpoints",
    ),
]

FIELDS_METADATA = {
    "TS": {"dim": 2, "name": "TS", "units": "K", "description": "Surface temperature"},
    "PS": {"dim": 2, "name": "PS", "units": "Pa", "description": "Surface pressure"},
    "PSL": {
        "dim": 2,
        "name": "PSL",
        "units": "Pa",
        "description": "Sea level pressure",
    },
    "TREFHT": {
        "dim": 2,
        "name": "TREFHT",
        "units": "K",
        "description": "Reference height (2m) temperature",
    },
    "QREFHT": {
        "dim": 2,
        "name": "QREFHT",
        "units": "kg/kg",
        "description": "Reference height humidity",
    },
    "U10": {"dim": 2, "name": "U10", "units": "m/s", "description": "10m wind speed"},
    "PRECT": {
        "dim": 2,
        "name": "PRECT",
        "units": "m/s",
        "description": "Total precipitation rate",
    },
    "PRECC": {
        "dim": 2,
        "name": "PRECC",
        "units": "m/s",
        "description": "Convective precipitation rate",
    },
    "TMQ": {
        "dim": 2,
        "name": "TMQ",
        "units": "kg/m²",
        "description": "Total precipitable water",
    },
    "CLDTOT": {
        "dim": 2,
        "name": "CLDTOT",
        "units": "fraction",
        "description": "Total cloud fraction",
    },
    "FSNS": {
        "dim": 2,
        "name": "FSNS",
        "units": "W/m²",
        "description": "Net solar flux at surface",
    },
    "FLNS": {
        "dim": 2,
        "name": "FLNS",
        "units": "W/m²",
        "description": "Net longwave flux at surface",
    },
    "LHFLX": {
        "dim": 2,
        "name": "LHFLX",
        "units": "W/m²",
        "description": "Surface latent heat flux",
    },
    "SHFLX": {
        "dim": 2,
        "name": "SHFLX",
        "units": "W/m²",
        "description": "Surface sensible heat flux",
    },
    "TAUX": {
        "dim": 2,
        "name": "TAUX",
        "units": "N/m²",
        "description": "Zonal surface wind stress",
    },
    "TAUY": {
        "dim": 2,
        "name": "TAUY",
        "units": "N/m²",
        "description": "Meridional surface wind stress",
    },
    "T": {
        "dim": 3,
        "name": "T",
        "units": "K",
        "description": "Air temperature on model levels",
    },
    "U": {
        "dim": 3,
        "name": "U",
        "units": "m/s",
        "description": "Zonal wind on model levels",
    },
    "V": {
        "dim": 3,
        "name": "V",
        "units": "m/s",
        "description": "Meridional wind on model levels",
    },
    "Q": {
        "dim": 3,
        "name": "Q",
        "units": "kg/kg",
        "description": "Specific humidity on model levels",
    },
    "RELHUM": {
        "dim": 3,
        "name": "RELHUM",
        "units": "%",
        "description": "Relative humidity on model levels",
    },
    "CLOUD": {
        "dim": 3,
        "name": "CLOUD",
        "units": "fraction",
        "description": "Cloud fraction on model levels",
    },
    "CLDLIQ": {
        "dim": 3,
        "name": "CLDLIQ",
        "units": "kg/kg",
        "description": "Cloud liquid water mixing ratio",
    },
    "CLDICE": {
        "dim": 3,
        "name": "CLDICE",
        "units": "kg/kg",
        "description": "Cloud ice mixing ratio",
    },
    "OMEGA": {
        "dim": 3,
        "name": "OMEGA",
        "units": "Pa/s",
        "description": "Vertical pressure velocity",
    },
    "Z3": {"dim": 3, "name": "Z3", "units": "m", "description": "Geopotential height"},
}

SITES = [
    {
        "title": "Southern Great Plains (SGP)",
        "value": "SGP",
        "lat": 36.607,
        "lon": 97.488,
    },
    {
        "title": "North Slope of Alaska (NSA)",
        "value": "NSA",
        "lat": 71.323,
        "lon": 156.609,
    },
    {
        "title": "Eastern North Atlantic (ENA)",
        "value": "ENA",
        "lat": 39.091,
        "lon": 28.026,
    },
]

SITES_LAT_LON = {site["value"]: (site["lat"], site["lon"]) for site in SITES}


VUETIFY_CONFIG = {
    "theme": {
        "defaultTheme": "siteviewLight",
        "themes": {
            "siteviewLight": {
                "dark": False,
                "colors": {
                    "primary": "#1f6f8b",
                    "secondary": "#7d3c98",
                    "background": "#f4f7f9",
                },
            },
            "siteviewDark": {
                "dark": True,
                "colors": {
                    "primary": "#6fc3e0",
                    "secondary": "#c996e6",
                    "background": "#0f1a20",
                },
            },
        },
    },
}
