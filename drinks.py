
"""
Drink schemas using Pydantic — Python equivalent of the Zod schemas in drinks.ts.
Pydantic provides the same runtime validation + type safety that Zod provides in TypeScript.
"""

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional


class DrinkSchema(BaseModel):
    name: str
    description: str
    support_milk: bool
    support_sweeteners: bool
    support_syrup: bool
    support_topping: bool
    support_size: bool
    image: Optional[str] = None


class SweetenerSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None


class SyrupSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None


class ToppingSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None


class SizeSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None


class MilkSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None


# Type aliases for lists
Drink = DrinkSchema
Sweetener = SweetenerSchema
Syrup = SyrupSchema
Topping = ToppingSchema
Size = SizeSchema
Milk = MilkSchema
