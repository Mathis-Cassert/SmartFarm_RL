from configs.env_config import PCSEConfig
from environments.pcse_env import PCSEEnv

#TODO: add script for random config w/ ranges (use a config class/file)
def make_env(config: PCSEConfig = None, verbose: int = 1) -> PCSEEnv:
    """
    Creates a PCSE environment with optional configuration

    :param config: Optional PCSEConfig instance for custom crop/agro/soil/location
    :type config: PCSEConfig
    :param verbose: Optional integer for verbosity level, 0: no output, 1: basic output (default), 2: debug output
    :type verbose: int
    :returns: an instance of PCSEEnv
    :rtype: PCSEEnv
    """
    if config is None:
        # Use default configuration for backward compatibility
        config = PCSEConfig()
    
    crop, weather, soil, site, agro = config.create_providers()
    return PCSEEnv(crop, weather, soil, site, agro, verbose=verbose)