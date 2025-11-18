const peerInfo = JSON.parse(localStorage.getItem("peer_info") || "{}");
const target = JSON.parse(localStorage.getItem("target_peer") || "{}");

const { owner } = peerInfo;
const me = `peer-${owner}`;
const targetId = target.id;

document.getElementById("title").innerText = `Chat with ${targetId}`;

// Gửi tin
async function send() {
  const msg = document.getElementById("msg").value.trim();
  if (!msg) return;

  console.log("[SEND]", { from: me, to: targetId, message: msg });

  const res = await fetch("/send-peer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from: me, to: targetId, message: msg }),
    credentials: "include",
  });

  if (!res.ok) {
    console.error("Send failed:", await res.text());
    return;
  }

  const now = new Date().toLocaleTimeString("en-GB", { hour12: false });
  const box = document.getElementById("box");
  box.insertAdjacentHTML("beforeend", `<div>[${now}] <b>me</b>: ${msg}</div>`);
  box.scrollTop = box.scrollHeight;
  document.getElementById("msg").value = "";
}

async function refreshMessages() {
  try {
    const res = await fetch("/get-messages", { credentials: "include" });
    const data = await res.json();

    const filtered = data.messages.filter(
      (m) =>
        (m.from === me && m.to === targetId) ||
        (m.from === targetId && m.to === me)
    );

    const box = document.getElementById("box");
    box.innerHTML = filtered
      .map((m) => {
        const sender = m.from === me ? "me" : m.from;
        return `<div>[${m.ts}] <b>${sender}</b>: ${m.message}</div>`;
      })
      .join("");
    box.scrollTop = box.scrollHeight;
  } catch (err) {
    console.error("[refreshMessages error]", err);
  }
}

document.getElementById("send").onclick = send;
document.getElementById("refresh").onclick = refreshMessages;
window.onload = refreshMessages;
