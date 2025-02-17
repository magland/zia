import numpy as np
import os
from .markov_reconstruct import (
    markov_reconstruct as markov_reconstruct_cpp,
)
from .markov_predict import (
    markov_predict as markov_predict_cpp,
)
from .get_run_lengths import get_run_lengths


SOURCE_FILE = "ans/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "ans.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()


def ans_encode(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

    encoded = ans_encode(x)
    if x.dtype == np.uint8:
        dtype_code = 0
    elif x.dtype == np.uint16:
        dtype_code = 1
    elif x.dtype == np.uint32:
        dtype_code = 2
    elif x.dtype == np.int16:
        dtype_code = 3
    elif x.dtype == np.int32:
        dtype_code = 4
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")
    header = (
        [
            dtype_code,
            encoded.num_bits,
            encoded.signal_length,
            encoded.state,
            len(encoded.symbol_counts),
        ]
        + [c for c in encoded.symbol_counts]
        + [v for v in encoded.symbol_values]
    )
    header_bytes = np.array(header, dtype=np.int64).tobytes()
    header_size = np.uint32(len(header_bytes))
    return header_size.tobytes() + header_bytes + encoded.bitstream


def ans0_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from simple_ans import ans_decode, EncodedSignal

    header_size = np.frombuffer(x[:4], dtype=np.uint32)[0]
    header = np.frombuffer(x[4 : 4 + header_size], dtype=np.int64)
    dtype_code, num_bits, signal_length, state, num_symbols = header[:5]
    symbol_counts = header[5 : 5 + num_symbols]
    symbol_values = header[5 + num_symbols :]
    bitstream = x[4 + header_size :]
    if dtype_code == 0:
        assert dtype == "uint8"
    elif dtype_code == 1:
        assert dtype == "uint16"
    elif dtype_code == 2:
        assert dtype == "uint32"
    elif dtype_code == 3:
        assert dtype == "int16"
    elif dtype_code == 4:
        assert dtype == "int32"
    else:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")

    encoded = EncodedSignal(
        num_bits=int(num_bits),
        signal_length=int(signal_length),
        state=int(state),
        symbol_counts=symbol_counts.astype(np.uint32),
        symbol_values=symbol_values.astype(dtype),
        bitstream=bitstream,
    )
    return ans_decode(encoded).reshape(shape)


def ans_delta_encode(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

    assert x.ndim == 1

    y = np.diff(x)
    # Encode just the differences
    encoded = ans_encode(y)
    if x.dtype == np.uint8:
        dtype_code = 0
    elif x.dtype == np.uint16:
        dtype_code = 1
    elif x.dtype == np.uint32:
        dtype_code = 2
    elif x.dtype == np.int16:
        dtype_code = 3
    elif x.dtype == np.int32:
        dtype_code = 4
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")
    # Include x[0] in the header
    header = (
        [
            dtype_code,
            encoded.num_bits,
            encoded.signal_length,
            encoded.state,
            len(encoded.symbol_counts),
            x[0],  # Store first value in header
        ]
        + [c for c in encoded.symbol_counts]
        + [v for v in encoded.symbol_values]
    )
    header_bytes = np.array(header, dtype=np.int64).tobytes()
    header_size = np.uint32(len(header_bytes))
    return header_size.tobytes() + header_bytes + encoded.bitstream


def ans_delta_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from simple_ans import ans_decode, EncodedSignal

    assert len(shape) == 1

    header_size = np.frombuffer(x[:4], dtype=np.uint32)[0]
    header = np.frombuffer(x[4 : 4 + header_size], dtype=np.int64)
    dtype_code, num_bits, signal_length, state, num_symbols, x0 = header[
        :6
    ]  # Extract x0 from header
    symbol_counts = header[6 : 6 + num_symbols]
    symbol_values = header[6 + num_symbols :]
    bitstream = x[4 + header_size :]
    if dtype_code == 0:
        assert dtype == "uint8"
    elif dtype_code == 1:
        assert dtype == "uint16"
    elif dtype_code == 2:
        assert dtype == "uint32"
    elif dtype_code == 3:
        assert dtype == "int16"
    elif dtype_code == 4:
        assert dtype == "int32"
    else:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")

    encoded = EncodedSignal(
        num_bits=int(num_bits),
        signal_length=int(signal_length),
        state=int(state),
        symbol_counts=symbol_counts.astype(np.uint32),
        symbol_values=symbol_values.astype(dtype),
        bitstream=bitstream,
    )
    # Decode the differences
    diffs = ans_decode(encoded)
    # Insert x0 at the beginning and cumulatively sum the differences
    return np.cumsum(np.insert(diffs, 0, x0))


def ans_markov_encode(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

    assert x.ndim == 1

    coeffs, initial, resid = markov_predict_cpp(x, M=6, num_training_samples=10000)
    # Encode just the differences
    encoded = ans_encode(resid)
    if x.dtype == np.uint8:
        dtype_code = 0
    elif x.dtype == np.uint16:
        dtype_code = 1
    elif x.dtype == np.uint32:
        dtype_code = 2
    elif x.dtype == np.int16:
        dtype_code = 3
    elif x.dtype == np.int32:
        dtype_code = 4
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")
    # Include x[0] in the header
    header = (
        [
            dtype_code,
            encoded.num_bits,
            encoded.signal_length,
            encoded.state,
            len(encoded.symbol_counts),
            len(coeffs),
            len(initial),
        ]
        + [c for c in encoded.symbol_counts]
        + [v for v in encoded.symbol_values]
        + [c for c in coeffs]
        + [v for v in initial]
    )
    header_bytes = np.array(header, dtype=np.float64).tobytes()
    header_size = np.uint32(len(header_bytes))
    return header_size.tobytes() + header_bytes + encoded.bitstream


def ans_markov_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from simple_ans import ans_decode, EncodedSignal

    assert len(shape) == 1

    header_size = np.frombuffer(x[:4], dtype=np.uint32)[0]
    header = np.frombuffer(x[4 : 4 + header_size], dtype=np.float64)
    dtype_code, num_bits, signal_length, state, num_symbols, num_coeffs, num_initial = (
        header[:7]
    )
    dtype_code = int(dtype_code)
    num_bits = int(num_bits)
    signal_length = int(signal_length)
    state = int(state)
    num_symbols = int(num_symbols)
    num_coeffs = int(num_coeffs)
    num_initial = int(num_initial)

    pos = 7
    symbol_counts = header[pos : pos + num_symbols]
    pos += num_symbols
    symbol_values = header[pos : pos + num_symbols]
    pos += num_symbols
    coeffs = header[pos : pos + num_coeffs].astype(np.float32)
    pos += num_coeffs
    initial = header[pos : pos + num_initial].astype(dtype)
    pos += num_initial
    bitstream = x[4 + header_size :]
    if dtype_code == 0:
        assert dtype == "uint8"
    elif dtype_code == 1:
        assert dtype == "uint16"
    elif dtype_code == 2:
        assert dtype == "uint32"
    elif dtype_code == 3:
        assert dtype == "int16"
    elif dtype_code == 4:
        assert dtype == "int32"
    else:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")

    encoded = EncodedSignal(
        num_bits=int(num_bits),
        signal_length=int(signal_length),
        state=int(state),
        symbol_counts=symbol_counts.astype(np.uint32),
        symbol_values=symbol_values.astype(dtype),
        bitstream=bitstream,
    )

    resid = ans_decode(encoded)
    output = markov_reconstruct_cpp(coeffs, initial, resid)
    return output


def ans_markov_sparse_encode(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

    assert x.ndim == 1

    run_lengths = get_run_lengths(x)

    non_zero_arrays = []
    array_pos = 0
    i = 0
    while i < len(run_lengths):
        non_zero_len = int(run_lengths[i])
        if non_zero_len > 0:
            non_zero_arrays.append(x[array_pos : array_pos + non_zero_len])
            array_pos += non_zero_len
        i += 1
        if i < len(run_lengths):
            zero_len = int(run_lengths[i])
            array_pos += zero_len
            i += 1

    non_zero_data = np.concatenate(non_zero_arrays)
    assert len(non_zero_data) == np.sum(run_lengths[::2])
    coeffs, initial, resid = markov_predict_cpp(
        non_zero_data, M=6, num_training_samples=10000
    )
    encoded = ans_encode(resid)

    if x.dtype == np.uint8:
        dtype_code = 0
    elif x.dtype == np.uint16:
        dtype_code = 1
    elif x.dtype == np.uint32:
        dtype_code = 2
    elif x.dtype == np.int16:
        dtype_code = 3
    elif x.dtype == np.int32:
        dtype_code = 4
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")

    if run_lengths.dtype == np.uint8:
        run_length_dtype_code = 0
    elif run_lengths.dtype == np.uint16:
        run_length_dtype_code = 1
    elif run_lengths.dtype == np.uint32:
        run_length_dtype_code = 2
    else:
        raise ValueError(f"Unsupported run length dtype: {run_lengths.dtype}")

    header = (
        [
            dtype_code,
            encoded.num_bits,
            len(encoded.bitstream),
            encoded.signal_length,
            encoded.state,
            len(encoded.symbol_counts),
            len(coeffs),
            len(initial),
            run_length_dtype_code,
            len(run_lengths),
        ]
        + [c for c in encoded.symbol_counts]
        + [v for v in encoded.symbol_values]
        + [c for c in coeffs]
        + [v for v in initial]
    )
    header_bytes = np.array(header, dtype=np.float64).tobytes()
    header_size = np.uint32(len(header_bytes))

    return (
        header_size.tobytes() + header_bytes + encoded.bitstream + run_lengths.tobytes()
    )


def ans_markov_sparse_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from simple_ans import ans_decode, EncodedSignal

    assert len(shape) == 1

    header_size = np.frombuffer(x[:4], dtype=np.uint32)[0]
    header = np.frombuffer(x[4 : 4 + header_size], dtype=np.float64)
    (
        dtype_code,
        num_bits,
        bitstream_length,
        signal_length,
        state,
        num_symbols,
        num_coeffs,
        num_initial,
        run_length_dtype_code,
        num_run_lengths,
    ) = header[:10]
    dtype_code = int(dtype_code)
    num_bits = int(num_bits)
    bitstream_length = int(bitstream_length)
    signal_length = int(signal_length)
    state = int(state)
    num_symbols = int(num_symbols)
    num_coeffs = int(num_coeffs)
    num_initial = int(num_initial)
    run_length_dtype_code = int(run_length_dtype_code)
    num_run_lengths = int(num_run_lengths)

    pos = 10
    symbol_counts = header[pos : pos + num_symbols]
    pos += num_symbols
    symbol_values = header[pos : pos + num_symbols]
    pos += num_symbols
    coeffs = header[pos : pos + num_coeffs].astype(np.float32)
    pos += num_coeffs
    initial = header[pos : pos + num_initial].astype(dtype)
    pos += num_initial

    bitstream_end = 4 + header_size + bitstream_length
    bitstream = x[4 + header_size : bitstream_end]

    # Get run lengths from the remaining bytes
    if run_length_dtype_code == 0:
        run_lengths = np.frombuffer(x[bitstream_end:], dtype=np.uint8)
    elif run_length_dtype_code == 1:
        run_lengths = np.frombuffer(x[bitstream_end:], dtype=np.uint16)
    elif run_length_dtype_code == 2:
        run_lengths = np.frombuffer(x[bitstream_end:], dtype=np.uint32)
    else:
        raise ValueError(f"Unsupported run length dtype code: {run_length_dtype_code}")

    if len(run_lengths) != num_run_lengths:
        raise ValueError(
            f"Expected {num_run_lengths} run lengths, got {len(run_lengths)}"
        )

    if dtype_code == 0:
        assert dtype == "uint8"
    elif dtype_code == 1:
        assert dtype == "uint16"
    elif dtype_code == 2:
        assert dtype == "uint32"
    elif dtype_code == 3:
        assert dtype == "int16"
    elif dtype_code == 4:
        assert dtype == "int32"
    else:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")

    encoded = EncodedSignal(
        num_bits=int(num_bits),
        signal_length=int(signal_length),
        state=int(state),
        symbol_counts=symbol_counts.astype(np.uint32),
        symbol_values=symbol_values.astype(dtype),
        bitstream=bitstream,
    )

    # Decode residuals and reconstruct non-zero data
    resid = ans_decode(encoded)
    non_zero_data = markov_reconstruct_cpp(coeffs, initial, resid)

    assert len(non_zero_data) == np.sum(run_lengths[::2])

    # Reconstruct full array using run lengths
    non_zero_pos = 0  # Position in non_zero_data
    i = 0
    segments = []
    while i < len(run_lengths):
        non_zero_len = int(run_lengths[i])
        if non_zero_len > 0:
            # print(f'--- b non_zero_len={non_zero_len} non_zero_pos={non_zero_pos} pos={pos} len(non_zero_data)={len(non_zero_data)} len(output)={len(output)}')
            # print('---- y')
            segment = non_zero_data[non_zero_pos : non_zero_pos + non_zero_len]
            assert len(segment) == non_zero_len
            segments.append(segment)
            non_zero_pos += non_zero_len
        i += 1
        if i < len(run_lengths):
            segments.append(np.zeros(int(run_lengths[i]), dtype=non_zero_data.dtype))
            i += 1
    output = np.concatenate(segments)

    return output


algorithms = [
    {
        "name": "ANS",
        "version": "3",
        "encode": lambda x: ans_encode(x),
        "decode": lambda x, dtype, shape: ans0_decode(x, dtype, shape),
        "description": "ANS compression via simple_ans for efficient data compression.",
        "tags": ["ANS", "integer"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "ANS-delta",
        "version": "3",
        "encode": lambda x: ans_delta_encode(x),
        "decode": lambda x, dtype, shape: ans_delta_decode(x, dtype, shape),
        "description": "ANS compression via simple_ans with delta encoding for improved compression of sequential data.",
        "tags": ["ANS", "integer", "delta_encoding", "1d"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "ANS-markov",
        "version": "6",
        "encode": lambda x: ans_markov_encode(x),
        "decode": lambda x, dtype, shape: ans_markov_decode(x, dtype, shape),
        "description": "ANS compression via simple_ans with Markov prediction for exploiting temporal correlations in the data.",
        "tags": ["ANS", "integer", "markov_prediction", "1d"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "ANS-markov-zrle",
        "version": "6",
        "encode": lambda x: ans_markov_sparse_encode(x),
        "decode": lambda x, dtype, shape: ans_markov_sparse_decode(x, dtype, shape),
        "description": "ANS compression via simple_ans with Markov prediction and zero run-length encoding for sparse data.",
        "tags": ["ANS", "integer", "markov_prediction", "zero_rle", "1d"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
]
