from enum import Enum


class Category(Enum):
    MEAT = '🥩 Meat'
    FISH = '🐟 Fish'
    CAT_FOOD = '🐈 Cat food'
    BEER = '🍺 Beer'

    @classmethod
    def get_all_values(cls):
        return [member.value for member in cls.__members__.values()]
