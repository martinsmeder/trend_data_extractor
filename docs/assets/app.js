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
const explorerCopyNode = document.querySelector("#explorer-copy");
const sourceSelectNode = document.querySelector("#source-select");
const metricSelectNode = document.querySelector("#metric-select");
const seriesSelectNode = document.querySelector("#series-select");
const selectedSourceNode = document.querySelector("#selected-source");
const selectedMetricNode = document.querySelector("#selected-metric");
const selectedSeriesNode = document.querySelector("#selected-series");
const chartCanvasNode = document.querySelector("#chart-preview");

if (statusNode) {
  statusNode.textContent = window.Chart ? "Chart.js ready" : "Chart.js failed to load";
}

const appState = {
  dataset: null,
  series: [],
  metrics: [],
  sources: [],
  selectedSource: "",
  selectedMetric: "",
  selectedSeriesId: "",
};
let chartInstance = null;

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
    initializeExplorer();
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

  if (explorerCopyNode) {
    explorerCopyNode.textContent =
      "Choose a source, metric, and series. The controls stay narrow and ordered so the first interaction remains obvious.";
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

  if (explorerCopyNode) {
    explorerCopyNode.textContent =
      "The chart explorer is unavailable because the dataset could not be loaded.";
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

function initializeExplorer() {
  if (!sourceSelectNode || !metricSelectNode || !seriesSelectNode) {
    return;
  }

  sourceSelectNode.disabled = false;
  metricSelectNode.disabled = false;
  seriesSelectNode.disabled = false;

  populateSourceOptions();

  appState.selectedSource = appState.sources[0] || "";
  sourceSelectNode.value = appState.selectedSource;

  populateMetricOptions();
  appState.selectedMetric = getAvailableMetrics(appState.selectedSource)[0] || "";
  metricSelectNode.value = appState.selectedMetric;

  populateSeriesOptions();
  appState.selectedSeriesId = getVisibleSeries()[0]?.id || "";
  seriesSelectNode.value = appState.selectedSeriesId;

  sourceSelectNode.addEventListener("change", handleSourceChange);
  metricSelectNode.addEventListener("change", handleMetricChange);
  seriesSelectNode.addEventListener("change", handleSeriesChange);

  updateSelectionSummary();
}

function handleSourceChange(event) {
  appState.selectedSource = event.target.value;
  const nextMetric = getAvailableMetrics(appState.selectedSource)[0] || "";

  populateMetricOptions();
  appState.selectedMetric = nextMetric;
  metricSelectNode.value = nextMetric;

  populateSeriesOptions();
  appState.selectedSeriesId = getVisibleSeries()[0]?.id || "";
  seriesSelectNode.value = appState.selectedSeriesId;

  updateSelectionSummary();
}

function handleMetricChange(event) {
  appState.selectedMetric = event.target.value;
  populateSeriesOptions();
  appState.selectedSeriesId = getVisibleSeries()[0]?.id || "";
  seriesSelectNode.value = appState.selectedSeriesId;
  updateSelectionSummary();
}

function handleSeriesChange(event) {
  appState.selectedSeriesId = event.target.value;
  updateSelectionSummary();
}

function populateSourceOptions() {
  replaceSelectOptions(
    sourceSelectNode,
    appState.sources.map((source) => ({
      value: source,
      label: source.toUpperCase(),
    })),
  );
}

function populateMetricOptions() {
  replaceSelectOptions(
    metricSelectNode,
    getAvailableMetrics(appState.selectedSource).map((metric) => ({
      value: metric,
      label: metric,
    })),
  );
}

function populateSeriesOptions() {
  replaceSelectOptions(
    seriesSelectNode,
    getVisibleSeries().map((series) => ({
      value: series.id,
      label: series.label,
    })),
  );
}

function replaceSelectOptions(selectNode, options) {
  if (!selectNode) {
    return;
  }

  selectNode.replaceChildren(
    ...options.map((option) => {
      const element = document.createElement("option");
      element.value = option.value;
      element.textContent = option.label;
      return element;
    }),
  );
}

function getAvailableMetrics(source) {
  return [...new Set(
    appState.series
      .filter((series) => series.source === source)
      .map((series) => series.metric),
  )].sort();
}

function getVisibleSeries() {
  return appState.series.filter((series) => {
    return (
      series.source === appState.selectedSource &&
      series.metric === appState.selectedMetric
    );
  });
}

function getSelectedSeries() {
  return appState.series.find((series) => series.id === appState.selectedSeriesId) || null;
}

function updateSelectionSummary() {
  const selectedSeries = getSelectedSeries();

  if (selectedSourceNode) {
    selectedSourceNode.textContent = appState.selectedSource
      ? appState.selectedSource.toUpperCase()
      : "None";
  }

  if (selectedMetricNode) {
    selectedMetricNode.textContent = appState.selectedMetric || "None";
  }

  if (selectedSeriesNode) {
    selectedSeriesNode.textContent = selectedSeries?.label || "None";
  }

  if (chartPlaceholderNode) {
    chartPlaceholderNode.textContent = selectedSeries
      ? `Selected series: ${selectedSeries.label}. Hover the line to inspect yearly values.`
      : "No series is currently selected.";
  }

  updateChartForSelection(selectedSeries);
}

function updateChartForSelection(selectedSeries) {
  if (!window.Chart || !chartCanvasNode) {
    return;
  }

  if (!chartInstance) {
    chartInstance = createChart(chartCanvasNode);
  }

  const observations = selectedSeries?.observations || [];
  const labels = observations.map((observation) => String(observation.year));
  const values = observations.map((observation) => observation.value);
  const valueTexts = observations.map((observation) => observation.valueText);

  chartInstance.data.labels = labels;
  chartInstance.data.datasets[0].label = selectedSeries?.label || "Series";
  chartInstance.data.datasets[0].data = values;
  chartInstance.data.datasets[0].valueTexts = valueTexts;
  chartInstance.options.plugins.title.text = selectedSeries?.label || "Selected series";
  chartInstance.options.plugins.subtitle.text = selectedSeries
    ? buildChartSubtitle(selectedSeries)
    : "";
  chartInstance.options.scales.y.title.text = selectedSeries?.unit || "";
  chartInstance.update();
}

function createChart(canvas) {
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Series",
          data: [],
          valueTexts: [],
          borderColor: "#0f6a73",
          backgroundColor: "rgba(15, 106, 115, 0.12)",
          borderWidth: 3,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#0f6a73",
          tension: 0.25,
          fill: false,
          spanGaps: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: {
        mode: "nearest",
        intersect: false,
      },
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: "Selected series",
          color: "#1d1d1b",
          font: {
            size: 16,
            weight: "700",
          },
          padding: {
            bottom: 8,
          },
        },
        subtitle: {
          display: true,
          text: "",
          color: "#60574b",
          font: {
            size: 12,
          },
          padding: {
            bottom: 12,
          },
        },
        tooltip: {
          enabled: true,
          callbacks: {
            title(items) {
              return items[0] ? `Year ${items[0].label}` : "";
            },
            label(context) {
              const textValue = context.dataset.valueTexts?.[context.dataIndex];
              if (textValue) {
                return `Value: ${textValue}`;
              }
              if (typeof context.parsed.y === "number") {
                return `Value: ${formatValue(context.parsed.y)}`;
              }
              return "Value: Not available";
            },
          },
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Year",
            color: "#60574b",
            font: {
              size: 12,
              weight: "700",
            },
          },
          grid: {
            display: false,
          },
          ticks: {
            color: "#60574b",
          },
        },
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "",
            color: "#60574b",
            font: {
              size: 12,
              weight: "700",
            },
          },
          ticks: {
            color: "#60574b",
            callback(value) {
              return formatValue(value);
            },
          },
          grid: {
            color: "rgba(96, 87, 75, 0.14)",
          },
        },
      },
    },
  });
}

function buildChartSubtitle(series) {
  const parts = [String(series.source).toUpperCase()];
  if (series.unit) {
    parts.push(series.unit);
  }
  return parts.join(" · ");
}

function formatValue(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "";
  }

  if (Number.isInteger(value)) {
    return new Intl.NumberFormat("en-US").format(value);
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

loadDataset();
