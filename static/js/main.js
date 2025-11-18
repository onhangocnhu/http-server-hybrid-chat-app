document.addEventListener("DOMContentLoaded", () => {
  const btnRefresh = document.getElementById("btn-refresh");
  const peerListTbody = document.getElementById("peer-list-container");

  btnRefresh.addEventListener("click", fetchPeerList);

  async function fetchPeerList() {
    peerListTbody.innerHTML = '<tr><td colspan="4">Loading...</td></tr>';
    try {
      const res = await fetch("/get-list");

      if (res.status === 401) {
        window.location.href = "/login.html";
        return;
      }

      if (!res.ok) {
        throw new Error("Server error: " + res.statusText);
      }

      const data = await res.json();
      renderPeers(data.active_peers);
    } catch (err) {
      console.error("Failed to load peer list:", err);
      peerListTbody.innerHTML = `<tr><td colspan="4">Error: ${err.message}</td></tr>`;
    }
  }

  function renderPeers(peers) {
    if (!peers || Object.keys(peers).length === 0) {
      peerListTbody.innerHTML = '<tr><td colspan="4">(No active peers)</td></tr>';
      return;
    }

    peerListTbody.innerHTML = "";

    Object.entries(peers).forEach(([peerId, info]) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${peerId}</td>
        <td>${info.owner || 'N/A'}</td>
        <td>${info.ip || 'N/A'}</td>
        <td>${info.port || 'N/A'}</td>
      `;
      peerListTbody.appendChild(row);
    });
  }

  fetchPeerList();
});