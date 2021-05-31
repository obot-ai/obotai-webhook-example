import copy
from enum import Enum

from util.session import SessionManager
from util import web_chat_v2


class State(Enum):
    START = 1  # 最初
    INPUT_TEXT = 2  # テキスト入力待ち
    SELECT_ITEM = 3  # アイテム選択
    RESULT = 4  # 結果表示


class Item(Enum):
    FLUITS = 'フルーツ'
    VEGETABLES = '野菜'


DATA = [
    {'kind': 'フルーツ', 'name': 'りんご'},
    {'kind': 'フルーツ', 'name': 'バナナ'},
    {'kind': '野菜', 'name': 'じゃがいも'},
    {'kind': '野菜', 'name': 'キャベツ'},
    {'kind': '野菜', 'name': 'トマト'},
]


class WebhookError(Exception):
    pass


class MyWebhookHandler:
    KEY_PREFIX = 'my_webhook_'

    def __init__(self, request_data):
        self.request_data = request_data
        self.session_manager = SessionManager()
        self.is_new_session = False
        self.session = None
        self.language_code = None
        self.query_text = None
        self.delete_session = False

    def session_value_key(self, key):
        return f'{self.KEY_PREFIX}{key}'

    def get_value(self, key, default=None):
        value_key = self.session_value_key(key)
        return self.session.get(value_key, default)

    def set_value(self, key, data):
        value_key = self.session_value_key(key)
        self.session[value_key] = data

    def get_platform_session_id(self, request_data):
        payload = request_data['originalDetectIntentRequest']['payload']
        platform = payload['platform']
        session_id = payload['session_id']
        return platform, session_id

    def get_language_code(self, request_data):
        language_code = request_data['queryResult']['languageCode']
        return language_code

    def get_quety_text(self, request_data):
        query_text = request_data['queryResult']['queryText']
        return query_text

    def get_query_output_context(self, request_data):
        output_context = copy.deepcopy(request_data['queryResult']['outputContexts'])
        return output_context

    def get_state(self):
        state = self.get_value('state')
        return state

    def set_state(self, state):
        self.set_value('state', state)

    def add_condition(self, cond_key, cond_value, overwrite=False):
        """検索条件の追加
        """
        conditions = self.get_value('conditions', [])
        # 上書きの場合
        if overwrite:
            new_condtions = []
            for exist_key, exist_value in conditions + [(cond_key, cond_value)]:
                if exist_key == cond_key:
                    new_condtions.append((cond_key, cond_value))
                else:
                    new_condtions.append((exist_key, exist_value))
        else:
            new_condtions = conditions + [(cond_key, cond_value)]
        self.set_value('conditions', new_condtions)

    def reset_condition(self):
        self.set_value('conditions', [])

    def handle(self):
        # 言語
        self.language_code = self.get_language_code(self.request_data)
        # 質問内容
        self.query_text = self.get_quety_text(self.request_data)

        # セッション復元
        platform, session_id = self.get_platform_session_id(self.request_data)
        session, created = self.session_manager.get_or_create(session_id, self.language_code)
        self.platform = platform
        self.session = session
        self.is_new_session = created

        result = {}
        state = self.get_state()
        # テキスト・状態によって処理を切り替え
        if self.query_text == '終了':
            # 終了の場合
            result = self.exit()
        elif self.query_text == 'はじめにもどる':
            # はじめにもどる
            result = self.back_to_start()
        elif state is None:
            result = self.state_initial()
        elif state == State.START:
            result = self.state_start()
        elif state == State.INPUT_TEXT:
            result = self.state_input_text()
        elif state == State.SELECT_ITEM:
            result = self.state_select_item()
        elif state == State.RESULT:
            result = self.state_result()

        # メッセージにindexを付与
        if 'fulfillmentMessages' in result:
            for index, payload in enumerate(result['fulfillmentMessages'], 1):
                payload['index'] = index

        # 10以上のライフスパン値のコンテキストをoutput 20にして維持
        # 自動で抜けてしまわないように
        if 'outputContexts' not in result:
            output_context = self.get_query_output_context(self.request_data)
            for context in output_context:
                lifespanCount = context.get('lifespanCount')
                if lifespanCount and lifespanCount > 10:
                    context['lifespanCount'] = 20
            result['outputContexts'] = output_context

        # セッション保存
        if self.delete_session:
            self.session.delete()
        else:
            self.session.save()

        return result

    def state_initial(self):
        """状態なし、初回
        """
        # 状態変更
        self.set_state(State.START)
        result = self.state_start()
        result['fulfillmentMessages'].insert(
            0,
            web_chat_v2.Text(
                'ウェブフックのサンプルです'
            ).as_dict(),
        )
        return result

    def state_start(self):
        # 入力されるまで状態を維持
        if self.query_text == 'テキスト入力':
            self.set_state(State.INPUT_TEXT)
            return self.state_input_text()
        elif self.query_text == 'アイテム選択':
            self.set_state(State.SELECT_ITEM)
            return self.state_select_item()
        card = web_chat_v2.Card(
            title='項目を選択してください',
        )
        cards = web_chat_v2.Cards([card])
        values = [
            'テキスト入力',
            'アイテム選択',
            '終了',
        ]
        for value in values:
            card.buttons.append(
                web_chat_v2.Button(btn_text=value, post_back=value))
        return {
            'fulfillmentMessages': [
                cards.as_dict(),
            ],
        }

    def state_input_text(self):
        # 入力されるまで状態を維持
        search_text = self.query_text and self.query_text.strip() or None
        if search_text != 'テキスト入力':
            self.add_condition('name', search_text)
            # 結果へ
            self.set_state(State.RESULT)
            return self.state_result()
        return {
            'fulfillmentMessages': [
                web_chat_v2.Text(
                    'テキストを入力してください'
                ).as_dict(),
            ]
        }

    def state_select_item(self):
        """アイテム選択
        """
        # 入力されるまで状態を維持
        values = [
            Item.FLUITS.value,
            Item.VEGETABLES.value,
        ]
        if self.query_text in values:
            self.add_condition('kind', self.query_text)
            # 結果へ
            self.set_state(State.RESULT)
            return self.state_result()
        card = web_chat_v2.Card(
            title='項目を選択して下さい',
        )
        cards = web_chat_v2.Cards([card])
        for value in values + ['はじめにもどる', '終了']:
            card.buttons.append(
                web_chat_v2.Button(btn_text=value, post_back=value))
        return {
            'fulfillmentMessages': [cards.as_dict()]
        }

    def state_result(self):
        if self.query_text == '検索条件を追加':
            self.set_state(State.START)
            return self.state_start()
        # 入力されるまで状態を維持
        # 検索結果を表示
        conditions = self.get_value('conditions', [])
        search_result = self.search(conditions)
        records_count = len(search_result)
        result = self.render_search_result(
            search_result, records_count, conditions)
        return result

    def search(self, conditions):
        result = []
        for item in DATA:
            for cond_key, cond_value in conditions:
                # 条件に一致するレコードを結果に入れる
                if item[cond_key] == cond_value:
                    result.append(item)
                    break
        return result

    def render_search_result(self, search_result, records_count, conditions):
        """検索結果
        """
        # 状態変更
        cards = self.search_result_to_cards(search_result)
        condition_texts = []
        for cond_key, cond_value in conditions:
            condition_texts.append(f'{cond_key}: {cond_value}')
        next_card = web_chat_v2.Card(
            title='項目を選択して下さい',
        )
        next_cards = web_chat_v2.CarouselOptions([next_card])
        next_values = [
            '検索条件を追加',
            'はじめにもどる',
            '終了',
        ]
        for value in next_values:
            next_card.buttons.append(
                web_chat_v2.Button(btn_text=value, post_back=value))
        result = {
            'fulfillmentMessages': [
                web_chat_v2.Text(
                    '検索結果(OR検索)は {records_count} 件です。'.format(
                        records_count=records_count,
                    ) + '\n' + '\n'.join(condition_texts)
                ).as_dict(),
                cards.as_dict(),
                next_cards.as_dict(),
            ],
        }
        return result

    def search_result_to_cards(self, search_result):
        """検索結果をカードにする
        """
        # 結果を作成
        cards = web_chat_v2.Cards()
        for record in search_result:
            card = web_chat_v2.Card(
                title=record['name'],
                subtitle=f'種類: {record["kind"]}',
            )
            cards.cards.append(card)
        return cards

    def back_to_start(self):
        """はじめにもどる
        """
        self.reset_condition()
        result = self.state_initial()
        return result

    def exit(self):
        """終了
        """
        self.delete_session = True
        output_context = self.get_query_output_context(self.request_data)
        for context in output_context:
            context['lifespanCount'] = 0
        result = {
            'fulfillmentMessages': [
                web_chat_v2.Text(
                    'ウェブフックのコンテキストを終了しました。'
                ).as_dict(),
            ],
            'outputContexts': output_context,
        }
        return result
