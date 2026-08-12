const params = new URLSearchParams(window.location.search);
const error = params.get("error");

if (error === "rate_limited") {
  document.getElementById("login-rate-limited").hidden = false;
} else if (error) {
  document.getElementById("login-error").hidden = false;
}
