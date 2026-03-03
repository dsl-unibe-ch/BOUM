from enum import IntEnum
import multiprocessing
import os
from sqlalchemy import create_engine, Integer, String, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from random import randint
import time
import logging
import signal
from os import stat

class VideoStatus(IntEnum):
    PENDING = 0
    SEEN = 1
    CHECKED = 2
    PROCESSING = 3
    PROCESSED = 4
    FAILED = 5

DATABASE_URL    = os.getenv('DATABASE_URL', 'sqlite+pysqlite:///app.db')
VIDEO_INPUT_DIR = os.getenv('VIDEO_INPUT_DIR', '/tmp/videos')

# global exit event for graceful shutdown of worker processes
exit_event = multiprocessing.Event()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

class Base(DeclarativeBase):
    ...

class Video(Base):
    __tablename__ = "videos"

    MAX_NAME_LEN = 200

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(MAX_NAME_LEN), nullable=False)
    path: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[int] = mapped_column(Integer, default=VideoStatus.PENDING)

def validate_video_mock(file_path):
    """
    Simulate video validation

    :param file_path: Description
    :return: bool
    """

    logging.info(f"Validating video at {file_path}")
    time.sleep(2) 

    random_outcome = randint(0, 10)
    if random_outcome < 2:
        logging.info(f"Validation failed for {file_path}")
        return False

    return True

def process_video_mock(video_id, file_path):
    """
    Simulate video processing
    
    :param video_id: Description
    :param file_path: Description
    """

    logging.info(f"Processing video {video_id} at {file_path}")
    time.sleep(10) 
    logging.info(f"Finished {video_id}")

def monitoring_loop():
    """
    Main worker loop to monitor and process video tasks.
    """

    engine.dispose()  # Ensure new connections for this process

    logging.info(f"{multiprocessing.current_process().name} started.")

    while not exit_event.is_set():
        session = SessionLocal()
        try:
            task = session.query(Video).filter(
                Video.status.in_([VideoStatus.PENDING, VideoStatus.CHECKED])
            ).first()

            if not task:
                time.sleep(5)
                continue

            original_status = task.status

            new_interim_status = (VideoStatus.SEEN if original_status == VideoStatus.PENDING 
                                  else VideoStatus.PROCESSING)

            rows_affected = session.query(Video).filter(
                Video.id == task.id,
                Video.status == original_status # required to avoid race condition
            ).update({"status": new_interim_status})

            session.commit()

            if rows_affected == 0:
                continue # lost race, loop again

            try:
                if original_status == VideoStatus.PENDING:
                    success = validate_video_mock(task.path)
                    task.status = VideoStatus.CHECKED if success else VideoStatus.FAILED
                
                elif original_status == VideoStatus.CHECKED:
                    process_video_mock(task.id, task.path)
                    task.status = VideoStatus.PROCESSED

            except Exception as e:
                logging.error(f"Execution error on task {task.id}: {e}")
                task.status = VideoStatus.FAILED
            
            session.commit()

        except Exception as e:
            logging.error(f"Worker Loop Error: {e}")
            session.rollback()
            time.sleep(10)
        finally:
            session.close()

def signal_handler(_sig, _frame):
    """
    Handle shutdown signals to gracefully terminate worker processes.
    """

    logging.info("Shutdown signal received. Finishing current tasks...")
    exit_event.set()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    processes = []
    num_workers = 4
    
    for i in range(num_workers):
        p = multiprocessing.Process(target=monitoring_loop, name=f"Worker-{i}")
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

if __name__ == "__main__":
    main()