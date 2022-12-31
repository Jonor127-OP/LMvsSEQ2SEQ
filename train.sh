#!/bin/bash

#SBATCH --job-name=RA

#SBATCH --qos=qos_gpu-t4

#SBATCH --output=./logfiles/logfile_wmt.out

#SBATCH --time=05:59:00

#SBATCH --ntasks=1

#SBATCH --gres=gpu:4

#SBATCH --cpus-per-task=40

#SBATCH --hint=nomultithread




module purge
module load anaconda-py3/2019.03
conda activate lmvsseq2seq
set -x
nvidia-smi
# This will create a config file on your server


srun accelerate launch --multi_gpu train_enc_dec_mp.py