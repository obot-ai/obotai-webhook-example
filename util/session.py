from django.core.cache import cache


class Session(dict):
    def __init__(
            self, *, manager=None, session_id=None,
            language_code=None, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.session_id = session_id
        self.language_code = language_code

    def save(self):
        self.manager.save(self)

    def delete(self):
        self.manager.delete(self.session_id, self.language_code)


class SessionManager:
    """セッションは言語ごとに保持する
    """
    def __init__(self, store=None):
        self.store = store or cache  # default: django cache

    def session_store_key(self, session_id, language_code):
        return f'sess_{session_id}_{language_code}'

    def get(self, session_id, language_code):
        key = self.session_store_key(session_id, language_code)
        data = self.store.get(key)
        if data is None:
            return
        session = Session(
            manager=self,
            session_id=session_id,
            language_code=language_code,
            **data)
        return session

    def get_or_create(self, session_id, language_code):
        """
        :returns: session, created
        """
        exist_session = self.get(session_id, language_code)
        if exist_session is not None:
            return exist_session, False
        new_session = Session(
            manager=self,
            session_id=session_id,
            language_code=language_code)
        return new_session, True

    def save(self, session):
        key = self.session_store_key(
            session.session_id, session.language_code)
        data = dict(**session)
        self.store.set(key, data)

    def delete(self, session_id, language_code):
        key = self.session_store_key(session_id, language_code)
        self.store.delete(key)
