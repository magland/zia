import time
import json
import os
from typing import Dict, Any, Tuple, List
import numpy as np
from statistics import median
from .algorithms import algorithms
from .datasets import datasets
from ._memobin import (
    construct_memobin_url,
    construct_dataset_url,
    upload_to_memobin,
    download_from_memobin,
    exists_in_memobin,
)


system_version = "v4"
GITHUB_ALGORITHMS_PREFIX = "https://github.com/magland/zia/blob/main/zia_benchmark/src/zia_benchmark/algorithms/"
GITHUB_DATASETS_PREFIX = (
    "https://github.com/magland/zia/blob/main/zia_benchmark/src/zia_benchmark/datasets/"
)


def is_compatible(algorithm_tags: List[str], dataset_tags: List[str]) -> bool:
    """Check if an algorithm is compatible with a dataset based on their tags.

    Args:
        algorithm_tags: List of tags for the algorithm
        dataset_tags: List of tags for the dataset

    Returns:
        True if the algorithm should be applied to the dataset
    """
    # If algorithm has delta_encoding tag, dataset must have continuous tag
    if "delta_encoding" in algorithm_tags and "continuous" not in dataset_tags:
        return False
    if "markov_prediction" in algorithm_tags and "continuous" not in dataset_tags:
        return False
    return True


