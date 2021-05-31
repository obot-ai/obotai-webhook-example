class BaseResponse:
    def as_dict(self):
        return {}


class Text(BaseResponse):
    """テキストレスポンス

    :text: 1つの場合
    :texts: 複数からランダム表示の場合
    """
    def __init__(self, text=None, texts=None):
        self.text = text
        self.texts = texts or []

    def as_dict(self):
        if self.text is None:
            texts = self.texts
        else:
            texts = [self.text]
        data = {
            'payload': {
                'responseType': 0,
                'platform': 'web_chat_v2',
                'web_chat_v2': {
                    'message_type': 0,
                    'type': 'message',
                    'texts': texts,
                }
            }
        }
        return data


class QuickReplies(BaseResponse):
    """クイックリプライ
    """
    def __init__(self, title=None, replies=None):
        self.title = title
        self.replies = replies or []

    def as_dict(self):
        data = {
            'payload': {
                'platform': 'web_chat_v2',
                'web_chat_v2': {
                    'message_type': 2,
                    'type': 'message',
                    'quick_replies': [
                        {
                            'title': self.title or '',
                            'replies': self.replies,
                        }
                    ]
                }
            }
        }
        return data


class Button:
    def __init__(self, btn_text, post_back=None, open_url=None):
        self.btn_text = btn_text
        self.post_back = post_back
        self.open_url = open_url

    def as_dict(self):
        data = {
            'btn_text': self.btn_text
        }
        if self.post_back:
            data['post_back'] = self.post_back
        if self.open_url:
            data['open_url'] = self.open_url
        return data


class Card:
    def __init__(self, title=None, subtitle=None, src=None, buttons=None):
        self.title = title
        self.subtitle = subtitle
        self.src = src
        self.buttons = buttons or []

    def as_dict(self):
        data = {
            'buttons': [button.as_dict() for button in self.buttons],
            'title': self.title or '',
            'subtitle': self.subtitle or '',
        }
        return data


class Cards(BaseResponse):
    """カード
    """
    def __init__(self, cards=None):
        self.cards = cards or []

    def as_dict(self):
        data = {
            'payload': {
                'platform': 'web_chat_v2',
                'web_chat_v2': {
                    'message_type': 1,
                    'type': 'message',
                    'cards': [card.as_dict() for card in self.cards]
                }
            }
        }
        return data


class CarouselOptions(BaseResponse):
    """カルーセルオプション
    """
    def __init__(self, cards=None):
        self.cards = cards or []

    def as_dict(self):
        data = {
            'payload': {
                'platform': 'web_chat_v2',
                'responseType': 501,
                'web_chat_v2': {
                    'message_type': 1,
                    'type': 'message',
                    'cards': [card.as_dict() for card in self.cards]
                }
            }
        }
        return data
