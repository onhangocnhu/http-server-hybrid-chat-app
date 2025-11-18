async function loadConnected() {
  const ul = document.getElementById("channels");
  ul.innerHTML = "";

  const connectedPeers = JSON.parse(localStorage.getItem("target_peers") || "[]");

  if (connectedPeers.length === 0) {
    ul.innerHTML = "<p>No connected peers yet.</p>";
    return;
  }

  connectedPeers.forEach(p => {
    const li = document.createElement("li");
    li.innerHTML = `
      <b>${p.id}</b> (${p.ip}:${p.port})
      <button onclick="openChat('${p.id}','${p.ip}','${p.port}')">Chat</button>
    `;
    ul.appendChild(li);
  });
}

function openChat(id, ip, port) {
  localStorage.setItem("target_peer", JSON.stringify({ id, ip, port }));
  window.location.href = "/chat_room.html";
}

window.onload = loadConnected;

async function broadcastPeers() {
  const owner = document.cookie
    .split("; ")
    .find(row => row.startsWith("username="))
    ?.split("=")[1];

  if (!owner) {
    alert("You are not authenticated!");
    return;
  }

  const from = `peer-${owner}`;
  const message = prompt("Enter message to broadcast:");

  if (!message || !message.trim()) return;

  try {
    const res = await fetch("/broadcast-peer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ from, message }),
    });

    const data = await res.json();

    if (res.ok) {
      alert("Broadcast sent successfully!");
      console.log("[BROADCAST RESULT]", data);
    } else {
      alert(`Failed: ${data.message}`);
    }
  } catch (err) {
    console.error("[BROADCAST ERROR]", err);
    alert("Network error while broadcasting");
  }
}

document.getElementById("broadcast").addEventListener("click", broadcastPeers);