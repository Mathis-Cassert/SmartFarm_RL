from enum import Enum

class ObservationFeature(Enum):
    """Named indices for observation features."""
    LAI = 0
    TAGP = 1
    SM = 2
    IRRAD = 3
    TEMP = 4
    VAP = 5
    CO2 = 6

OBSERVATION_BOUNDS = {
    ObservationFeature.LAI: (0, 10),        # standard value for agriculture (typically max ~= 7)
    ObservationFeature.TAGP: (0, 100000),   # TODO: Check max possible value
    ObservationFeature.SM: (0.0, 1.0),      # Based on %
    ObservationFeature.IRRAD: (0.0, 40e6),  # Based on pcse.base.weather.WeatherDataContainer ↓
    ObservationFeature.TEMP: (-50.0, 60.0),
    ObservationFeature.VAP: (0.06, 199.3),
    ObservationFeature.CO2: (300.0, 1400.0),# Based on WOFOST 8.1 range
}

class ActionFeature(Enum):
    """Named indices for action features."""
    IRRIGATION = 0

ACTION_BOUNDS = {
    ActionFeature.IRRIGATION: (0, 5), # Arbitrarily chosen
}