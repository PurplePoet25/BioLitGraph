(function () {
  function setPresetHandlers() {
    const input = document.getElementById('query');
    document.querySelectorAll('[data-preset]').forEach((button) => {
      button.addEventListener('click', () => {
        if (input) input.value = button.dataset.preset || '';
      });
    });
  }

  function renderDetails(html) {
    const panel = document.getElementById('details-content');
    if (!panel) return;
    panel.classList.remove('empty-state');
    panel.innerHTML = html;
  }

  function paperList(papers) {
    if (!papers || !papers.length) return '<p class="aliases">No supporting papers stored for this selection.</p>';
    return `<ol class="paper-list">${papers.map((paper) => `
      <li>
        <a href="https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/" target="_blank" rel="noreferrer">${paper.title}</a>
        <div>${paper.journal || 'Unknown journal'}${paper.pub_date ? ' • ' + paper.pub_date : ''}</div>
      </li>`).join('')}
    </ol>`;
  }

  function neighborList(neighbors) {
    if (!neighbors || !neighbors.length) return '<p class="aliases">No neighbors passed the current graph filters.</p>';
    return `<ul class="simple-list">${neighbors.map((item) => `
      <li><strong>${item.label}</strong> (${item.entity_type}) — ${item.support_count} supporting papers</li>`).join('')}
    </ul>`;
  }

  function renderNodeDetail(detail) {
    const aliases = detail.aliases && detail.aliases.length ? detail.aliases.join(', ') : 'No alias list available';
    renderDetails(`
      <span class="detail-kicker">Node</span>
      <h3 class="detail-title">${detail.label}</h3>
      <div class="detail-meta">
        <span class="meta-pill">${detail.entity_type}</span>
        <span class="meta-pill">${detail.support_count} supporting papers</span>
        <span class="meta-pill">Degree ${detail.degree}</span>
      </div>
      <div class="detail-section">
        <h4>Normalized ID</h4>
        <div class="aliases">${detail.normalized_id}</div>
      </div>
      <div class="detail-section">
        <h4>Aliases / observed names</h4>
        <div class="aliases">${aliases}</div>
      </div>
      <div class="detail-section">
        <h4>Top connected entities</h4>
        ${neighborList(detail.neighbors)}
      </div>
      <div class="detail-section">
        <h4>Supporting papers</h4>
        ${paperList(detail.papers)}
      </div>
    `);
  }

  function renderEdgeDetail(detail) {
    const relationText = detail.relation_label || detail.edge_kind;
    renderDetails(`
      <span class="detail-kicker">Edge</span>
      <h3 class="detail-title">${detail.source} ↔ ${detail.target}</h3>
      <div class="detail-meta">
        <span class="meta-pill">${relationText}</span>
        <span class="meta-pill">${detail.support_count} supporting papers</span>
      </div>
      <div class="detail-section">
        <h4>What this edge means</h4>
        <div class="aliases">This connection survived the graph filters because at least two papers linked these two entities together, either by co-occurrence or by an explicit extracted relation.</div>
      </div>
      <div class="detail-section">
        <h4>Supporting papers</h4>
        ${paperList(detail.papers)}
      </div>
    `);
  }

  function renderGraph(bundle) {
    const container = document.getElementById('graph-network');
    if (!container || !bundle || !bundle.graph) return;

    const nodes = new vis.DataSet(bundle.graph.nodes.map((node) => ({
      ...node,
      font: { color: '#edf2ff', size: 18, face: 'Inter' },
      shape: 'dot',
    })));
    const edges = new vis.DataSet(bundle.graph.edges.map((edge) => ({
      ...edge,
      color: { color: 'rgba(142, 168, 255, 0.42)', highlight: '#64e5d6' },
      font: { color: '#cdd6f4', size: 12, face: 'Inter', align: 'top' },
      smooth: { type: 'dynamic' },
      scaling: { min: 1, max: 8 },
    })));

    const data = { nodes, edges };
    const options = {
      autoResize: true,
      physics: {
        stabilization: false,
        barnesHut: {
          gravitationalConstant: -2800,
          springLength: 120,
          springConstant: 0.04,
          damping: 0.18,
        },
      },
      interaction: { hover: true, navigationButtons: true, keyboard: true },
      nodes: {
        scaling: { min: 14, max: 40 },
        borderWidth: 1,
        color: {
          border: 'rgba(255,255,255,0.08)',
          background: '#8ea8ff',
          highlight: { border: '#64e5d6', background: '#64e5d6' },
        },
      },
      groups: {
        Gene: { color: { background: '#8ea8ff' } },
        Disease: { color: { background: '#ff8ec7' } },
        Chemical: { color: { background: '#64e5d6' } },
        Variant: { color: { background: '#ffd47b' } },
        CellLine: { color: { background: '#d8a4ff' } },
      },
      edges: {
        selectionWidth: 2,
        width: 1.5,
      },
    };

    const network = new vis.Network(container, data, options);
    network.on('click', (params) => {
      if (params.nodes && params.nodes.length) {
        const nodeId = params.nodes[0];
        const detail = bundle.node_details[nodeId];
        if (detail) renderNodeDetail(detail);
        return;
      }
      if (params.edges && params.edges.length) {
        const edgeId = params.edges[0];
        const detail = bundle.edge_details[edgeId];
        if (detail) renderEdgeDetail(detail);
        return;
      }
    });
  }

  function renderTimeline(bundle) {
    const timeline = bundle && bundle.timeline ? bundle.timeline : [];
    const container = document.getElementById('timeline-chart');
    if (!container || !timeline.length || typeof Plotly === 'undefined') return;
    const trace = {
      x: timeline.map((row) => row.year),
      y: timeline.map((row) => row.count),
      mode: 'lines+markers',
      type: 'scatter',
      line: { color: '#64e5d6', width: 3 },
      marker: { size: 8, color: '#8ea8ff' },
      fill: 'tozeroy',
      fillcolor: 'rgba(100, 229, 214, 0.12)',
      hovertemplate: 'Year %{x}<br>Papers %{y}<extra></extra>',
    };
    const layout = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(2, 6, 18, 0)',
      margin: { l: 50, r: 20, t: 12, b: 42 },
      font: { color: '#edf2ff', family: 'Inter' },
      xaxis: { title: 'Publication year', gridcolor: 'rgba(255,255,255,0.08)' },
      yaxis: { title: 'Paper count', gridcolor: 'rgba(255,255,255,0.08)' },
    };
    Plotly.newPlot(container, [trace], layout, { responsive: true, displayModeBar: false });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setPresetHandlers();
    if (window.BioLitGraphData) {
      renderGraph(window.BioLitGraphData);
      renderTimeline(window.BioLitGraphData);
    }
  });
})();
