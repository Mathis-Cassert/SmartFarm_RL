import pathlib
import random
import copy
import tempfile
from datetime import date, timedelta

import numpy as np
import yaml

from pcse.input import YAMLAgroManagementReader, YAMLCropDataProvider, NASAPowerWeatherDataProvider
from pcse.input import WOFOST81SiteDataProvider_Classic, DummySoilDataProvider
from configs.definition import ROOT_DIR

# Define the providers (crop, weather, soil, site, agro)
PCSEProviders = tuple[
    YAMLCropDataProvider,
    NASAPowerWeatherDataProvider,
    DummySoilDataProvider,
    WOFOST81SiteDataProvider_Classic,
    YAMLAgroManagementReader
]

AGRO_FILE_PATH: pathlib.Path = ROOT_DIR / "env_config/agro/RPPO_agro.yaml"
# TODO: add files for eval w/ specific values so the model can be evaluate precisely (e.g. 10~20 different env config)
AGRO_TRAIN_FILE_PATH: pathlib.Path = ROOT_DIR / "env_config/train/RPPO_agro.yaml"
SOIL_TRAIN_FILE_PATH: pathlib.Path = ROOT_DIR / "env_config/train/RPPO_soil.yaml"
SITE_TRAIN_FILE_PATH: pathlib.Path = ROOT_DIR / "env_config/train/RPPO_site.yaml"

# TODO: make multiple for different region of the world (less general more specialized)
TYPE_NAME: str = "rppo"

# TODO: research ranges and add soil archetype / check values
# Realistic Soil Ranges (covers Sand to Clay)
SOIL_RANGES_PARAMETER: dict[str, tuple[float, float]] = {
    "SMFCF": (0.100, 0.450),  # Field capacity (cm3/cm3)
    "SM0": (0.320, 0.580),    # Porosity/Saturation (cm3/cm3)
    "SMW": (0.020, 0.250),    # Wilting point (cm3/cm3)
    "CRAIRC": (0.050, 0.100), # Critical air content (cm3/cm3)
    "SOPE": (0.1, 500.0),     # Max percolation rate root zone (cm/day)
    "KSUB": (0.1, 500.0),     # Max percolation rate subsoil (cm/day)
    "RDMSOL": (40.0, 200.0),  # Maximum rootable depth (cm)
    "K0": (0.1, 500.0),       # Saturated hydraulic conductivity (cm/day)
}

# Scalable Soil Archetypes (Position 0.0=Sand, 0.5=Loam, 1.0=Clay)
# You can add as many intermediate points as you want here.
SOIL_ARCHETYPES = [
    (0.0, {"SMW": 0.04, "SMFCF": 0.11, "SM0": 0.38, "K0": 200.0, "CRAIRC": 0.09, "SOPE": 200.0}), # Sand
    (0.5, {"SMW": 0.12, "SMFCF": 0.32, "SM0": 0.45, "K0": 20.0,  "CRAIRC": 0.07, "SOPE": 20.0}),  # Loam
    (1.0, {"SMW": 0.25, "SMFCF": 0.44, "SM0": 0.52, "K0": 1.0,   "CRAIRC": 0.05, "SOPE": 2.0}),   # Clay
]

# Site Parameter Ranges based on WOFOST81SiteDataProvider_Classic defaults
SITE_RANGES_PARAMETER: dict[str, tuple[float, float]] = {
    "IFUNRN": (0, 1),           # Binary: 0 or 1
    "NOTINF": (0.0, 1.0),       # Fraction of rain not-infiltrating [0-1]
    "SSI": (0.0, 2.0),          # Initial surface storage [cm]
    "SSMAX": (0.0, 3.0),        # Maximum surface storage [cm]
    "WAV": (0.0, 100.0),        # Initial water availability [cm] (required)
    "SMLIM": (0.0, 1.0),        # Initial max moisture in topsoil [0-1]
    "CO2": (300.0, 1400.0),     # Atmospheric CO2 concentration [ppm] (required)
    "BG_N_SUPPLY": (0.0, 0.1),  # Background N supply [kg/ha/day]
    "NSOILBASE": (0.0, 100.0),  # Initial soil mineral N [kg/ha]
    "NSOILBASE_FR": (0.025, 100.0), # Fraction of NSOILBASE in topsoil [0-100]
    "NAVAILI": (0.0, 250.0),    # Initial N available in pool [kg/ha] (required)
}


