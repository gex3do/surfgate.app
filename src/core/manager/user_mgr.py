import hashlib
import uuid

from sqlalchemy.orm import Session

from src.core.entity.user import User
from src.utils.logger import logger


class UserMgr:
    def __init__(self, settings):
        self.settings = settings
        self.salt_prefix = self.settings["main"]["password_salt"]

    def create_user(
        self, sess: Session, firstname: str, lastname: str, email: str, user_type: str
    ) -> User:
        password = UserMgr.generate_password()

        logger.info("Create User\nEmail: {}\nPassword: {}\n".format(email, password))

        hashed_password = self._hash_password(password)

        user = User(
            firstname=firstname,
            lastname=lastname,
            password=hashed_password,
            email=email,
            type=user_type,
            uuid=str(uuid.uuid4()),
        )
        sess.add(user)
        sess.flush()
        return user

    @staticmethod
    def get_user_by_uuid(sess: Session, user_uuid: uuid.UUID) -> User | None:
        return sess.query(User).filter(User.uuid == str(user_uuid)).first()

    def _hash_password(self, password: str) -> str:
        return hashlib.md5(str(self.salt_prefix + password).encode("utf8")).hexdigest()

    @staticmethod
    def generate_password() -> str:
        return uuid.uuid4().hex.upper()[0:6]
