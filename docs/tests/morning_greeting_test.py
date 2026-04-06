# How to inherit from a class in python?
import random
from datatypes import Day_slices
from common_service import Common_Service

class morning_greeting:
    # init with 
    def __init__(self):
        pass

    def translate(self, language, word, learning_factor):
        # logic to translate word
        to_translate = random.random() < learning_factor
        if to_translate:
            return "translated_word"
        return word

    def generate_likely_ending(self):
        day_slice = Common_Service.time_of_day_slice()

        match day_slice:
            case Day_slices.MORNING:
                return "have a productive day!"
            case Day_slices.AFTERNOON:
                return "hope your afternoon is going well!"
            case Day_slices.EVENING:
                return "have a relaxing evening!"

    def generate_greeting(self):
        weather = Common_Service.get_weather()
        intro_word = "Good morning"
        learning_factor = 0.1
        used_intro_word = self.translate("jp", intro_word, learning_factor)

        greeting = f"{used_intro_word}, the weather is {weather}. {self.generate_likely_ending()}"
        print(greeting)
        return greeting

# TODO:
# class morning_greeting_test:
#     def __init__(self, name):
#         self.questions = [] # somehow declare this later java lateinitvar equivalent
#         self.name = name
#
#     # helper methods
#     def some_functionality(self):
#         return
#
#     def add_questions(self, questions):
#         self.questions.append(questions)

# This test is for the morning greeting. We should import the morning greeting class,
# and then test our model's output against it!
expected_answers = ["おはようございますビショップ さん, it's 10:04 in the morning. There's a cold breeze expected today,  lows around 58 degrees fahrenheit or 19 celsius. Today you have a few meetings, and tomorrow don't forget you have a 4pm apartment showing so prep for that. Can I suggest something for breakfast sir?"]

# Fixed line 70: Create an instance first, then call the method
if __name__ == "__main__":
    greeting = morning_greeting()
    test = greeting.generate_greeting()
