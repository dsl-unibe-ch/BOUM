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

from app.utils import run_job as run_slurm_job, get_jobs as get_slurm_jobs
from app.config import Config

class VideoStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    PROCESSED = 2
    FAILED = 3

JOB_POLL_INTERVAL_SECONDS = 2 * 60
DB_POLL_INTERVAL_SECONDS = 5

# global exit event for graceful shutdown of worker processes
exit_event = multiprocessing.Event()

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)

if Config.DATABASE_URL.startswith("sqlite"):
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

    job_id = run_slurm_job(
        gres=Config.SLURM_GRES,
        mem=Config.SLURM_MEM,
        ncpus=Config.SLURM_CPUS_PER_TASK,
        batch_file=Config.SLURM_BATCH_FILE
    )

    logging.info(f"Submitted SLURM job {job_id} for video {video_id}")

    while True:
        job = [j for j in get_slurm_jobs() if j.job_id == job_id].pop()

        if "COMPLETED" in job.state.current or "FAILED" in job.state.current:
            logging.info(f"Job {job_id} for video {video_id} finished with state: {job.state.current}")
            break

        elif "CANCELLED" in job.state.current:
            logging.warning(f"Job {job_id} for video {video_id} was cancelled: {job.state.reason}.")

            raise Exception(f"Job {job_id} was cancelled: {job.state.reason}.")

        elif "FAILED" in job.state.current:
            logging.error(f"Job {job_id} for video {video_id} failed: {job.state.reason}.")

            raise Exception(f"Job {job_id} failed: {job.state.reason}.")

        time.sleep(JOB_POLL_INTERVAL_SECONDS)


def monitoring_loop():
    """
    Main worker loop to monitor and process video tasks.
    """

    engine.dispose()  # Ensure new connections for this process

    logging.info(f"{multiprocessing.current_process().name} started.")

    """
    TODO: sort queue by time to process the latest first
    """

    while not exit_event.is_set():
        session = SessionLocal()
        try:
            task = session.query(Video).filter(
                Video.status.is_(VideoStatus.PENDING)
            ).first()

            if not task:
                time.sleep(DB_POLL_INTERVAL_SECONDS)
                continue

            original_status = task.status

            rows_affected = session.query(Video).filter(
                Video.id == task.id,
                Video.status == original_status # required to avoid race condition
            ).update({"status": VideoStatus.PROCESSING})

            session.commit()

            if rows_affected == 0:
                continue # lost race, loop again

            # from here we can assume we have the lock on the task and can safely
            # process it

            try:
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
    num_workers = Config.NUM_WORKERS
    
    for i in range(num_workers):
        p = multiprocessing.Process(target=monitoring_loop, name=f"Worker-{i}")
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

if __name__ == "__main__":
    main()