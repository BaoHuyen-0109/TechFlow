"use strict";

document.querySelectorAll("[data-category-chart]").forEach((root) => {
  const container = root.querySelector("[data-chart-container]");
  const status = root.querySelector("[data-chart-status]");
  const canvas = root.querySelector("canvas");
  try {
    const rows = JSON.parse(root.dataset.chartData);
    status.textContent = "Đang hiển thị biểu đồ…";
    container.hidden = false;
    new Chart(canvas, {
      type: "bar",
      data: {
        labels: rows.map((row) => row.name),
        datasets: [{ label: "Sản phẩm hoạt động", data: rows.map((row) => row.count),
          backgroundColor: "#6a83e9", hoverBackgroundColor: "#4265da", borderRadius: 5, maxBarThickness: 23 }],
      },
      options: {
        indexAxis: "y", responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false }, tooltip: { displayColors: false } },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0, color: "#8c99af" }, grid: { color: "#eef1f7" }, border: { display: false } },
          y: { ticks: { color: "#72819b", font: { size: 11 }, callback: function(value) {
            const label = this.getLabelForValue(value);
            return label.length > 21 ? label.slice(0, 20) + "…" : label;
          } }, grid: { display: false }, border: { display: false } },
        },
      },
    });
    root.querySelector("details").open = false;
    status.textContent = "Di chuột hoặc mở bảng để xem số liệu chi tiết.";
    root.dataset.chartReady = "true";
  } catch {
    container.hidden = true;
    status.textContent = "Chưa thể hiển thị biểu đồ. Số liệu vẫn có trong bảng bên dưới.";
    root.querySelector("details").open = true;
  }
});
