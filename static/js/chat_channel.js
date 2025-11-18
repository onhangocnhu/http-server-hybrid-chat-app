const TRACKER_URL = "http://tracker.local:9000";

const peerInfo = JSON.parse(localStorage.getItem("peer_info") || "{}");
const { owner, ip, port } = peerInfo;

const port_target = 0

window.addEventListener("load", async () => {
  try {
    if (!peerInfo) {
      console.warn("[add-list] missing info", { ip, port, owner });
      return;
    }

    if (localStorage.getItem("added") === "true") {
      console.log("[add-list] already sent once, skipping");
      return;
    }

    const payload = { ip, port, owner };
    console.log("[add-list] registering peer", payload);

    const res = await fetch(`${TRACKER_URL}/add-list`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include"
    });

    const text = await res.text();
    console.log("[add-list] tracker response:", text);

    if (res.ok) {
      localStorage.setItem("added", "true");
    }
  } catch (err) {
    console.error("[add-list] failed:", err);
  }
});

async function loadPeers() {
  try {
    const myId = `peer-${owner}`;

    const res = await fetch("/get-list", {
      method: "GET",
      credentials: "include"
    });

    const tbody = document.getElementById("peerTable");
    tbody.innerHTML = "";

    let trackerPeers = {};
    if (res.ok) {
      const data = await res.json();
      trackerPeers = data.active_peers || {};
    }

    const connectedPeers = JSON.parse(localStorage.getItem("target_peers") || "[]");

    const mergedPeers = { ...trackerPeers };
    connectedPeers.forEach(p => {
      if (!mergedPeers[p.id]) {
        mergedPeers[p.id] = { ip: p.ip, port: p.port, connected: true };
      }
    });

    const entries = Object.entries(mergedPeers);
    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4">There is not any peer online</td></tr>`;
      return;
    }

    entries.forEach(([id, info]) => {
      if (id === myId) return;

      const isConnected = connectedPeers.some(p => p.id === id);
      const btnLabel = isConnected ? "Connected" : "Connect";
      const disabled = isConnected ? "disabled" : "";

      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${id}</td>
        <td>${info.ip}</td>
        <td>${info.port}</td>
        <td><button ${disabled} onclick="connectPeer('${id}', '${info.ip}', '${info.port}')">${btnLabel}</button></td>
      `;
      if (isConnected) {
        row.querySelector("button").style.backgroundColor = "#9acd32";
      }
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("[loadPeers] failed:", err);
    document.getElementById("peerTable").innerHTML =
      `<tr><td colspan="4">Failed to load peers: ${err.message}</td></tr>`;
  }
}

document.getElementById("refresh").addEventListener("click", loadPeers);

async function connectPeer(targetId, targetIp, targetPort) {
  const me = `peer-${owner}`;

  const res = await fetch("/connect-peer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from: me, to: targetId }),
    credentials: "include"
  });

  if (res.ok) {
    const newPeer = {
      id: targetId,
      ip: targetIp,
      port: targetPort
    };
    const existing = JSON.parse(localStorage.getItem("target_peers") || "[]");

    const already = existing.some(p => p.id === targetId);
    if (!already) existing.push(newPeer);

    localStorage.setItem("target_peers", JSON.stringify(existing));

    const rows = document.querySelectorAll("#peerTable tr");
    for (const row of rows) {
      if (row.innerText.includes(targetId)) {
        const btn = row.querySelector("button");
        btn.textContent = "Connected";
        btn.disabled = true;
        btn.style.backgroundColor = "#9acd32";
        btn.style.cursor = "not-allowed";
        break;
      }
    }

    console.log(`[CONNECT] ${me} connected to ${targetId}`);
  } else {
    const text = await res.text();
    alert("Connect failed: " + text);
  }
}