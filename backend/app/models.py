from typing import Optional
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, LargeBinary, Table, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bcrypt import hashpw, gensalt, checkpw
from app.extensions import Base
from app.constants import MAX_VIDEO_NAME_LEN, UserRole, VideoStatus


experiment_users = Table(
    "experiment_users",
    Base.metadata,
    Column("experiment_id", Integer, ForeignKey("experiments.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    pw_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[int] = mapped_column(Integer, default=UserRole.USER)

    experiments: Mapped[list["Experiment"]] = relationship(
        secondary=experiment_users, back_populates="users"
    )

    def __init__(self, username: str, pw: str, role: UserRole = UserRole.USER):
        pw_hash = hashpw(pw.encode("utf-8"), gensalt())
        super().__init__(username=username, pw_hash=pw_hash, role=role)

    @property
    def password(self) -> None:
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, plain_text_password: str) -> None:
        self.pw_hash = hashpw(plain_text_password.encode("utf-8"), gensalt())

    def verify_password(self, plain_text_password: str) -> bool:
        return checkpw(plain_text_password.encode("utf-8"), self.pw_hash)


class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), unique=True, nullable=False)

    title: Mapped[Optional[str]] = mapped_column(String(200))
    species: Mapped[Optional[str]] = mapped_column(String(100))
    cultivar: Mapped[Optional[str]] = mapped_column(String(100))
    genotype: Mapped[Optional[str]] = mapped_column(String(100))
    plant_age: Mapped[Optional[str]] = mapped_column(String(50))
    plant_growth_stage: Mapped[Optional[str]] = mapped_column(String(100))
    growth_environment: Mapped[Optional[str]] = mapped_column(String(100))
    pot_volume: Mapped[Optional[float]] = mapped_column(Float)
    substrate_type: Mapped[Optional[str]] = mapped_column(String(100))
    special_plant_treatments: Mapped[Optional[str]] = mapped_column(String(500))
    operator: Mapped[Optional[str]] = mapped_column(String(100))
    creation_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    video: Mapped["Video"] = relationship(back_populates="video_metadata")

    @classmethod
    def metadata_fields(cls):
        skip = {"id", "video_id"}
        return [c.key for c in cls.__table__.columns if c.key not in skip]


class ExperimentMetadataDefaults(Base):
    __tablename__ = "experiment_metadata_defaults"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), unique=True, nullable=False)

    species: Mapped[Optional[str]] = mapped_column(String(100))
    cultivar: Mapped[Optional[str]] = mapped_column(String(100))
    genotype: Mapped[Optional[str]] = mapped_column(String(100))
    plant_age: Mapped[Optional[str]] = mapped_column(String(50))
    plant_growth_stage: Mapped[Optional[str]] = mapped_column(String(100))
    growth_environment: Mapped[Optional[str]] = mapped_column(String(100))
    pot_volume: Mapped[Optional[float]] = mapped_column(Float)
    substrate_type: Mapped[Optional[str]] = mapped_column(String(100))
    special_plant_treatments: Mapped[Optional[str]] = mapped_column(String(500))
    operator: Mapped[Optional[str]] = mapped_column(String(100))

    experiment: Mapped["Experiment"] = relationship(back_populates="metadata_defaults")

    @classmethod
    def metadata_fields(cls):
        skip = {"id", "experiment_id"}
        return [c.key for c in cls.__table__.columns if c.key not in skip]


class Video(Base):
    __tablename__ = "videos"

    MAX_NAME_LEN = MAX_VIDEO_NAME_LEN

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(MAX_VIDEO_NAME_LEN), nullable=False)
    path: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=VideoStatus.PENDING)

    experiment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("experiments.id"), nullable=True
    )
    experiment: Mapped[Optional["Experiment"]] = relationship(back_populates="videos")
    video_metadata: Mapped[Optional["VideoMetadata"]] = relationship(
        back_populates="video", uselist=False, cascade="all, delete-orphan"
    )

    def __init__(self, filename: str, path: str, experiment_id: int):
        super().__init__(filename=filename, path=path, experiment_id=experiment_id)

    def apply_experiment_defaults(self, defaults: "ExperimentMetadataDefaults") -> None:
        """Populate metadata from experiment defaults, without overwriting existing values."""
        if self.video_metadata is None:
            self.video_metadata = VideoMetadata(video_id=self.id)
        for field in ExperimentMetadataDefaults.metadata_fields():
            if getattr(self.video_metadata, field) is None:
                setattr(self.video_metadata, field, getattr(defaults, field))


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    videos: Mapped[list["Video"]] = relationship(
        back_populates="experiment", foreign_keys="[Video.experiment_id]"
    )
    users: Mapped[list["User"]] = relationship(
        secondary=experiment_users, back_populates="experiments"
    )
    metadata_defaults: Mapped[Optional["ExperimentMetadataDefaults"]] = relationship(
        back_populates="experiment", uselist=False, cascade="all, delete-orphan"
    )

    def __init__(self, name: str, users: list[User] | None = None, start_date: datetime | None = None):
        super().__init__(name=name, users=users or [], start_date=start_date)

    def is_user_participant(self, user_id: int) -> bool:
        return any(user.id == user_id for user in self.users)