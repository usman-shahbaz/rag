"""
All drink, size, milk, syrup, sweetener, and topping options are defined here
as the single source of truth for what the agent can offer.
"""

from drinks import Drink, Size, Milk, Syrup, Sweetener, Topping

DRINKS: list[Drink] = [
    Drink(
        name="Espresso",
        description="Strong concentrated coffee shot.",
        support_milk=False,
        support_sweeteners=True,
        support_syrup=True,
        support_topping=False,
        support_size=False,
    ),
    Drink(
        name="Latte",
        description="Espresso with steamed milk, smooth and creamy.",
        support_milk=True,
        support_sweeteners=True,
        support_syrup=True,
        support_topping=True,
        support_size=True,
    ),
    Drink(
        name="Cappuccino",
        description="Espresso with steamed milk and a deep layer of foam.",
        support_milk=True,
        support_sweeteners=True,
        support_syrup=True,
        support_topping=True,
        support_size=True,
    ),
    Drink(
        name="Cold Brew",
        description="Smooth, cold-steeped coffee served over ice.",
        support_milk=True,
        support_sweeteners=True,
        support_syrup=True,
        support_topping=False,
        support_size=True,
    ),
    Drink(
        name="Frappuccino",
        description="Blended iced coffee drink with flavors and toppings.",
        support_milk=True,
        support_sweeteners=True,
        support_syrup=True,
        support_topping=True,
        support_size=True,
    ),
]

SIZES: list[Size] = [
    Size(name="Tall", description="12 fl oz (small)"),
    Size(name="Grande", description="16 fl oz (medium)"),
    Size(name="Venti", description="20 fl oz (large for hot, 24 fl oz for cold)"),
    Size(name="Trenta", description="31 fl oz (cold drinks only)"),
]

MILKS: list[Milk] = [
    Milk(name="Whole Milk", description="Rich, full-bodied dairy milk."),
    Milk(name="2% Milk", description="Reduced fat milk option."),
    Milk(name="Nonfat Milk", description="Fat-free dairy milk."),
    Milk(name="Oat Milk", description="Smooth, plant-based oat milk."),
    Milk(name="Soy Milk", description="Plant-based soy milk."),
    Milk(name="Almond Milk", description="Nutty, plant-based almond milk."),
    Milk(name="Coconut Milk", description="Creamy, tropical plant-based milk."),
]

SYRUPS: list[Syrup] = [
    Syrup(name="Vanilla Syrup", description="Classic sweet vanilla flavor."),
    Syrup(name="Caramel Syrup", description="Rich caramel sweetness."),
    Syrup(name="Hazelnut Syrup", description="Nutty, sweet hazelnut flavor."),
    Syrup(name="Mocha Syrup", description="Chocolate syrup for coffee drinks."),
    Syrup(name="Pumpkin Spice Syrup", description="Seasonal pumpkin spice flavor."),
]

SWEETENERS: list[Sweetener] = [
    Sweetener(name="Classic Syrup", description="Standard liquid sweetener."),
    Sweetener(name="Raw Sugar", description="Natural cane sugar."),
    Sweetener(name="Stevia", description="Zero-calorie natural sweetener."),
    Sweetener(name="Honey", description="Natural honey sweetener."),
    Sweetener(name="Splenda", description="Low-calorie artificial sweetener."),
]

TOPPINGS: list[Topping] = [
    Topping(name="Whipped Cream", description="Fluffy whipped topping."),
    Topping(name="Caramel Drizzle", description="Sweet caramel sauce topping."),
    Topping(name="Mocha Drizzle", description="Chocolate drizzle topping."),
    Topping(name="Cinnamon Powder", description="Warm spice powder."),
    Topping(name="Vanilla Bean Powder", description="Sweet vanilla topping."),
    Topping(name="Caramel Crunch", description="Crunchy caramelized sugar bits."),
]
