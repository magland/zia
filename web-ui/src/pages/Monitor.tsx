import { useEffect, useState } from "react";
import axios from "axios";

interface BenchmarkStatus {
  current_dataset: string;
  current_algorithm: string;
  completed_count: number;
  total_count: number;
  progress_percentage: number;
  elapsed_time: number;
  last_update: string;
  completed_benchmarks: Array<{
    dataset: string;
    algorithm: string;
    compression_ratio: number;
    encode_time: number;
    decode_time: number;
  }>;
}

export default function Monitor() {
  const [status, setStatus] = useState<BenchmarkStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(
          "https://tempory.net/f/memobin/benchmark_status/current.json",
        );
        setStatus(response.data);
        setError(null);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Failed to fetch status";
        setError(message);
        console.error("Error fetching benchmark status:", error);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately and then every 30 seconds
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div>Loading benchmark status...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!status) {
    return <div>No active benchmark run found.</div>;
  }

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Benchmark Progress</h1>

      <div style={{ marginBottom: "20px" }}>
        <h2>Current Status</h2>
        <div
          style={{
            border: "1px solid #eee",
            padding: "20px",
            borderRadius: "8px",
            backgroundColor: "#f9f9f9",
          }}
        >
          <p>
            <strong>Current Dataset:</strong> {status.current_dataset}
          </p>
          <p>
            <strong>Current Algorithm:</strong> {status.current_algorithm}
          </p>
          <p>
            <strong>Progress:</strong> {status.completed_count} /{" "}
            {status.total_count} ({status.progress_percentage.toFixed(1)}%)
          </p>
          <p>
            <strong>Elapsed Time:</strong> {formatTime(status.elapsed_time)}
          </p>
          <p>
            <strong>Last Update:</strong>{" "}
            {new Date(status.last_update).toLocaleString()}
          </p>

          <div style={{ marginTop: "10px" }}>
            <div
              style={{
                width: "100%",
                height: "20px",
                backgroundColor: "#eee",
                borderRadius: "10px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${status.progress_percentage}%`,
                  height: "100%",
                  backgroundColor: "#4CAF50",
                  transition: "width 0.5s ease-in-out",
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2>Completed Benchmarks</h2>
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              marginTop: "10px",
            }}
          >
            <thead>
              <tr style={{ backgroundColor: "#f5f5f5" }}>
                <th
                  style={{
                    padding: "12px",
                    textAlign: "left",
                    borderBottom: "2px solid #ddd",
                  }}
                >
                  Dataset
                </th>
                <th
                  style={{
                    padding: "12px",
                    textAlign: "left",
                    borderBottom: "2px solid #ddd",
                  }}
                >
                  Algorithm
                </th>
                <th
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    borderBottom: "2px solid #ddd",
                  }}
                >
                  Compression Ratio
                </th>
                <th
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    borderBottom: "2px solid #ddd",
                  }}
                >
                  Encode Time (ms)
                </th>
                <th
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    borderBottom: "2px solid #ddd",
                  }}
                >
                  Decode Time (ms)
                </th>
              </tr>
            </thead>
            <tbody>
              {status.completed_benchmarks.map((benchmark, index) => (
                <tr
                  key={index}
                  style={{
                    backgroundColor: index % 2 === 0 ? "white" : "#fafafa",
                  }}
                >
                  <td
                    style={{ padding: "12px", borderBottom: "1px solid #ddd" }}
                  >
                    {benchmark.dataset}
                  </td>
                  <td
                    style={{ padding: "12px", borderBottom: "1px solid #ddd" }}
                  >
                    {benchmark.algorithm}
                  </td>
                  <td
                    style={{
                      padding: "12px",
                      textAlign: "right",
                      borderBottom: "1px solid #ddd",
                    }}
                  >
                    {benchmark.compression_ratio.toFixed(2)}x
                  </td>
                  <td
                    style={{
                      padding: "12px",
                      textAlign: "right",
                      borderBottom: "1px solid #ddd",
                    }}
                  >
                    {(benchmark.encode_time * 1000).toFixed(2)}
                  </td>
                  <td
                    style={{
                      padding: "12px",
                      textAlign: "right",
                      borderBottom: "1px solid #ddd",
                    }}
                  >
                    {(benchmark.decode_time * 1000).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
