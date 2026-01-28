from sqlalchemy import ForeignKey, Integer, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bcrypt import hashpw, gensalt, checkpw
from app.extensions import Base
from app.constants import UserRole, VideoStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    pw_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[int] = mapped_column(Integer, default=UserRole.USER)

    videos: Mapped[list["Video"]] = relationship(back_populates="owner")

    def __init__(self, username: str, pw: str, role: UserRole = UserRole.USER):
        username = username
        pw_hash = hashpw(pw.encode("utf-8"), gensalt())

        super().__init__(username=username, pw_hash=pw_hash, role=role, videos=[])

    @property
    def password(self) -> None:
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, plain_text_password: str) -> None:
        self.pw_hash = hashpw(plain_text_password.encode("utf-8"), gensalt())

    def verify_password(self, plain_text_password: str) -> bool:
        return checkpw(plain_text_password.encode("utf-8"), self.pw_hash)


class Video(Base):
    __tablename__ = "videos"

    MAX_NAME_LEN = 200

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(MAX_NAME_LEN), nullable=False)
    path: Mapped[str] = mapped_column(String(200), nullable=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="videos")

    status: Mapped[int] = mapped_column(Integer, default=VideoStatus.PENDING)

    def __init__(self, filename: str, path: str, owner: User):
        super().__init__(filename=filename, path=path, owner=owner)