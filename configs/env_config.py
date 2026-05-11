import pathlib
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
        self._last_agro_type = None
        self._last_soil_type = None
        self._last_latitude = None
        self._last_longitude = None
    
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
        if self._agro is None or self.agro_type != self._last_agro_type:
            agro_file: pathlib.Path = ROOT_DIR / f"env_config/agro/{self.agro_type}_agro.yaml"
            self._agro = YAMLAgroManagementReader(agro_file)
            self._last_agro_type = self.agro_type
        
        return self._crop, self._weather, self._soil, self._site, self._agro
