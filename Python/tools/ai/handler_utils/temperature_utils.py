def map_temperature_description(description: str, current_temp: float = 6500.0) -> float:
    desc_lower = description.lower().strip()
    # Note: Lower Kelvin = warmer (more red/orange), Higher Kelvin = cooler (more blue/white)
    if "very warm" in desc_lower or "extremely warm" in desc_lower:
        return 2700.0  # Very warm candle light
    elif "warm" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
        return max(1500.0, current_temp - 1000.0)  # Make warmer
    elif "warm" in desc_lower:
        return 3200.0  # Standard warm white
    elif "very cold" in desc_lower or "extremely cold" in desc_lower:
        return 10000.0  # Very cold blue
    elif "cold" in desc_lower and ("more" in desc_lower or "er" in desc_lower):
        return min(15000.0, current_temp + 1000.0)  # Make cooler  
    elif "cooler" in desc_lower or "more cool" in desc_lower:
        return min(15000.0, current_temp + 1000.0)  # Make cooler by +1000K
    elif "cold" in desc_lower or "cool" in desc_lower:
        return 8000.0  # Standard cool white
    elif "daylight" in desc_lower or "neutral" in desc_lower:
        return 6500.0  # Standard daylight
    elif "sunset" in desc_lower or "golden" in desc_lower:
        return 2200.0  # Sunset/golden hour
    elif "noon" in desc_lower or "bright" in desc_lower:
        return 5600.0  # Noon daylight
    else:
        raise ValueError(f"Could not interpret color description: '{description}'. Try 'warm', 'cold', 'warmer', 'cooler', 'daylight', 'sunset', etc.")