const statusNode = document.querySelector("#chartjs-status");
const datasetStatusNode = document.querySelector("#dataset-status");
const datasetCopyNode = document.querySelector("#dataset-copy");
const chartPlaceholderNode = document.querySelector("#chart-placeholder");
const statDatasetIdNode = document.querySelector("#stat-dataset-id");
const statSeriesCountNode = document.querySelector("#stat-series-count");
const statSourceCountNode = document.querySelector("#stat-source-count");
const statMetricCountNode = document.querySelector("#stat-metric-count");
const overviewDescriptionNode = document.querySelector("#overview-description");
const overviewSourcesNode = document.querySelector("#overview-sources");

if (statusNode) {
  statusNode.textContent = window.Chart ? "Chart.js ready" : "Chart.js failed to load";
}

const appState = {
  dataset: null,
  series: [],
  metrics: [],
  sources: [],
};

async function loadDataset() {
  try {
    setLoadingState();

    const response = await fetch("data/sweden_dataset.json");
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    const dataset = await response.json();
    const parsed = parseDataset(dataset);

    appState.dataset = dataset;
    appState.series = parsed.series;
    appState.metrics = parsed.metrics;
    appState.sources = parsed.sources;

    setSuccessState(parsed);
  } catch (error) {
    setErrorState(error);
  }
}

function parseDataset(dataset) {
  const rawSeries = Array.isArray(dataset?.series) ? dataset.series : [];
  const series = rawSeries.map((item, index) => normalizeSeries(item, index));
  const metrics = [...new Set(series.map((item) => item.metric))].sort();
  const sources = [...new Set(series.map((item) => item.source))].sort();

  return { series, metrics, sources };
}

function normalizeSeries(item, index) {
  const observations = Array.isArray(item?.observations) ? item.observations : [];
  const normalizedObservations = observations
    .map((observation) => normalizeObservation(observation))
    .sort((left, right) => left.year - right.year);

  return {
    id: `${item.source || "unknown"}:${item.metric || "series"}:${index}`,
    metric: item.metric || "unknown_metric",
    label: item.label || "Untitled series",
    source: item.source || "unknown",
    url: item.url || "",
    unit: item.unit || "",
    dimensions: item.dimensions || {},
    notes: Array.isArray(item.notes) ? item.notes : [],
    observations: normalizedObservations,
    points: normalizedObservations.map((observation) => ({
      x: observation.year,
      y: observation.value,
      valueText: observation.valueText,
    })),
  };
}

function normalizeObservation(observation) {
  return {
    year: Number(observation.year),
    value: typeof observation.value === "number" ? observation.value : null,
    valueText:
      typeof observation.value_text === "string"
        ? observation.value_text
        : typeof observation.valueText === "string"
          ? observation.valueText
          : null,
  };
}

function setLoadingState() {
  if (datasetStatusNode) {
    datasetStatusNode.textContent = "Loading dataset";
    datasetStatusNode.className = "status-pill status-neutral";
  }
}

function setSuccessState(parsed) {
  if (datasetStatusNode) {
    datasetStatusNode.textContent = "Dataset loaded";
    datasetStatusNode.className = "status-pill status-success";
  }

  if (datasetCopyNode && appState.dataset) {
    datasetCopyNode.textContent =
      `${appState.dataset.title} loaded successfully from the hosted JSON file. ` +
      "Series are now normalized into chart-ready points and selection lists.";
  }

  if (overviewDescriptionNode && appState.dataset) {
    overviewDescriptionNode.textContent =
      `${appState.dataset.description} ` +
      "Use the chart explorer below to inspect one normalized time series at a time.";
  }

  if (overviewSourcesNode) {
    overviewSourcesNode.replaceChildren(
      ...parsed.sources.map((source) => buildSourceChip(source)),
    );
  }

  if (chartPlaceholderNode) {
    chartPlaceholderNode.textContent =
      `${parsed.series.length} series are ready for chart rendering. ` +
      "The next implementation step will bind these parsed records to chart and control UI.";
  }

  if (statDatasetIdNode && appState.dataset) {
    statDatasetIdNode.textContent = appState.dataset.dataset_id || "Unknown";
  }

  if (statSeriesCountNode) {
    statSeriesCountNode.textContent = String(parsed.series.length);
  }

  if (statSourceCountNode) {
    statSourceCountNode.textContent = String(parsed.sources.length);
  }

  if (statMetricCountNode) {
    statMetricCountNode.textContent = String(parsed.metrics.length);
  }
}

function setErrorState(error) {
  if (datasetStatusNode) {
    datasetStatusNode.textContent = "Dataset failed";
    datasetStatusNode.className = "status-pill status-error";
  }

  if (datasetCopyNode) {
    datasetCopyNode.textContent =
      "The hosted dataset could not be loaded. Check that docs/data/sweden_dataset.json exists and is served by the current web root.";
  }

  if (overviewDescriptionNode) {
    overviewDescriptionNode.textContent =
      "The dataset overview could not be loaded because the hosted JSON file is unavailable.";
  }

  if (overviewSourcesNode) {
    overviewSourcesNode.replaceChildren(buildSourceChip("Unavailable"));
  }

  if (chartPlaceholderNode) {
    chartPlaceholderNode.textContent = `Loading error: ${error.message}`;
  }

  if (statDatasetIdNode) {
    statDatasetIdNode.textContent = "Error";
  }
}

function buildSourceChip(source) {
  const chip = document.createElement("span");
  chip.className = "source-chip";
  chip.textContent = String(source).toUpperCase();
  return chip;
}

loadDataset();
