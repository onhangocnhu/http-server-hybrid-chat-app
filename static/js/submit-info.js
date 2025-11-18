
document.getElementById("submitInfo").addEventListener("click", async () => {
  const statusEl = document.getElementById("status");
  statusEl.textContent = "Submitting...";

  try {
    const res = await fetch("/submit-info", {
      method: "POST",
      credentials: "include"
    });

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      statusEl.textContent = data.message || "OK";
      const { owner, ip, port } = data;
      localStorage.setItem("peer_info", JSON.stringify(data));

      const redirectUrl = `http://${ip}:${port}/chat_channel.html`;
      setTimeout(() => (window.location.href = redirectUrl), 1000);

    } else if (res.status === 409) {
      statusEl.textContent = data.message || "Already submitted. Redirecting...";

      const { owner, ip, port } = data;
      if (ip && port) {
        localStorage.setItem("peer_info", JSON.stringify(data));
        const redirectUrl = `http://${ip}:${port}/chat_channel.html`;
        setTimeout(() => (window.location.href = redirectUrl), 1000);
      } else {
        statusEl.textContent = "Already submitted, but cannot get peer info to redirect.";
      }

    } else {
      statusEl.textContent = "Error: " + (data.message || "An unknown error occurred.");
    }
  } catch (error) {
    statusEl.textContent = "Error: " + error.message;
  }
});