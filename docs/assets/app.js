const statusNode = document.querySelector("#chartjs-status");

if (statusNode) {
  statusNode.textContent = window.Chart ? "Chart.js ready" : "Chart.js failed to load";
}
