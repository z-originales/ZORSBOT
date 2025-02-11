from os import getenv
import requests


def get_required_env_vars() -> dict:
    """
    Checks if specific environment variables are set and returns their values.
    Raises an exception if any of the required environment variables are missing.

    Returns:
        dict: A dictionary of environment variable names and their values.
    """
    required_env_vars = [
        "DISCORD_TOKEN",
    ]

    env_vars_values = {}
    missing_vars = []

    for var in required_env_vars:
        value = getenv(var)
        if value is None:
            missing_vars.append(var)
        env_vars_values[var] = value
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return env_vars_values


def get_color_name(colorhex: str) -> str:
    """
    Returns the name of a color based on its RGB values.

    Args:
        colorhex: A string representing the hexadecimal value of a color you want to get the name of.

    Returns:
        str: The name of the color.
    """
    api_url = f"https://www.thecolorapi.com/id?hex={colorhex[1:]}&format=json"
    response_json = requests.get(api_url).json()
    return response_json["name"]["value"]
