import pathlib
import random
import copy
import tempfile
from datetime import date, timedelta

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


# TODO: Create a base config class for futur implementation of both model 81 and 73
# FIXME: I have to use this in the file pcse_env.py in the reset function
class PCSEConfig:

    """Configuration class for PCSE providers with selective reinitialization."""
    def __init__(self, crop_type="W81", agro_type="rice", soil_type="bangkok",
                 latitude=13.7563, longitude=100.5018):
        # public attributes for personalization
        self.crop_type = crop_type
        self.agro_type = agro_type
        self.soil_type = soil_type
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
        with open(AGRO_FILE_PATH, 'r') as f:
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
            for date, daily_data in self._weather.store.items():
                daily_data.RAIN = daily_data.RAIN * 0.1
            self._last_latitude = self.latitude
            self._last_longitude = self.longitude

        # Recreate soil/site only if soil_type changed
        if self._soil is None or self.soil_type != self._last_soil_type:
            soil_params_file: pathlib.Path = ROOT_DIR / f"env_config/soil/{self.soil_type}.yaml"
            with open(soil_params_file, 'r') as f:
                soil_params = yaml.safe_load(f)

            soil_type_params = soil_params['base'][self.soil_type]

            # Create custom soil data provider
            self._soil = DummySoilDataProvider()
            self._soil['SMFCF'] = soil_type_params['SMFCF']
            self._soil['SM0'] = soil_type_params['SM0']
            self._soil['SMW'] = soil_type_params['SMW']
            self._soil['RDMSOL'] = soil_type_params['RDMSOL']
            self._soil['CRAIRC'] = soil_type_params['CRAIRC']
            self._soil['SOPE'] = soil_type_params['SOPE']
            self._soil['KSUB'] = soil_type_params['KSUB']
            self._last_soil_type = self.soil_type

        if self._site is None or self.soil_type != self._last_soil_type:
            soil_params_file: pathlib.Path = ROOT_DIR / f"env_config/soil/{self.soil_type}.yaml"
            with open(soil_params_file, 'r') as f:
                soil_params = yaml.safe_load(f)

            soil_type_params = soil_params['base'][self.soil_type]

            # Create site data provider with N parameters (Wofost81)
            self._site = WOFOST81SiteDataProvider_Classic(
                WAV=soil_type_params['WAV'],
                CO2=soil_type_params['CO2'],
                NAVAILI=soil_type_params['NAVAILI'],
                NSOILBASE=soil_type_params['NSOILBASE'],
                NSOILBASE_FR=soil_type_params['NSOILBASE_FR'],
                BG_N_SUPPLY=soil_type_params['BG_N_SUPPLY'],
                SSMAX=soil_type_params['SSMAX'],
                SSI=soil_type_params['SSI'],
                NOTINF=soil_type_params['NOTINF'],
                IFUNRN=soil_type_params['IFUNRN']
            )

        # Recreate agro only if agro_type changed
        if self._agro is None:
            self._agro = YAMLAgroManagementReader(AGRO_FILE_PATH)
            self._last_agro_type = self.agro_type

        return self.get_agro_params()

    def randomize_agro_year(self, year_range=(1984, 2024)):
        """
        Randomizes the agromanagement year and optionally month.

        :param year_range: Tuple of (min_year, max_year) for random selection
        """
        year = random.randint(*year_range)
        self.set_agro_year(year)

    def set_agro_year(self, year: int, random_month: bool = True):
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

    def randomize_soil_params(self):
        """TODO: Randomize soil parameters within valid ranges"""
        pass

    def randomize_site_params(self):
        """TODO: Randomize site parameters within valid ranges"""
        pass


    def randomize_all(self) -> PCSEProviders:
        """
        Randomizes all configurable parameters.
        Call this from reset for full environmental variation.
        """
        self.randomize_agro_year()
        self.randomize_soil_params()
        self.randomize_site_params()

        return self.get_agro_params()