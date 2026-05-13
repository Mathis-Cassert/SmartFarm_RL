import gymnasium as gym
import pandas as pd
from gymnasium import spaces
import numpy as np

from pcse.models import Wofost81_WLP_CWB, Wofost81_PP
from pcse.base import ParameterProvider
from pcse import signals

from utils.observation_process import apply_noise, normalize_observation
from configs.observation_noise_config import FeatureNoiseConfig, NoiseConfig
from configs.gym_obs_act import ObservationFeature, OBSERVATION_BOUNDS, ActionFeature, ACTION_BOUNDS


class PCSEEnv(gym.Env):
    def __init__(self, config, verbose: int=1):
        super(PCSEEnv, self).__init__()

        self.config = config

        # Store the providers so we can recreate the engine on every reset
        crop, weather, soil, site, agro = config.create_providers()
        self.crop_provider = crop
        self.weather_provider = weather
        self.soil_provider = soil
        self.site_provider = site
        self.agro_management = agro

        self.verbose = verbose

        # Add reset counter for environmental variation
        self.reset_counter = 0

        self.noise_config = NoiseConfig(
            enabled=True,
            feature_configs={
                ObservationFeature.LAI: FeatureNoiseConfig(noise_type="gaussian", std=0.05),
                ObservationFeature.TAGP: FeatureNoiseConfig(noise_type="uniform", std=50.0),
                ObservationFeature.SM: FeatureNoiseConfig(noise_type="gaussian", std=0.02),
                ObservationFeature.IRRAD: FeatureNoiseConfig(noise_type="gaussian", std=1.0),
                ObservationFeature.TEMP: FeatureNoiseConfig(noise_type="gaussian", std=0.5),
                ObservationFeature.VAP: FeatureNoiseConfig(noise_type="uniform", std=2.0),
                ObservationFeature.CO2: FeatureNoiseConfig(noise_type="none", std=0.0),
            }
        )

        #Engine for the RL model to learn and eval engine for the reward calculation/visualization
        self.engine = None
        self.eval_engine = None

        self.eval_summary = None
        self.eval_output = None

        # Define Action Space: Irrigation amount (0 to 5 cm)
        self.action_space = spaces.Box(low=np.array([ACTION_BOUNDS[f][0] for f in ActionFeature]),
                                       high=np.array([ACTION_BOUNDS[f][1] for f in ActionFeature]),
                                       shape=(1,), dtype=np.float32)

        # Define Observation Space (normalized to [0, 1])
        self.observation_space = spaces.Box(
            low=np.zeros(len(ObservationFeature), dtype=np.float64),
            high=np.ones(len(ObservationFeature), dtype=np.float64),
            dtype=np.float64
        )

        self._prev_tagp = None
        self._stagnant_days = 0

    def update_providers(self, crop, weather, soil, site, agro):
        self.crop_provider = crop
        self.weather_provider = weather
        self.soil_provider = soil
        self.site_provider = site
        self.agro_management = agro

    #TODO: add environnmental changes
    def reset(self, seed=None, options=None):
        # Handle the random seed (required for Gymnasium)
        super().reset(seed=seed)

        # Increment reset counter for environmental variation
        self.reset_counter += 1

        # Reset tracking variables for early termination
        self._prev_tagp = None
        self._stagnant_days = 0

        self.update_providers(*self.config.randomize_all())

        # 1. Create a fresh ParameterProvider
        # This ensures any changes from the previous run are wiped clean
        params = ParameterProvider(
            cropdata=self.crop_provider,
            soildata=self.soil_provider,
            sitedata=self.site_provider
        )

        # 2. Re-initialize the WOFOST Engine and eval engine
        # This sets the simulation back to the 'sowing date' defined in your agro file
        self.engine = Wofost81_WLP_CWB(params, self.weather_provider, self.agro_management)
        self.eval_engine = Wofost81_PP(params, self.weather_provider, self.agro_management)

        # 3. Get the initial observation
        observation = self._get_obs()

        # 4. Gymnasium reset must return (observation, info_dictionary)
        info = {}
        return observation, info

    def _get_obs(self):
        """
        Extracts the current state from the PCSE engine and weather provider.
        """
        # Get crop state
        lai = self.engine.get_variable("LAI")   # LAI: Leaf Area Index
        tagp = self.engine.get_variable("TAGP") # TAGP: Total Aboveground Production (proxy for growth/size)

        # Get soil state
        sm = self.engine.get_variable("SM") # SM: Volumetric Soil Moisture

        # Get current weather from the weather provider
        # We ask the engine for its current internal date
        current_date = self.engine.day
        weather_at_date = self.weather_provider(current_date)

        irrad = weather_at_date.IRRAD
        temp = weather_at_date.TEMP
        vap = weather_at_date.VAP #TODO: either use VAP or find a way to get RH

        # Get CO2 from site provider (it is a constant)
        co2 = self.site_provider["CO2"]

        # Build observation dict (order-independent)
        obs_dict = {
            ObservationFeature.LAI: float(np.nan_to_num(lai)),
            ObservationFeature.TAGP: float(np.nan_to_num(tagp)),
            ObservationFeature.SM: float(np.nan_to_num(sm)),
            ObservationFeature.IRRAD: float(np.nan_to_num(irrad)),
            ObservationFeature.TEMP: float(np.nan_to_num(temp)),
            ObservationFeature.VAP: float(np.nan_to_num(vap)),
            ObservationFeature.CO2: float(np.nan_to_num(co2)),
        }

        # Apply noise and convert to array
        noisy_obs = apply_noise(obs_dict, self.noise_config, OBSERVATION_BOUNDS, reset_count=self.reset_counter)
        # Pre-normalize for stability
        normalized_obs = normalize_observation(noisy_obs, OBSERVATION_BOUNDS)
        return normalized_obs

    def step(self, action):
        # 1. Translate the Action
        # Action is a [1] array with a value between 0 and 5.0 (cm of water)
        irrigation_amount = float(action[0])

        # 2. Inject Irrigation into the Engine
        # WOFOST 8.1 tracks irrigation via signals, not direct variable setting.
        # This bypasses the need for an irrigation schedule in the YAML file.
        self.engine._send_signal(signal=signals.irrigate, amount=irrigation_amount, efficiency=1.0)

        # 3. Advance the Simulation by 1 Day
        self.engine.run(days=1)

        # 4. Get the New State
        new_obs = self._get_obs()
        
        # DEBUG: Log crop state
        lai = self.engine.get_variable("LAI")
        lai_val = lai if lai is not None else 0.0

        tagp = self.engine.get_variable("TAGP")
        tagp_val = tagp if tagp is not None else 0.0

        # 5. Check for natural crop termination conditions
        terminated = False
        truncated = False
        
        # Check if engine says to terminate (calendar end)
        if self.engine.flag_terminate:
            terminated = True
            if self.verbose >= 2 : print("DEBUG: Calendar end reached")
        
        # Check for crop death (LAI = 0 and not recovering)
        if lai_val <= 0.0 and tagp_val > 0:  # Biomass exists but no leaves
            terminated = True
            if self.verbose >= 2 : print("DEBUG: Crop died (LAI=0 with existing biomass)")
        
        # Check if biomass is stagnant (no growth for many days)
        if hasattr(self, '_prev_tagp') and self._prev_tagp is not None:
            if abs(tagp_val - self._prev_tagp) < 1.0:  # Very little growth
                if hasattr(self, '_stagnant_days'):
                    self._stagnant_days += 1
                else:
                    self._stagnant_days = 1

                if self._stagnant_days > 7:  # week of no growth
                    terminated = True
                    if self.verbose >= 2 : print("DEBUG: Crop growth stalled for 14+ days")
            else:
                self._stagnant_days = 0
        
        self._prev_tagp = tagp_val

        # 6. CALCULATE REWARD
        # This is where we define 'Maximize Yield, Save Water'
        reward = self._calculate_reward(irrigation_amount, terminated)

        return new_obs, reward, terminated, truncated, {}

    def _calculate_reward(self, water_applied, is_done):
        """
        Custom reward function:
        - Small penalty for every cm of water used (to encourage saving)
        - Big bonus at the end for final Yield (TAGP or TWSO)
        """
        # Penalty for using water (e.g., -0.1 per cm)
        # This prevents the agent from just flooding the field daily.
        reward = -(water_applied * 0.1)

        if is_done:
            # get the maximal yield production
            pp = self._potential_production()

            # Yield is represented by TWSO (Total Weight of Storage Organs / Grain)
            final_yield = self.engine.get_variable("TWSO")
            if final_yield is None: final_yield = 0

            # We give a massive reward (0-100) for the final harvested yield (may need to be scaled)
            pp_reward = (final_yield / pp) * 100
            reward += pp_reward

            if self.verbose >= 2: print(f"DEBUG: Final yield={final_yield:.2f}, Reward={reward:.2f}")

        return float(reward)

    def _potential_production(self) -> float:
        # Get the potential production from the engine
        self.eval_engine.run_till_terminate()
        self.eval_summary = self.eval_engine.get_summary_output()
        self.eval_output = self.eval_engine.get_output()
        potential_production = self.eval_summary[0].get('TWSO', 0)
        return potential_production

    def get_eval_outputs(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns the output and summary dataframes from the potential production (evaluation) engine.
        """
        eval_output_df = pd.DataFrame(self.eval_output).set_index("day")
        eval_summary_df = pd.DataFrame(self.eval_summary)
        return eval_output_df, eval_summary_df
