from typing import Tuple
from httpx import TimeoutException,AsyncClient
import re

class Color:
    @classmethod
    async def get_color_name(cls,color:Tuple[int,int,int]) -> str:
        """
        Returns the name of a color based on its RGB values or if the request times out, returns the hexadecimal representation of the color.

        Returns:
            str: The name of the color or the hexadecimal representation of the color.
        """
        if not all(0 <= c <= 255 for c in color):
            raise ValueError(f"{color} is not a valid RGB color")
        api_url = f"https://www.thecolorapi.com/id?rgb=({color[0]},{color[1]},{color[2]})&format=json"
        try:
            async with AsyncClient() as client:
                response = await client.get(api_url, timeout=5)
            if not response.is_success:
                return "Unknown"
            return response.json()["name"]["value"]
        except TimeoutException:
            return cls.to_hexstring(color)

    @classmethod
    def to_hexstring(cls, color:Tuple[int,int,int]) -> str:
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

    @classmethod
    def from_hexstring(cls,hex_string:str) -> Tuple[int,int,int]:
        if not re.match(r"^#[0-9a-fA-F]{6}$", hex_string):
            raise ValueError(f"{hex_string} is not a valid hexadecimal color")

        r = int(hex_string[1:3], 16)
        g = int(hex_string[3:5], 16)
        b = int(hex_string[5:7], 16)

        return r, g, b
