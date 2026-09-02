# GPU Configuration for Symbolic Regression Algorithms

## Overview

This document explains how to configure GPU usage for DSR, BSR, and AIFeynman algorithms.

## Algorithm GPU Support

| Algorithm | GPU Support | Framework | Configuration Method |
|-----------|-------------|-----------|---------------------|
| **DSR** | ✅ Yes | TensorFlow 1.x | Automatic (if CUDA available) + ConfigProto |
| **BSR** | ❌ No | NumPy/SciPy | CPU-only (no GPU support) |
| **AIFeynman** | ✅ Yes | PyTorch | Automatic (if CUDA available) |

## DSR (Deep Symbolic Regression) - GPU Setup

DSR uses TensorFlow 1.x and can utilize GPU if CUDA is available.

### Requirements
- CUDA-compatible GPU
- TensorFlow with GPU support installed in `dso_env`
- CUDA drivers installed

### Configuration

DSR automatically uses GPU if:
1. CUDA is available
2. TensorFlow GPU version is installed
3. GPU memory growth is enabled (already configured in `dso/core.py`)

### Environment Variables

Set `CUDA_VISIBLE_DEVICES` to specify which GPU(s) to use:

```bash
# Use GPU 0
export CUDA_VISIBLE_DEVICES=0

# Use GPU 1
export CUDA_VISIBLE_DEVICES=1

# Use multiple GPUs (TensorFlow will use first available)
export CUDA_VISIBLE_DEVICES=0,1

# Disable GPU (force CPU)
export CUDA_VISIBLE_DEVICES=""
```

### Verify GPU Usage

Check if TensorFlow sees the GPU:
```python
import tensorflow as tf
print("GPU Available:", tf.test.is_gpu_available())
print("GPU Devices:", tf.config.list_physical_devices('GPU'))
```

### Run Scripts with GPU

Update run scripts to set `CUDA_VISIBLE_DEVICES`:

```bash
# In run_dsr_enb.sh, add before python command:
export CUDA_VISIBLE_DEVICES=0  # or 1, 2, etc.
python analyze.py ...
```

## AIFeynman - GPU Setup

AIFeynman uses PyTorch and **automatically uses GPU** if CUDA is available.

### Requirements
- CUDA-compatible GPU
- PyTorch with CUDA support installed in `aifeynman_env` or `env_alfey`

### Configuration

AIFeynman automatically detects and uses GPU via:
- `torch.cuda.is_available()` check
- `.cuda()` calls on tensors and models

### Environment Variables

Set `CUDA_VISIBLE_DEVICES` to specify which GPU to use:

```bash
# Use GPU 0
export CUDA_VISIBLE_DEVICES=0

# Use GPU 1
export CUDA_VISIBLE_DEVICES=1

# Disable GPU (force CPU)
export CUDA_VISIBLE_DEVICES=""
```

### Verify GPU Usage

Check if PyTorch sees the GPU:
```python
import torch
print("CUDA Available:", torch.cuda.is_available())
print("CUDA Device Count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("Current Device:", torch.cuda.current_device())
    print("Device Name:", torch.cuda.get_device_name(0))
```

## BSR - CPU Only

BSR uses NumPy and SciPy, which are CPU-only libraries. **BSR cannot use GPU**.

## Recommended Setup

### For Single GPU System
```bash
export CUDA_VISIBLE_DEVICES=0
```

### For Multi-GPU System
Distribute jobs across GPUs:
- **GPU 0**: DSR experiments
- **GPU 1**: AIFeynman experiments  
- **GPU 2**: Other DSR experiments

### Example: Run DSR on GPU 1
```bash
cd /raid/hussein/project/srbench/experiment
export CUDA_VISIBLE_DEVICES=1
conda activate srbench
python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 \
    -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16
```

### Example: Run AIFeynman on GPU 2
```bash
cd /raid/hussein/project/srbench/experiment
export CUDA_VISIBLE_DEVICES=2
conda activate srbench
python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 \
    -results ../.results -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16
```

## Troubleshooting

### DSR Not Using GPU

1. **Check TensorFlow GPU installation**:
   ```bash
   conda activate dso_env
   python -c "import tensorflow as tf; print(tf.test.is_gpu_available())"
   ```

2. **Check CUDA availability**:
   ```bash
   nvidia-smi
   ```

3. **Verify CUDA_VISIBLE_DEVICES**:
   ```bash
   echo $CUDA_VISIBLE_DEVICES
   ```

### AIFeynman Not Using GPU

1. **Check PyTorch CUDA installation**:
   ```bash
   conda activate env_alfey  # or aifeynman_env
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Check CUDA availability**:
   ```bash
   nvidia-smi
   ```

### GPU Memory Issues

If you encounter "out of memory" errors:

1. **For DSR**: GPU memory growth is already enabled, but you can reduce batch size:
   ```python
   config["training"]["batch_size"] = 500  # Reduce from 1000
   ```

2. **For AIFeynman**: Reduce batch size in neural network training (modify `S_NN_train.py`)

3. **Use specific GPU**:
   ```bash
   export CUDA_VISIBLE_DEVICES=1  # Use GPU 1 instead of 0
   ```

## Performance Notes

- **DSR**: GPU acceleration primarily helps with neural network training (policy network)
- **AIFeynman**: GPU significantly speeds up neural network training phases
- **BSR**: CPU-only, no GPU benefit available

## Updating Run Scripts

To add GPU support to run scripts, add `CUDA_VISIBLE_DEVICES` export:

```bash
# In .run/run_dsr_enb.sh, add after conda activate:
export CUDA_VISIBLE_DEVICES=0  # Change to desired GPU ID
```
