import { useParams } from "react-router-dom";
import { Algorithm as AlgorithmType, BenchmarkData } from "../types";
import { BenchmarkCharts } from "../components/benchmark/charts/BenchmarkCharts";
import { useBenchmarkChartData } from "../hooks/useBenchmarkChartData";
import { BenchmarkTable } from "../components/benchmark/table/BenchmarkTable";

interface AlgorithmProps {
  algorithms: AlgorithmType[];
  benchmarkData: BenchmarkData | null;
}

function Algorithm({ algorithms, benchmarkData }: AlgorithmProps) {
  const { algorithmName } = useParams<{ algorithmName: string }>();
  const algorithm = algorithms.find((a) => a.name === algorithmName);
  const chartData = useBenchmarkChartData(
    benchmarkData?.results || [],
    null,
    algorithm?.name || null,
  );

  if (!algorithm) {
    return <div>Algorithm not found</div>;
  }

  return (
    <div>
      <h1
        style={{
          fontSize: "2rem",
          fontWeight: "bold",
          color: "#333",
          marginBottom: "1rem",
        }}
      >
        {algorithm.name}
      </h1>
      <div>
        <div style={{ marginBottom: "1.5rem" }}>
          <p style={{ fontSize: "0.9rem", lineHeight: "1.5" }}>
            {algorithm.description}
          </p>
        </div>
        <div
          style={{
            marginBottom: "1.5rem",
            display: "flex",
            gap: "2rem",
            flexWrap: "wrap",
          }}
        >
          <div>
            <span style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
              Version:{" "}
            </span>
            <span style={{ fontSize: "0.9rem" }}>{algorithm.version}</span>
          </div>
          <div>
            <span style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
              Tags:{" "}
            </span>
            {algorithm.tags.map((tag) => (
              <span
                key={tag}
                style={{
                  display: "inline-block",
                  backgroundColor: "#e1e1e1",
                  padding: "2px 6px",
                  borderRadius: "3px",
                  margin: "2px",
                  fontSize: "0.8rem",
                }}
              >
                {tag}
              </span>
            ))}
          </div>
          {algorithm.source_file && (
            <div>
              <span style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                Source:{" "}
              </span>
              <a
                href={algorithm.source_file}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "#0066cc",
                  textDecoration: "none",
                  padding: "2px 6px",
                  backgroundColor: "#f0f0f0",
                  borderRadius: "4px",
                  fontSize: "0.9rem",
                }}
              >
                View
              </a>
            </div>
          )}
        </div>
        {benchmarkData && (
          <>
            <div style={{ marginBottom: "1.5rem" }}>
              <h2
                style={{
                  fontSize: "1.2rem",
                  fontWeight: "bold",
                  marginBottom: "0.5rem",
                }}
              >
                Benchmark Results
              </h2>
              <BenchmarkCharts chartData={chartData} />
            </div>
            <div style={{ marginBottom: "1.5rem" }}>
              <BenchmarkTable
                results={benchmarkData.results.filter(
                  (result) => result.algorithm === algorithm.name,
                )}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Algorithm;
