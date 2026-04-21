# Video Processing Worker

A multi-process worker service that processes videos by submitting SLURM jobs to a remote HPC cluster.

## Overview

The worker polls a database for videos with `PENDING` status, submits them as SLURM batch jobs via SSH, monitors job progress, and updates video status to `PROCESSED` or `FAILED` based on the job outcome.

## Components

- **`main.py`**: Core worker logic with monitoring loop and multiprocessing
- **`config.py`**: Configuration via environment variables (SLURM settings, SSH, database)
- **`utils.py`**: SSH connection handling and SLURM job management (sacct/sbatch)

## Features

- Multi-worker processing (configurable via `NUM_WORKERS`)
- Graceful shutdown on SIGINT/SIGTERM
- Database-backed task queue (SQLite or PostgreSQL)
- SLURM job status polling
- Race-condition-safe task claiming

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `SLURM_HOST` | localhost | SLURM cluster hostname |
| `SLURM_USER` | user | SSH username |
| `SSH_KEY_PATH` | ~/.ssh/id_rsa | SSH private key path |
| `KNOWN_HOSTS_FILE` | ~/.ssh/known_hosts | Known hosts file |
| `SLURM_GRES` | gpu:rtx4090 | GPU resources |
| `SLURM_MEM` | 4 | Memory in GB |
| `SLURM_CPUS_PER_TASK` | 2 | CPUs per task |
| `SLURM_BATCH_FILE` | ~/nop.sh | Batch script path |
| `DATABASE_URL` | sqlite+pysqlite:///app.db | Database connection URL |
| `VIDEO_INPUT_DIR` | /tmp/videos | Video input directory |
| `NUM_WORKERS` | 4 | Number of worker processes |

## SLURM Batch Script
In production, the following script is used to process videos:

```bash
#!/bin/bash
#SBATCH --qos=job_gpu_preemptable
#SBATCH --partition=gpu-invest
#SBATCH --gres=gpu:h100:1
#SBATCH --mem=90G
#SBATCH --cpus-per-task=16
#SBATCH --nodes=1
#SBATCH --time=02:00:00
#SBATCH --job-name=boum_pipeline
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

PROJECT_DIR='...'
UPLOAD_DIR='...'
FILENAME="${1:?Usage: sbatch submit.sh <dataset_folder>}"
DATASET="$(cut -d . -f1 $FILENAME)"  # the expected structure of the filename is `{UUIDv4}.{EXT}`

cd "$PROJECT_DIR"

mkdir -p logs
mkdir -p "Data/$DATASET/input"

# $UPLOAD_DIR is not auto-bound with exec so we have to bind it
apptainer exec --bind "$UPLOAD_DIR:/uploads" boum.sif ffmpeg -i "/uploads/$FILENAME" -q:v 2 -start_number 1 "Data/$DATASET/input/%06d.jpg"

apptainer run --nv \
  --bind "$PROJECT_DIR/outputs:/outputs" \
  --bind "$PROJECT_DIR/Data:/Data" \
  boum.sif \
  /scripts/gs_pipeline.py quick-clean --data-dir "Data/${DATASET}"
"boum_quick_clean_slurm.sh" 30L, 990B written       
```
