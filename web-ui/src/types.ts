export interface BenchmarkResult {
  dataset: string;
  algorithm: string;
  algorithm_version: string;
  dataset_version: string;
  system_version: string;
  compression_ratio: number;
  encode_time: number;
  decode_time: number;
  encode_mb_per_sec: number;
  decode_mb_per_sec: number;
  original_size: number;
  compressed_size: number;
  array_shape: number[];
  array_dtype: string;
  timestamp: number;
}

export interface BenchmarkData {
  results: BenchmarkResult[];
}
