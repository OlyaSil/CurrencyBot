import telebot
import requests
import json
import pymorphy2
from config import TOKEN, ACCESS_KEY

class ConvertionException(Exception):
    pass

class CurrencyConverterBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.morph = pymorphy2.MorphAnalyzer()

        self.keys = {
            'евро': 'EUR',
            'доллар': 'USD',
            'рубль': 'RUB',
        }

        @self.bot.message_handler(commands=['start', 'help'])
        def help(message: telebot.types.Message):
            text = ('Чтобы узнать сумму конвертации по текущему курсу, введите команду в следующем формате: '
                    '\n<исходная валюта> <валюта конвертации> <сумма перевода>. '
                    '\nДля получения списка доступных валют для конвертации введите команду "/values". ')
            self.bot.reply_to(message, text)

        @self.bot.message_handler(commands=['values'])
        def values(message: telebot.types.Message):
            text = 'Доступные валюты для конвертации:'
            for key in self.keys:
                text = '\n'.join((text, key))
            self.bot.reply_to(message, text)

        @self.bot.message_handler(content_types=['text', ])
        def convert(message: telebot.types.Message):
            try:
                input_values = message.text.split(' ')
                if len(input_values) != 3:
                    raise ConvertionException("Неверное число параметров.")
                quote, base, amount = input_values
                if quote == base:
                    raise ConvertionException("Валюта конвертации не может совпадать с исходной валютой.")
                if quote not in self.keys:
                    raise ConvertionException("Неверная исходная валюта.")
                if base not in self.keys:
                    raise ConvertionException("Неверная валюта конвертации.")
                try:
                    amount = float(amount)
                except ValueError:
                    raise ConvertionException("Введена неверная сумма.")
                url = f'http://api.currencylayer.com/live?access_key={ACCESS_KEY}&currencies={self.keys[base]}&source={self.keys[quote]}&format=1'
                response = requests.get(url)
                data = response.json()
                rate = data['quotes'][f'{self.keys[quote]}{self.keys[base]}']
                converted_amount = self.format_amount(amount * rate)
                quote_plural_form = self.get_plural(quote, amount)
                base_plural_form = self.get_plural(base, converted_amount)

                quote_plural_form = self.get_plural(quote, amount)
                base_plural_form = self.get_plural(base, converted_amount) if not amount.is_integer() else self.get_plural(base, amount)

                text = f'{self.format_amount(amount)} {quote_plural_form} = {self.format_amount(converted_amount)} {base_plural_form}'
                self.bot.send_message(message.chat.id, text)
            except ConvertionException as e:
                self.bot.reply_to(message, f'Произошла ошибка: {e}')

    def get_plural(self, word, amount):
        parsed_word = self.morph.parse(word)[0]
        plural_form = parsed_word.make_agree_with_number(amount).word
        return plural_form

    def format_amount(self, amount):
        if int(amount) == amount:
            return int(amount)
        return round(amount, 2)

    def run(self):
        self.bot.polling(none_stop=True)
