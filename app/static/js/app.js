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
      const url = new URL(source, window.location.origin);
      if ((source.startsWith("/") && url.origin !== window.location.origin) ||
          !["http:", "https:"].includes(url.protocol) || url.username || url.password ||
          /[\s\u0000-\u001f\u007f]/.test(source)) throw new Error();
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
  update(preview.dataset.imageSource || (input ? input.value : ""));
});

document.querySelectorAll("[data-image-drop]").forEach((zone) => {
  const input = zone.querySelector('input[type="file"]');
  const choose = zone.querySelector("[data-image-choose]");
  const preview = zone.parentElement.querySelector("[data-upload-preview]");
  const image = preview?.querySelector("[data-upload-image]");
  const name = preview?.querySelector("[data-upload-name]");
  let objectUrl;
  const chooseFile = () => input?.click();
  choose?.addEventListener("click", chooseFile);
  zone.addEventListener("click", (event) => {
    if (event.target !== choose && event.target !== input) chooseFile();
  });
  zone.addEventListener("keydown", (event) => {
    if (event.target === zone && ["Enter", " "].includes(event.key)) {
      event.preventDefault();
      chooseFile();
    }
  });
  ["dragenter", "dragover"].forEach((type) => zone.addEventListener(type, (event) => {
    event.preventDefault();
    zone.classList.add("is-dragging");
  }));
  ["dragleave", "drop"].forEach((type) => zone.addEventListener(type, (event) => {
    event.preventDefault();
    zone.classList.remove("is-dragging");
  }));
  zone.addEventListener("drop", (event) => {
    const file = event.dataTransfer?.files?.[0];
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
  input?.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    image.src = objectUrl;
    name.textContent = file.name;
    preview.hidden = false;
  });
  input?.form?.addEventListener("submit", () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
  }, { once: true });
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

document.querySelectorAll("[data-nav-group]").forEach((group) => {
  const summary = group.querySelector("summary");
  const sync = () => summary.setAttribute("aria-expanded", String(group.open));
  group.addEventListener("toggle", sync);
  summary.addEventListener("click", (event) => {
    if (matchMedia("(min-width: 992px)").matches && document.body.classList.contains("workspace-collapsed")) {
      event.preventDefault();
      document.body.classList.remove("workspace-collapsed");
      group.open = true;
      document.querySelectorAll("[data-sidebar-collapse]").forEach((button) => {
        button.setAttribute("aria-expanded", "true");
        button.setAttribute("aria-label", "Thu gọn thanh điều hướng");
      });
    }
  });
  sync();
});
function syncAccountNavigation() {
  const account = document.querySelector('[data-nav-group="account"]');
  if (!account) return;
  const profile = account.querySelector("a");
  const isProfile = location.pathname === new URL(profile.href).pathname && location.hash === "#session";
  if (isProfile) account.open = true;
  account.classList.toggle("is-active", isProfile);
  profile.classList.toggle("active", isProfile);
  if (isProfile) profile.setAttribute("aria-current", "location");
  else profile.removeAttribute("aria-current");
  const overview = document.querySelector('.ws-navigation > a[href="/staff/dashboard"]');
  if (overview && location.pathname === "/staff/dashboard") {
    overview.classList.toggle("active", !isProfile);
    if (isProfile) overview.removeAttribute("aria-current");
    else overview.setAttribute("aria-current", "page");
  }
}
syncAccountNavigation();
window.addEventListener("hashchange", syncAccountNavigation);

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
