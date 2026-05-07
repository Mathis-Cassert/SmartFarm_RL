import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pcse.models import Wofost81_WLP_CWB
from pcse.base import ParameterProvider
from pcse import signals


class PCSEEnv(gym.Env):
    def __init__(self, crop, weather, soil, site, agro, verbose: int=1):
        super(PCSEEnv, self).__init__()

        # Store the providers so we can recreate the engine on every reset
        self.crop_provider = crop
        self.weather_provider = weather
        self.soil_provider = soil
        self.site_provider = site
        self.agro_management = agro

        self.verbose = verbose

        self.engine = None
        # Define Action Space: Irrigation amount (0 to 5 cm)
        self.action_space = spaces.Box(low=0.0, high=5.0, shape=(1,), dtype=np.float32)

        # Define Observation Space:
        # [LAI, TAGP (Biomass), SM (Soil Moisture), IRRAD, TEMP, RELH, CO2]
        # We use TAGP as a proxy for 'visual height/size' as it's more stable in WOFOST
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, -10, 0, 300]),
            high=np.array([10, 20000, 1, 40, 50, 100, 1000]),
            dtype=np.float32
        )

        self._prev_tagp = None
        self._stagnant_days = 0

    #TODO: add environnmental changes
    def reset(self, seed=None, options=None):
        # Handle the random seed (required for Gymnasium)
        super().reset(seed=seed)

        # Reset tracking variables for early termination
        self._prev_tagp = None
        self._stagnant_days = 0

        # 1. Create a fresh ParameterProvider
        # This ensures any changes from the previous run are wiped clean
        params = ParameterProvider(
            cropdata=self.crop_provider,
            soildata=self.soil_provider,
            sitedata=self.site_provider
        )

        # 2. Re-initialize the WOFOST Engine
        # This sets the simulation back to the 'sowing date' defined in your agro file
        self.engine = Wofost81_WLP_CWB(params, self.weather_provider, self.agro_management)

        # 3. Get the initial observation
        observation = self._get_obs()

        # 4. Gymnasium reset must return (observation, info_dictionary)
        info = {}
        return observation, info

    #TODO: add some noise for more realism
    def _get_obs(self):
        """
        Extracts the current state from the PCSE engine and weather provider.
        """
        # Get crop state
        # LAI: Leaf Area Index
        # TAGP: Total Aboveground Production (proxy for growth/size)
        lai = self.engine.get_variable("LAI")
        tagp = self.engine.get_variable("TAGP")

        # Get soil state
        # SM: Volumetric Soil Moisture
        sm = self.engine.get_variable("SM")

        # Get current weather from the weather provider
        # We ask the engine for its current internal date
        current_date = self.engine.day
        weather_at_date = self.weather_provider(current_date)

        irrad = weather_at_date.IRRAD
        temp = weather_at_date.TEMP
        relh = weather_at_date.VAP #TODO: either use VAP or find a way to get RH

        # CO2 is usually a constant in the site parameters or a variable
        co2 = self.engine.get_variable("CO2")

        # Combine into a single numpy array for the RL model
        # We use 'nan_to_num' because at day 0, some variables might be None
        obs = np.array([lai, tagp, sm, irrad, temp, relh, co2], dtype=np.float32)
        return np.nan_to_num(obs)

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
        
        # Check for natural maturity
        # try:
        #     dvs = self.engine.get_variable("DVS")
        #     if dvs is not None and dvs >= 2.0:
        #         terminated = True
        #         if self.verbose >= 2 : print(f"DEBUG: Crop reached natural maturity (DVS={dvs:.2f})")
        # except:
        #     pass  # DVS variable might not be available
        
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

    # NOTE: If i implement crop rotation, I need to normalize thanks to max yield (potential production) models.Wofost81_PP
    #   reward += (final_yield / crop_max_yield) * 100 -> to get a % so everything is relative
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
            # Yield is represented by TWSO (Total Weight of Storage Organs / Grain)
            final_yield = self.engine.get_variable("TWSO")
            if final_yield is None: final_yield = 0

            # We give a massive reward for the final harvested yield
            # We might scale it (e.g., yield in kg/ha / 1000)
            reward += (final_yield / 100.0)
            if self.verbose >= 2: print(f"DEBUG: Final yield={final_yield:.2f}, Reward={reward:.2f}")

        return float(reward)