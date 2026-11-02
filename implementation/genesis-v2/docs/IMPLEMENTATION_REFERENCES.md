# Primary implementation references checked 2026-11-02

- PyTorch functional_call (tie_weights, buffers, functional parameter identity): https://docs.pytorch.org/docs/stable/generated/torch.func.functional_call.html
- PyTorch jvp: https://docs.pytorch.org/docs/stable/generated/torch.func.jvp.html
- PyTorch reproducibility: https://docs.pytorch.org/docs/stable/notes/randomness.html
- Official wheel archive (2.10.0 + CUDA 12.8, Windows CPython 3.11/3.12/3.13 confirmed listed): https://download.pytorch.org/whl/cu128/torch/
- Official paired torchvision 0.25.0 and torch 2.10.0 installation: https://pytorch.org/get-started/previous-versions/#v2-10-0
- Gradient Smoothing, primary HTML Eq. (2), Algorithm 1: https://arxiv.org/html/2606.30813v1
- PMLR paper: https://proceedings.mlr.press/v306/meng26j.html

This implementation uses an explicitly labeled window-smoothing reference on base optimizer updates, not raw gradients. Decoupled weight decay is kept outside the smoothing. The author repository was discoverable but not imported; no claim is made that these are the authors' benchmark code/results. All optimizer comparisons still require local scientific execution and fairness review.

The packaged torch version is a compatible tested API baseline, not a 'latest version' claim. This build was executed with torch 2.10.0+cpu/Python 3.13.5 on Linux. Windows CUDA wheels exist, but the user's driver, CUDA runtime and actual 4070 Ti numerical G0 have NOT been verified here.
