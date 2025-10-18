"""Train a ~26M parameter fully-connected network on synthetic data.

The script is intentionally self-contained so it can run without external ML
frameworks.  It builds a three-layer perceptron with roughly twenty-six million
trainable parameters, fits it on a tiny synthetic classification task, and
persists the learned weights to ``small_network_26m.npz`` in the project root.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Tuple

import numpy as np


def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0, out=x)


def relu_backward(grad_output: np.ndarray, pre_activation: np.ndarray) -> np.ndarray:
    grad = grad_output.copy()
    grad[pre_activation <= 0.0] = 0.0
    return grad


def softmax_cross_entropy(logits: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, float]:
    logits = logits - logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits, dtype=np.float64)
    probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
    loss = -np.log(probs[np.arange(labels.size), labels] + 1e-12).mean()
    probs[np.arange(labels.size), labels] -= 1.0
    probs /= labels.size
    return probs.astype(np.float32), float(loss)


def glorot_uniform(shape: Tuple[int, ...], rng: np.random.Generator) -> np.ndarray:
    if len(shape) != 2:
        raise ValueError("Glorot initialisation is only implemented for 2D matrices.")
    fan_in, fan_out = shape
    limit = math.sqrt(6.0 / (fan_in + fan_out))
    return rng.uniform(-limit, limit, size=shape).astype(np.float32)


def count_parameters(weights: dict[str, np.ndarray]) -> int:
    return int(sum(arr.size for arr in weights.values()))


def train(
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 5e-4,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    input_dim = 512
    hidden_dim1 = 2048
    hidden_dim2 = 12032
    num_classes = 10

    weights = {
        "W1": glorot_uniform((input_dim, hidden_dim1), rng),
        "b1": np.zeros(hidden_dim1, dtype=np.float32),
        "W2": glorot_uniform((hidden_dim1, hidden_dim2), rng),
        "b2": np.zeros(hidden_dim2, dtype=np.float32),
        "W3": glorot_uniform((hidden_dim2, num_classes), rng),
        "b3": np.zeros(num_classes, dtype=np.float32),
    }

    num_samples = 128
    features = rng.normal(size=(num_samples, input_dim)).astype(np.float32)
    weights_true = rng.normal(size=(input_dim, num_classes)).astype(np.float32)
    logits_true = features @ weights_true
    labels = logits_true.argmax(axis=1)

    parameter_count = count_parameters(weights)
    if parameter_count < 26_000_000 or parameter_count > 27_000_000:
        raise RuntimeError(
            f"Network parameter count {parameter_count:,} outside the expected ~26M range."
        )

    for epoch in range(epochs):
        permutation = rng.permutation(num_samples)
        features_shuffled = features[permutation]
        labels_shuffled = labels[permutation]

        epoch_loss = 0.0
        batches = 0
        for start in range(0, num_samples, batch_size):
            end = start + batch_size
            batch_x = features_shuffled[start:end]
            batch_y = labels_shuffled[start:end]

            z1 = batch_x @ weights["W1"] + weights["b1"]
            a1 = relu(z1.copy())
            z2 = a1 @ weights["W2"] + weights["b2"]
            a2 = relu(z2.copy())
            logits = a2 @ weights["W3"] + weights["b3"]

            grad_logits, loss = softmax_cross_entropy(logits, batch_y)
            epoch_loss += loss
            batches += 1

            grad_W3 = a2.T @ grad_logits
            grad_b3 = grad_logits.sum(axis=0)
            grad_a2 = grad_logits @ weights["W3"].T
            grad_z2 = relu_backward(grad_a2, z2)
            grad_W2 = a1.T @ grad_z2
            grad_b2 = grad_z2.sum(axis=0)
            grad_a1 = grad_z2 @ weights["W2"].T
            grad_z1 = relu_backward(grad_a1, z1)
            grad_W1 = batch_x.T @ grad_z1
            grad_b1 = grad_z1.sum(axis=0)

            weights["W3"] -= learning_rate * grad_W3
            weights["b3"] -= learning_rate * grad_b3
            weights["W2"] -= learning_rate * grad_W2
            weights["b2"] -= learning_rate * grad_b2
            weights["W1"] -= learning_rate * grad_W1
            weights["b1"] -= learning_rate * grad_b1

        average_loss = epoch_loss / max(batches, 1)
        print(f"Epoch {epoch + 1}/{epochs} - loss: {average_loss:.4f}")

    logits = relu(relu(features @ weights["W1"] + weights["b1"]) @ weights["W2"] + weights["b2"])
    logits = logits @ weights["W3"] + weights["b3"]
    predictions = logits.argmax(axis=1)
    accuracy = (predictions == labels).mean()
    print(f"Training accuracy: {accuracy:.2%}")

    return weights


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=5, help="Number of optimisation epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("small_network_26m.npz"),
        help="Destination file for the trained weights",
    )
    args = parser.parse_args()

    weights = train(epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)
    np.savez_compressed(args.output, **weights)
    print(f"Saved weights to {args.output.resolve()}")


if __name__ == "__main__":
    main()
