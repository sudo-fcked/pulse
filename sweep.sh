#!/bin/bash
# Make sure to make this executable with: chmod +x sweep.sh

# Loop over all YAML configuration files in the configs directory
for config_file in configs/*.yaml; do
    echo "Starting training run for $config_file..."
    # Replace 'src/train.py' with the actual path to your training script
    python src/train.py --config "$config_file"
done
