"use strict";

// Progressive enhancement: the named field remains the canonical Decimal value.
// The visible field uses Vietnamese separators. Never convert money to Number.
document.querySelectorAll("[data-vnd-input]").forEach((canonical) => {
  const display = canonical.cloneNode(false);
  display.type = "text";
  display.removeAttribute("name");
  display.removeAttribute("step");
  display.removeAttribute("data-vnd-input");
  display.setAttribute("inputmode", "decimal");
  display.setAttribute("data-vnd-display", "");
  display.classList.add("catalog-money-input");
  const help = document.getElementById(canonical.id + "-help");
  const errors = document.getElementById(canonical.id + "-errors");
  const clientError = document.createElement("div");
  clientError.className = "catalog-field-error";
  clientError.setAttribute("aria-live", "polite");
  errors.append(clientError);
  function format(value) {
    if (!/^-?\d+(?:\.\d+)?$/.test(value)) return value;
    const [integer, fraction] = value.split(".");
    return integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (fraction === undefined ? "" : "," + fraction);
  }
  function parse(value) {
    const trimmed = value.trim();
    if (trimmed === "") return "";
    if (!/^-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/.test(trimmed)) return null;
    return trimmed.replaceAll(".", "").replace(",", ".");
  }
  display.value = format(canonical.value);
  canonical.type = "hidden";
  canonical.id += "-canonical";
  canonical.classList.remove("is-invalid");
  canonical.removeAttribute("aria-invalid");
  canonical.before(display);
  help.textContent = "Định dạng Việt Nam: 15.000.000,50 hoặc 15000000,50. Dấu phẩy cho phần thập phân; tối đa 2 chữ số.";
  function sync(showError) {
    const value = parse(display.value);
    canonical.value = value === null ? "" : value;
    clientError.textContent = value === null && showError ? "Nhập giá theo định dạng Việt Nam, ví dụ 15.000.000,50." : "";
    if (value === null && showError) {
      display.classList.add("is-invalid");
      display.setAttribute("aria-invalid", "true");
    }
    return value;
  }
  display.addEventListener("input", () => {
    display.classList.remove("is-invalid");
    display.setAttribute("aria-invalid", "false");
    clientError.textContent = "";
    sync(false);
  });
  display.addEventListener("blur", () => {
    const value = sync(true);
    if (value !== null) display.value = format(value);
  });
  canonical.form.addEventListener("submit", (event) => {
    if (sync(true) === null) {
      event.preventDefault();
      if (!canonical.form.querySelector("[data-vnd-display].is-invalid:focus")) display.focus();
    }
  });
});

document.querySelectorAll("[data-ui-tooltip]").forEach((element) => {
  new bootstrap.Tooltip(element, { trigger: "hover focus", html: false, animation: false });
});

document.querySelectorAll("[data-image-preview]").forEach((preview) => {
  const image = preview.querySelector("[data-preview-image]");
  const status = preview.querySelector("[data-preview-status]");
  const placeholder = preview.dataset.imagePlaceholder;
  let showingPhoto = false;
  let timer;
  function fallback(message) {
    showingPhoto = false;
    image.src = placeholder;
    image.alt = "Ảnh mặc định";
    if (status) status.textContent = message;
    preview.removeAttribute("aria-busy");
  }
  function update(value) {
    const source = value.trim();
    if (!source) return fallback("Chưa có ảnh. Đang dùng ảnh mặc định.");
    try {
      const url = new URL(source);
      if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || source.length > 500 || /[\s\u0000-\u001f\u007f]/.test(source)) throw new Error();
      showingPhoto = true;
      preview.setAttribute("aria-busy", "true");
      if (status) status.textContent = "Đang tải ảnh xem trước…";
      image.alt = "Ảnh sản phẩm";
      image.src = url.href;
    } catch {
      fallback("URL chưa hợp lệ. Đang dùng ảnh mặc định.");
    }
  }
  image.addEventListener("load", () => {
    if (!showingPhoto) return;
    preview.removeAttribute("aria-busy");
    if (status) status.textContent = "Ảnh xem trước";
  });
  image.addEventListener("error", () => {
    if (showingPhoto) fallback("Không tải được ảnh. Đang dùng ảnh mặc định.");
  });
  const input = document.getElementById(preview.dataset.imageInput || "");
  input?.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => update(input.value), 350);
  });
  update(input ? input.value : preview.dataset.imageSource || "");
});

document.querySelector(".catalog-edit .is-invalid")?.focus();

document.querySelector("#delete-modal")?.addEventListener("show.bs.modal", (event) => {
  document.querySelectorAll("[data-ui-tooltip]").forEach((element) => bootstrap.Tooltip.getInstance(element)?.hide());
  const trigger = event.relatedTarget;
  const modal = event.currentTarget;
  modal.querySelector("[data-delete-name]").textContent = trigger.dataset.recordName;
  modal.querySelector("[data-delete-form]").action = trigger.dataset.deleteUrl;
});

document.querySelectorAll("[data-sidebar-collapse]").forEach((button) => {
  button.addEventListener("click", () => {
    const collapsed = document.body.classList.toggle("workspace-collapsed");
    button.setAttribute("aria-expanded", String(!collapsed));
    button.setAttribute("aria-label", collapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng");
  });
});

document.querySelectorAll("[data-password-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = button.parentElement.querySelector("input");
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    button.setAttribute("aria-pressed", String(visible));
    button.setAttribute("aria-label", visible ? "Ẩn mật khẩu" : "Hiện mật khẩu");
    button.querySelector("i").className = visible ? "bi bi-eye-slash" : "bi bi-eye";
  });
});

document.querySelectorAll("[data-loading-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (event.defaultPrevented) return;
    if (form.getAttribute("aria-busy") === "true") {
      event.preventDefault();
      return;
    }
    form.setAttribute("aria-busy", "true");
    const button = form.querySelector("button[type=submit]");
    if (button) button.disabled = true;
    form.querySelector("[data-submit-label]")?.classList.add("d-none");
    form.querySelector("[data-submit-loading]")?.classList.remove("d-none");
    const announcement = form.querySelector("[data-loading-announcement]");
    if (announcement) announcement.textContent = form.dataset.loadingMessage || "Đang xử lý yêu cầu đăng nhập.";
  });
});

window.addEventListener("pageshow", () => {
  document.querySelectorAll("[data-loading-form]").forEach((form) => {
    form.removeAttribute("aria-busy");
    form.querySelectorAll("button[type=submit]").forEach((button) => { button.disabled = false; });
    form.querySelector("[data-submit-label]")?.classList.remove("d-none");
    form.querySelector("[data-submit-loading]")?.classList.add("d-none");
  });
});
