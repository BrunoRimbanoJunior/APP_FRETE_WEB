(function () {
  function init() {
    const form = document.getElementById('garantia-form');
    const payloadInput = document.getElementById('id_items_payload');
    const initialDataTag = document.getElementById('items-initial-data');
    let items = [];
    try {
      items = JSON.parse(initialDataTag ? (initialDataTag.textContent || '[]') : '[]');
      if (!Array.isArray(items)) {
        items = [];
      }
    } catch (err) {
      items = [];
    }

    const produtoSearch = document.getElementById('produto-search');
    const codigoSelect = document.getElementById('id_item_codigo_peca');
    const quantidadeInput = document.getElementById('id_item_quantidade');
    const numeroLoteInput = document.getElementById('id_item_numero_lote');
    const defeitoInput = document.getElementById('id_item_defeito');
    const valorInput = document.getElementById('id_item_valor');
    const maoCheckbox = document.getElementById('id_item_mao_de_obra');
    const valorMaoInput = document.getElementById('id_item_valor_mao_de_obra');
    const notaRetornoInput = document.getElementById('id_item_nota_retorno');
    const dataRetornoInput = document.getElementById('id_item_data_retorno');
    const addItemBtn = document.getElementById('add-item-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const itemsTableBody = document.querySelector('#items-table tbody');

    if (!form || !addItemBtn || !cancelEditBtn || !itemsTableBody) {
      return;
    }

    let editingIndex = null;

    function escapeHtml(value) {
      if (value === null || value === undefined) {
        return '';
      }
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function toggleValorMao() {
      if (!valorMaoInput) {
        return;
      }
      const enabled = !!(maoCheckbox && maoCheckbox.checked);
      valorMaoInput.disabled = !enabled;
      if (!enabled) {
        valorMaoInput.value = '';
      }
    }

    function resetItemForm() {
      if (codigoSelect && codigoSelect.options.length) {
        codigoSelect.selectedIndex = 0;
      }
      if (produtoSearch) {
        produtoSearch.value = '';
      }
      if (quantidadeInput) {
        quantidadeInput.value = '1';
      }
      if (numeroLoteInput) {
        numeroLoteInput.value = '';
      }
      if (defeitoInput) {
        defeitoInput.value = '';
      }
      if (valorInput) {
        valorInput.value = '';
      }
      if (maoCheckbox) {
        maoCheckbox.checked = false;
      }
      if (valorMaoInput) {
        valorMaoInput.value = '';
      }
      if (notaRetornoInput) {
        notaRetornoInput.value = '';
      }
      if (dataRetornoInput) {
        dataRetornoInput.value = '';
      }
      toggleValorMao();
      editingIndex = null;
      addItemBtn.textContent = 'Adicionar item';
      cancelEditBtn.classList.add('d-none');
    }

    function serializeItems() {
      if (!payloadInput) {
        return;
      }
      payloadInput.value = JSON.stringify(items);
    }

    function renderTable() {
      if (!itemsTableBody) {
        return;
      }
      if (!items.length) {
        itemsTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhum item adicionado</td></tr>';
        return;
      }
      const rows = items.map(function (item, index) {
        const produtoLabel = escapeHtml(item.produto_label || item.codigo_peca || '');
        const quantidadeValor = item && item.quantidade !== undefined && item.quantidade !== null
          ? parseInt(item.quantidade, 10) || 1
          : 1;
        const defeito = escapeHtml(item.defeito || '');
        const valor = item.valor !== null && item.valor !== undefined && item.valor !== ''
          ? Number(item.valor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : '';
        const mao = item.mao_de_obra ? 'Sim' : 'Nao';
        const maoValor = item.mao_de_obra && item.valor_mao_de_obra !== null && item.valor_mao_de_obra !== undefined && item.valor_mao_de_obra !== ''
          ? ' (' + Number(item.valor_mao_de_obra).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ')'
          : '';
        const retornoParts = [];
        if (item.nota_retorno) {
          retornoParts.push(escapeHtml(item.nota_retorno));
        }
        if (item.data_retorno) {
          retornoParts.push(escapeHtml(item.data_retorno));
        }
        const retorno = retornoParts.join(' - ');
        return '<tr data-index="' + index + '">' +
          '<td>' + produtoLabel + '</td>' +
          '<td>' + quantidadeValor + '</td>' +
          '<td>' + defeito + '</td>' +
          '<td>' + valor + '</td>' +
          '<td>' + mao + maoValor + '</td>' +
          '<td>' + (retorno || '') + '</td>' +
          '<td class="text-end">' +
            '<button type="button" class="btn btn-sm btn-outline-primary me-2" data-action="edit">Editar</button>' +
            '<button type="button" class="btn btn-sm btn-outline-danger" data-action="remove">Remover</button>' +
          '</td>' +
        '</tr>';
      }).join('');
      itemsTableBody.innerHTML = rows;
    }

    function getItemFromForm() {
      const codigo = codigoSelect ? (codigoSelect.value || '').trim() : '';
      const quantidadeRaw = quantidadeInput ? quantidadeInput.value : '1';
      const numeroLote = numeroLoteInput ? (numeroLoteInput.value || '').trim() : '';
      const defeito = defeitoInput ? (defeitoInput.value || '').trim() : '';
      const valorRaw = valorInput ? valorInput.value : '';
      const valor = valorRaw !== '' ? parseFloat(valorRaw) : null;
      const maoChecked = !!(maoCheckbox && maoCheckbox.checked);
      const valorMaoRaw = valorMaoInput ? valorMaoInput.value : '';
      const valorMao = valorMaoRaw !== '' ? parseFloat(valorMaoRaw) : null;
      const notaRetorno = notaRetornoInput ? (notaRetornoInput.value || '').trim() : '';
      const dataRetorno = dataRetornoInput ? dataRetornoInput.value || '' : '';

      if (!codigo) {
        alert('Selecione um produto para adicionar.');
        return null;
      }
      const quantidade = quantidadeRaw !== '' ? parseInt(quantidadeRaw, 10) : 1;
      if (Number.isNaN(quantidade) || quantidade < 1) {
        alert('Informe uma quantidade valida.');
        return null;
      }
      if (!defeito) {
        alert('Informe o defeito do produto.');
        return null;
      }
      if (maoChecked && (valorMao === null || Number.isNaN(valorMao))) {
        alert('Informe o valor de mao de obra.');
        return null;
      }
      if (valor !== null && Number.isNaN(valor)) {
        alert('Informe um valor numerico valido.');
        return null;
      }

      const selectedOption = codigoSelect && codigoSelect.selectedIndex >= 0
        ? codigoSelect.options[codigoSelect.selectedIndex]
        : null;
      const produtoLabel = selectedOption ? selectedOption.text : codigo;

      return {
        codigo_peca: codigo,
        quantidade: quantidade,
        numero_lote: numeroLote,
        defeito: defeito,
        valor: valor !== null && !Number.isNaN(valor) ? valor : null,
        nota_retorno: notaRetorno,
        data_retorno: dataRetorno,
        mao_de_obra: maoChecked,
        valor_mao_de_obra: maoChecked && valorMao !== null && !Number.isNaN(valorMao) ? valorMao : null,
        produto_label: produtoLabel
      };
    }

    addItemBtn.addEventListener('click', function () {
      const item = getItemFromForm();
      if (!item) {
        return;
      }
      if (editingIndex !== null && editingIndex >= 0 && editingIndex < items.length) {
        items[editingIndex] = item;
      } else {
        items.push(item);
      }
      serializeItems();
      renderTable();
      resetItemForm();
    });

    cancelEditBtn.addEventListener('click', function () {
      resetItemForm();
    });

    itemsTableBody.addEventListener('click', function (event) {
      const button = event.target.closest('button[data-action]');
      if (!button) {
        return;
      }
      const row = button.closest('tr[data-index]');
      if (!row) {
        return;
      }
      const index = parseInt(row.getAttribute('data-index'), 10);
      if (Number.isNaN(index) || index < 0 || index >= items.length) {
        return;
      }

      if (button.dataset.action === 'edit') {
        const item = items[index];
        editingIndex = index;
        if (codigoSelect) {
          const exists = Array.from(codigoSelect.options || []).some(function (opt) {
            return opt.value === item.codigo_peca;
          });
          if (!exists) {
            const opt = document.createElement('option');
            opt.value = item.codigo_peca;
            opt.textContent = item.produto_label || item.codigo_peca;
            codigoSelect.appendChild(opt);
          }
          codigoSelect.value = item.codigo_peca;
        }
        if (quantidadeInput) {
          quantidadeInput.value = item.quantidade !== undefined && item.quantidade !== null ? item.quantidade : 1;
        }
        if (numeroLoteInput) {
          numeroLoteInput.value = item.numero_lote || '';
        }
        if (defeitoInput) {
          defeitoInput.value = item.defeito || '';
        }
        if (valorInput) {
          valorInput.value = item.valor !== null && item.valor !== undefined ? item.valor : '';
        }
        if (maoCheckbox) {
          maoCheckbox.checked = !!item.mao_de_obra;
        }
        if (valorMaoInput) {
          valorMaoInput.value = item.valor_mao_de_obra !== null && item.valor_mao_de_obra !== undefined ? item.valor_mao_de_obra : '';
        }
        if (notaRetornoInput) {
          notaRetornoInput.value = item.nota_retorno || '';
        }
        if (dataRetornoInput) {
          dataRetornoInput.value = item.data_retorno || '';
        }
        toggleValorMao();
        addItemBtn.textContent = 'Atualizar item';
        cancelEditBtn.classList.remove('d-none');
      } else if (button.dataset.action === 'remove') {
        if (confirm('Remover este item da garantia?')) {
          items.splice(index, 1);
          serializeItems();
          renderTable();
          resetItemForm();
        }
      }
    });

    if (maoCheckbox) {
      maoCheckbox.addEventListener('change', toggleValorMao);
      toggleValorMao();
    }

    function bootstrapInitialRender() {
      if (!Array.isArray(items)) {
        items = [];
      } else {
        items = items.map(function (item) {
          if (item && typeof item === 'object') {
            const normalizado = item.quantidade !== undefined && item.quantidade !== null
              ? parseInt(item.quantidade, 10) || 1
              : 1;
                        const label = item && item.produto_label ? item.produto_label : "";
            return Object.assign({ quantidade: normalizado, produto_label: label }, item);
          }
          return item;
        });
      }
      serializeItems();
      renderTable();
    }

    form.addEventListener('submit', function (event) {
      serializeItems();
      if (!items.length) {
        event.preventDefault();
        alert('Adicione ao menos um produto antes de salvar.');
      }
    });

    bootstrapInitialRender();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

