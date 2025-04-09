#!/bin/bash
#SBATCH --job-name=generate  # Job name
#SBATCH --output=logs/%j.out # Name of stdout output file
#SBATCH --error=logs/%j.err  # Name of stderr error file
#SBATCH --partition=standard-g  # Partition (queue) name
#SBATCH --nodes=1              # Total number of nodes
#SBATCH --ntasks-per-node=1     # 8 MPI ranks per node, 128 total (16x8)
#SBATCH --gpus-per-node=8
#SBATCH --time=00:20:00       # Run time (d-hh:mm:ss)
#SBATCH --account=project_462000447  # Project for billing


module use /appl/local/csc/modulefiles/
module load pytorch


python inference.py \
        --model LumiOpen/Poro-34B-chat \
        --prompts_file sample_prompts.txt \
        --temperature 1.0 --top_k 10
