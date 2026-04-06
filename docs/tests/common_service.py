import time
import datatypes



class Common_Service:

    @staticmethod
    def get_weather():
        return "someWeatherStringEnabledByApy"

    @staticmethod
    def time_of_day_slice():
        hour_of_the_day = time.localtime().tm_hour
        if 5 <= hour_of_the_day < 12:
            return datatypes.Day_slices.MORNING
        elif 12 <= hour_of_the_day < 17:
           return datatypes.Day_slices.AFTERNOON
        else:
           return datatypes.Day_slices.EVENING