# TODO: Create a base config class for futur implementation of both model 81 and 73
# FIXME: I have to use this in the file pcse_env.py in the reset function
class PCSEConfig:

    """Configuration class for PCSE providers with selective reinitialization."""
    def __init__(self, crop_type="W81", latitude=13.7563, longitude=100.5018):
        # public attributes for personalization
        self.crop_type = crop_type
        self.latitude = latitude
        self.longitude = longitude

        # Cached providers
        self._crop = None
        self._weather = None
        self._soil = None
        self._site = None
        self._agro = None

        # Track last used parameters for change detection
        self._last_crop_type = None
        self._last_soil_type = None
        self._last_latitude = None
        self._last_longitude = None

        #cache file data
        with open(AGRO_TRAIN_FILE_PATH, 'r') as f:
            self._original_agro_data = yaml.safe_load(f)


    def get_agro_params(self) -> PCSEProviders:
        return self._crop, self._weather, self._soil, self._site, self._agro

    def create_providers(self) -> PCSEProviders:
        """
        Creates providers with selective reinitialization based on parameter changes.

        :returns: an instance of PCSEProviders (crop, weather, soil, site, agro)
        :rtype: PCSEProviders
        """
        # Recreate crop only if crop_type changed
        if self._crop is None or self.crop_type != self._last_crop_type:
            crop_dir: pathlib.Path = ROOT_DIR / f"env_config/crop/{self.crop_type}"
            self._crop = YAMLCropDataProvider(fpath=crop_dir)
            self._last_crop_type = self.crop_type

        # Recreate weather only if location changed
        if self._weather is None or self.latitude != self._last_latitude or self.longitude != self._last_longitude:
            self._weather = NASAPowerWeatherDataProvider(latitude=self.latitude, longitude=self.longitude, ETmodel="PM")
            # TESTS: make it almost not rain so we see if the model learn to waterize
            for _, daily_data in self._weather.store.items():
                daily_data.RAIN = daily_data.RAIN * 0.1
            self._last_latitude = self.latitude
            self._last_longitude = self.longitude

        # Create a soil based on the file if the parameter does not exist
        if self._soil is None:
            with open(SOIL_TRAIN_FILE_PATH, 'r') as f:
                soil_params = yaml.safe_load(f)

            soil_type_params = soil_params['base'][TYPE_NAME]

            # Create custom soil data provider with autofill from ranges if values not in YAML
            self._soil = DummySoilDataProvider()
            for param, (min_val, max_val) in SOIL_RANGES_PARAMETER.items():
                # Default behavior for initial creation
                self._soil[param] = soil_type_params.get(param, random.uniform(min_val, max_val))
            
            # Ensure physical consistency even for YAML-loaded soil if possible
            if 'SMW' in self._soil and 'SMFCF' in self._soil:
                if self._soil['SMW'] >= self._soil['SMFCF']:
                    self._soil['SMFCF'] = self._soil['SMW'] + 0.05

        if self._site is None:
            with open(SITE_TRAIN_FILE_PATH, 'r') as f:
                site_params = yaml.safe_load(f)

            site_type_params = site_params['base'][TYPE_NAME]

            # Create site data provider with N parameters (Wofost81)
            self.create_site(site_type_params)

        # Create a new agro management reader
        if self._agro is None:
            self._agro = YAMLAgroManagementReader(AGRO_TRAIN_FILE_PATH)

        return self.get_agro_params()

    def randomize_agro_year(self, year_range=(1984, 2024)):
        """
        Randomizes the agromanagement year and optionally month.

        :param year_range: Tuple of (min_year, max_year) for random selection
        """
        year = random.randint(*year_range)
        self.set_agro_year(year)

    def set_agro_year(self, year: int, random_month: bool = True) -> None:
        """
        Sets the agromanagement to a specific year, optionally randomizing the month.

        :param year: The year to use
        :param random_month: If True, randomizes the sowing month
        """
        # Deep copy to avoid modifying cached original
        agro_data = copy.deepcopy(self._original_agro_data)

        for agro_item in agro_data['AgroManagement']:
            for date_key, calendar_data in list(agro_item.items()):
                crop_calendar = calendar_data['CropCalendar']
                # Parse original date
                original_date = date_key if isinstance(date_key, date) else date.fromisoformat(str(date_key))

                if random_month:
                    # Randomize month (1-12), keep day
                    month = random.randint(1, 12)
                    day = original_date.day
                    new_date = date(year, month, day)
                else:
                    # Keep original month/day
                    new_date = date(year, original_date.month, original_date.day)

                # Update the key and dates
                agro_item[new_date] = agro_item.pop(date_key)
                crop_calendar['crop_start_date'] = new_date

                # Update end date
                crop_calendar['crop_end_date'] = new_date + timedelta(days=365)

            # Write to temporary file and pass file path
            # TODO: See if there is no way to pass the agro data directly (inefficient I/O)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(agro_data, f)
                temp_file = f.name

        self._agro = YAMLAgroManagementReader(temp_file)

    def randomize_soil_params(self) -> None:
        """Randomize soil parameters with texture-based interpolation and physical consistency."""
        if self._soil is None:
            self._soil = DummySoilDataProvider()

        # Texture index and archetype data extraction
        texture_idx = random.random()
        x_archetypes = [arch[0] for arch in SOIL_ARCHETYPES] # Give the value of the texture index for the archetype
        param_names = SOIL_ARCHETYPES[0][1].keys() # Give the name of the parameter


        # Robust interpolation using NumPy for each parameter
        for p in param_names:
            y_values = [a[1][p] for a in SOIL_ARCHETYPES] # Give the value of the parameter for the archetype
            base_val = np.interp(texture_idx, x_archetypes, y_values)

            # Apply noise (+/- 10%) and clamp to valid ranges
            val = base_val * random.uniform(0.9, 1.1)
            min_r, max_r = SOIL_RANGES_PARAMETER.get(p, (0.0, 999.0))
            self._soil[p] = np.clip(val, min_r, max_r)

        # Enforce physical constraints: SMW < SMFCF < SM0
        if self._soil['SMW'] >= self._soil['SMFCF']:
            self._soil['SMFCF'] = self._soil['SMW'] + 0.02
        if self._soil['SMFCF'] >= self._soil['SM0']:
            self._soil['SM0'] = self._soil['SMFCF'] + 0.05

        # Handle non-texture parameters
        self._soil['RDMSOL'] = random.uniform(*SOIL_RANGES_PARAMETER['RDMSOL'])
        
        # Link Percolation to Conductivity: KSUB and SOPE follow K0
        # These are physically capped by the saturated conductivity K0
        self._soil['SOPE'] = self._soil['K0'] * random.uniform(0.8, 1.0)
        self._soil['KSUB'] = self._soil['SOPE'] * random.uniform(0.8, 1.0)


    def create_site(self, param):
        """
        Create a site provider from a dictionary of parameters.
        :param param: Dictionary of site parameters
        """
        # TODO: a name is not in param, use default values from 'RPPO_site.yaml'
        self._site = WOFOST81SiteDataProvider_Classic(
            WAV= param.get('WAV', 5),
            CO2= param.get('CO2', 410),
            NAVAILI= param.get('NAVAILI', 30),
            NSOILBASE= param.get('NSOILBASE'),
            NSOILBASE_FR= param.get('NSOILBASE_FR'),
            BG_N_SUPPLY= param.get('BG_N_SUPPLY'),
            SSMAX= param.get('SSMAX'),
            SSI= param.get('SSI'),
            NOTINF= param.get('NOTINF'),
            IFUNRN= param.get('IFUNRN'),
            SMLIM= param.get('SMLIM')
        )

    def randomize_site_params(self, soil=None) -> None:
        """
        Randomize site parameters within valid ranges.
        Links WAV, SMLIM, and SSI to soil properties or logic.
        """
        random_params = {}
        for param, (min_val, max_val) in SITE_RANGES_PARAMETER.items():
            if param == "IFUNRN":
                random_params[param] = random.randint(0, 1)
            elif param == "SMLIM" and soil is not None:
                # SMLIM should be near Field Capacity (SMFCF)
                s_min = soil['SMW']
                s_max = soil['SM0']
                random_params[param] = random.uniform(
                    max(s_min, soil['SMFCF'] - 0.05),
                    min(s_max, soil['SMFCF'] + 0.05)
                )
            elif param == "WAV" and soil is not None:
                # WAV = Fraction * Available Water Capacity * Depth
                awc = (soil['SMFCF'] - soil['SMW']) * soil['RDMSOL']
                random_params[param] = random.uniform(0.1, 1.0) * awc
            elif param == "SSI":
                # Initial storage must be <= Max storage (SSMAX), handled after the loop
                continue 
            else:
                random_params[param] = random.uniform(min_val, max_val)

        # Handle SSI linkage to SSMAX
        random_params['SSI'] = random.uniform(0.0, random_params['SSMAX'])

        # Update site provider
        self.create_site(random_params)


    def randomize_all(self) -> PCSEProviders:
        """
        Randomizes all configurable parameters.
        Call this from reset for full environmental variation.
        """
        self.randomize_agro_year()
        self.randomize_soil_params()
        self.randomize_site_params(soil=self._soil)

        return self.get_agro_params()
