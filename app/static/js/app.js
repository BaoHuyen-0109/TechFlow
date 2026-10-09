"use strict";

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
  form.addEventListener("submit", () => {
    form.setAttribute("aria-busy", "true");
    const button = form.querySelector("button[type=submit]");
    if (button) button.disabled = true;
    form.querySelector("[data-submit-label]")?.classList.add("d-none");
    form.querySelector("[data-submit-loading]")?.classList.remove("d-none");
    const announcement = form.querySelector("[data-loading-announcement]");
    if (announcement) announcement.textContent = "Đang xử lý yêu cầu đăng nhập.";
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