def run_benchmarks(
    cache_dir: str = ".benchmark_cache", verbose: bool = True
) -> Dict[str, Any]:
    """Run all benchmarks, with caching based on algorithm and dataset versions.

    Results are stored in separate directories for each dataset/algorithm combination:
    cache_dir/
        dataset_name/
            algorithm_name/
                metadata.json  # Contains algorithm version, dataset version, and results
                compressed.dat # The actual compressed data

    Args:
        cache_dir: Directory to store cached results

    Returns:
        Dictionary containing benchmark results and metadata
    """
    print("\n=== Starting Benchmark Run ===")
    print(f"Cache directory: {cache_dir}")

    os.makedirs(cache_dir, exist_ok=True)

    results = []
    print("\nRunning benchmarks for all dataset-algorithm combinations...")

    # Run benchmarks for each dataset and algorithm combination
    for dataset in datasets:
        dataset_tags = dataset.get("tags", [])
        print(f"\n*** Dataset: {dataset['name']} (tags: {dataset_tags}) ***")

        # data will only be created if needed
        data = None
        original_size = None
        dtype = None

        for algorithm in algorithms:
            alg_name = algorithm["name"]
            alg_tags = algorithm.get("tags", [])

            # Skip if algorithm and dataset are not compatible based on tags
            if not is_compatible(alg_tags, dataset_tags):
                if verbose:
                    print(
                        f"\nSkipping algorithm {alg_name} (tags: {alg_tags}) - incompatible with dataset tags"
                    )
                continue

            print(f"\nTesting algorithm: {alg_name} (tags: {alg_tags})")

            # Check if we can use cached result
            test_dir = os.path.join(cache_dir, dataset["name"], alg_name)
            metadata_file = os.path.join(test_dir, "metadata.json")
            compressed_file = os.path.join(test_dir, "compressed.dat")

            # First try local cache
            cached_data = None
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    cached_data = json.load(f)
                    # if versions do not match, then set to None
                    if isinstance(cached_data, dict) and "result" in cached_data:
                        result = cached_data["result"]
                        if (
                            result["algorithm_version"] != algorithm["version"]
                            or result["dataset_version"] != dataset["version"]
                            or result.get("system_version", "") != system_version
                        ):
                            cached_data = None

            # If not in local cache, try memobin
            if cached_data is None:
                memobin_url = construct_memobin_url(
                    alg_name,
                    dataset["name"],
                    algorithm["version"],
                    dataset["version"],
                    system_version,
                    "metadata.json",
                )
                if verbose:
                    print("  Looking for cached result in memobin...")
                cached_data = download_from_memobin(memobin_url)
                if cached_data is not None:
                    if verbose:
                        print("  Found result in memobin, saving locally...")
                    # Save to local cache
                    os.makedirs(test_dir, exist_ok=True)
                    with open(metadata_file, "w") as f:
                        json.dump(cached_data, f, indent=2)

            if (
                cached_data is not None
                and isinstance(cached_data, dict)
                and "result" in cached_data
            ):
                result = cached_data["result"]
                if (
                    isinstance(result, dict)
                    and result.get("algorithm_version") == algorithm["version"]
                    and result.get("dataset_version") == dataset["version"]
                    and result.get("system_version", "") == system_version
                ):
                    print("  Using cached result:")
                    results.append(result)
                    continue

            print("  Running new benchmark...")
            if data is None:
                # only create data if needed
                data = dataset["create"]()
                dtype = str(data.dtype)
                original_size = len(data.tobytes())
                print(f"Created dataset: shape={data.shape}, dtype={dtype}")
                print(f"Original size: {original_size:,} bytes")

                # Upload dataset to memobin if enabled
                memobin_api_key = os.environ.get("MEMOBIN_API_KEY")
                upload_enabled = os.environ.get("UPLOAD_TO_MEMOBIN") == "1"
                if memobin_api_key and upload_enabled:
                    try:
                        dataset_url = construct_dataset_url(
                            dataset["name"], dataset["version"]
                        )
                        if not exists_in_memobin(dataset_url):
                            if verbose:
                                print("  Uploading dataset to memobin...")
                            upload_to_memobin(
                                data.tobytes(),
                                dataset_url,
                                os.environ.get("MEMOBIN_USER_ID", "default"),
                                memobin_api_key,
                                content_type="application/octet-stream",
                            )
                            if verbose:
                                print("  Successfully uploaded dataset")
                    except Exception as e:
                        print(
                            f"  Warning: Failed to upload dataset to memobin: {str(e)}"
                        )

            assert data is not None
            assert isinstance(data, np.ndarray)
            assert isinstance(original_size, int)
            assert isinstance(dtype, str)

            def run_timed_trials(operation, *args) -> Tuple[float, float]:
                """Run multiple trials of an operation until total time exceeds 1 second.
                Returns (median_time, mb_per_sec)"""
                assert data is not None
                assert isinstance(data, np.ndarray)
                times = []
                total_time = 0
                array_size_mb = data.nbytes / (1024 * 1024)  # Convert to MB

                while total_time < 1.0:
                    start_time = time.perf_counter()
                    _ = operation(*args)  # Execute operation but discard result
                    trial_time = time.perf_counter() - start_time
                    times.append(trial_time)
                    total_time += trial_time

                median_time = median(times)
                mb_per_sec = array_size_mb / median_time
                return median_time, mb_per_sec

            # Measure encoding with multiple trials
            encode_time, encode_mb_per_sec = run_timed_trials(algorithm["encode"], data)
            encoded = algorithm["encode"](data)  # One final encode to get the result
            compressed_size = len(encoded)
            compression_ratio = original_size / compressed_size
            print("  Compression complete:")
            print(f"    Compressed size: {compressed_size:,} bytes")
            print(f"    Compression ratio: {compression_ratio:.2f}x")
            print(f"    Encode time: {encode_time*1000:.2f}ms")
            print(f"    Encode throughput: {encode_mb_per_sec:.2f} MB/s")

            print("  Verifying decompression...")
            # Measure decoding with multiple trials
            decode_time, decode_mb_per_sec = run_timed_trials(
                algorithm["decode"], encoded, dtype
            )
            decoded = algorithm["decode"](encoded, dtype)  # One final decode to verify
            print(f"    Decode time: {decode_time*1000:.2f}ms")
            print(f"    Decode throughput: {decode_mb_per_sec:.2f} MB/s")

            if len(data) != len(decoded):
                raise ValueError(
                    f"Decompression failed: decoded length {len(decoded)} != original length {len(data)}"
                )

            # Verify correctness
            if not np.array_equal(data, decoded):
                print(data[:100])
                print(decoded[:100])
                for j in range(len(data)):
                    if data[j] != decoded[j]:
                        print(f"Error at index {j}: {data[j]} != {decoded[j]}")
                raise ValueError(
                    f"Decompression verification failed for {alg_name} on {dataset['name']}"
                )
            print("  Verification successful!")

            # Store result
            result = {
                "dataset": dataset["name"],
                "algorithm": alg_name,
                "algorithm_version": algorithm["version"],
                "dataset_version": dataset["version"],
                "system_version": system_version,
                "compression_ratio": compression_ratio,
                "encode_time": encode_time,
                "decode_time": decode_time,
                "encode_mb_per_sec": encode_mb_per_sec,
                "decode_mb_per_sec": decode_mb_per_sec,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "array_shape": data.shape,
                "array_dtype": dtype,
                "timestamp": time.time(),
            }
            results.append(result)

            # Save result and compressed data
            os.makedirs(test_dir, exist_ok=True)
            cache_data = {"result": result}
            with open(metadata_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            with open(compressed_file, "wb") as f:
                f.write(encoded)
            print(f"  Results saved to: {test_dir}")

            # Upload to memobin if API key is set and upload is enabled
            memobin_api_key = os.environ.get("MEMOBIN_API_KEY")
            upload_enabled = os.environ.get("UPLOAD_TO_MEMOBIN") == "1"
            if memobin_api_key and upload_enabled:
                if verbose:
                    print("  Uploading results to memobin...")
                try:
                    memobin_url = construct_memobin_url(
                        alg_name,
                        dataset["name"],
                        algorithm["version"],
                        dataset["version"],
                        system_version,
                    )
                    upload_to_memobin(
                        cache_data,
                        memobin_url,
                        os.environ.get("MEMOBIN_USER_ID", "default"),
                        memobin_api_key,
                    )
                    if verbose:
                        print("  Successfully uploaded to memobin")
                except Exception as e:
                    print(f"  Warning: Failed to upload to memobin: {str(e)}")

    print("\n=== Benchmark Run Complete ===\n")

    # Collect algorithm and dataset information as lists
    algorithm_info = []
    for algorithm in algorithms:
        info = {
            "name": algorithm["name"],
            "description": algorithm.get("description", ""),
            "version": algorithm["version"],
            "tags": algorithm.get("tags", []),
        }
        if "source_file" in algorithm:
            info["source_file"] = GITHUB_ALGORITHMS_PREFIX + algorithm["source_file"]
        algorithm_info.append(info)

    dataset_info = []
    for dataset in datasets:
        info = {
            "name": dataset["name"],
            "description": dataset.get("description", ""),
            "version": dataset["version"],
            "tags": dataset.get("tags", []),
            "data_url": construct_dataset_url(dataset["name"], dataset["version"]),
        }
        if "source_file" in dataset:
            info["source_file"] = GITHUB_DATASETS_PREFIX + dataset["source_file"]
        dataset_info.append(info)

    return {"results": results, "algorithms": algorithm_info, "datasets": dataset_info}
