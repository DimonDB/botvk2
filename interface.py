import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from config import comunity_token, access_token, db_url_object
from core import VkTools
from data_store import user_check, add_bd_user
from sqlalchemy import create_engine

class BotInterface:
    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.longpoll = VkLongPoll(self.interface)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )
    def request_info(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                return event.text
            
    def int_check(self, num):
        try:
            int(num)
        except (TypeError, ValueError):
            return False
        else:
            return True
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Здравствуй {self.params["name"]}')
                    if self.params['year'] is None:
                        self.message_send(event.user_id, f'Укажите Ваш возраст, пожалуйста')
                        age = (self.request_info())
                        while not self.int_check(age):
                            self.message_send(event.user_id, f'Введите корректный возраст')
                            age = (self.request_info())
                        self.params['year'] = int(age)
                    if self.params['city'] is None:
                        self.message_send(event.user_id, f'Укажите Ваш город, пожалуйста')
                        self.params['city']= self.request_info()
                    self.message_send(event.user_id, f'Введите "поиск" для поиска')
                elif event.text.lower() == 'поиск':
                    self.message_send(event.user_id, 'Начинаю поиск')
                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.api.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.api.search_worksheet(self.params, self.offset)
                        worksheet = self.worksheets.pop()
                        photos = self.api.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 10
                    self.message_send(event.user_id, f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                                      attachment = photo_string)
                     # Проверка и добавление в бд
                    if not user_check(engine, event.user_id, worksheet["id"]):
                        add_bd_user(engine, event.user_id, worksheet["id"])
                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'До новых встреч')
                else:
                    self.message_send(event.user_id, 'Вы ввели неизвестную команду')

if __name__ == '__main__':
    engine = create_engine(db_url_object)
    bot_interface = BotInterface(comunity_token, access_token)
    bot_interface.event_handler()

