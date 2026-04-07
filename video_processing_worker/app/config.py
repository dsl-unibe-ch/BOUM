from os import getenv

class Config:
    SLURM_HOST = getenv("SLURM_HOST", "localhost")
    SLURM_USER = getenv("SLURM_USER", "user")

    SSH_KEY_PATH = getenv("SSH_KEY_PATH", f"{getenv('HOME')}/.ssh/id_rsa")
    KNOWN_HOSTS_FILE = getenv("KNOWN_HOSTS_FILE", f"{getenv('HOME')}/.ssh/known_hosts")

    SLURM_GRES          = getenv("SLURM_GRES", "gpu:rtx4090")
    SLURM_MEM           = int(getenv("SLURM_MEM", 4))
    SLURM_CPUS_PER_TASK = int(getenv("SLURM_CPUS_PER_TASK", 2))
    SLURM_BATCH_FILE    = getenv("SLURM_BATCH_FILE", "~/nop.sh")

    DATABASE_URL    = getenv('DATABASE_URL', 'sqlite+pysqlite:///app.db')
    VIDEO_INPUT_DIR = getenv('VIDEO_INPUT_DIR', '/tmp/videos')

    NUM_WORKERS = int(getenv("NUM_WORKERS", 4))