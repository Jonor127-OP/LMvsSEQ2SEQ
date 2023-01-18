#!/bin/bash

#SBATCH --job-name=wmt-en2de-test

#SBATCH --qos=qos_gpu-t3

#SBATCH --output=./logfiles/test.out

#SBATCH --error=./logfiles/test.err

#SBATCH --time=01:00:00

#SBATCH --ntasks=1

#SBATCH --gres=gpu:4

#SBATCH --cpus-per-task=40

#SBATCH --hint=nomultithread

#SBATCH --constraint=v100-32g


module purge
module load anaconda-py3/2019.03
conda activate lmvsseq2seq
set -x
nvidia-smi
# This will create a config file on your server


srun accelerate launch --multi_gpu train_enc_dec_mp.py --train=False --test=True