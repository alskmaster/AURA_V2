// ==== AURA_V2/app/static/js/studio.js (VERSÃO QUÂNTICA 3.0) ====

document.addEventListener('DOMContentLoaded', function () {
    // Seletores de Elementos
    const hostGroupsSelect = document.getElementById('host_groups');
    const hostsContainer = document.getElementById('hosts-container');
    const hostsSelect = document.getElementById('hosts');
    const availableModulesContainer = document.getElementById('available-modules-container');
    const reportLayoutList = document.getElementById('report-layout');
    const helperText = document.getElementById('modules-helper-text');
    const hiddenLayoutInput = document.getElementById('report_layout_order');
    
    // NOVO: Seletores para o Modal
    const configModalElement = document.getElementById('moduleConfigModal');
    const configModal = new bootstrap.Modal(configModalElement);
    const modalTitle = document.getElementById('moduleConfigModalLabel');
    const modalFormContent = document.getElementById('modal-form-content');
    const saveConfigBtn = document.getElementById('saveModuleConfigBtn');
    
    // Variável para guardar a que instância nos estamos a referir
    let currentEditingInstanceId = null;

    const moduleIcons = {
        'cpu': 'fas fa-microchip',
        'default': 'fas fa-box'
    };

    new Sortable(reportLayoutList, {
        animation: 150,
        handle: '.drag-handle',
        onUpdate: updateLayoutConfig,
    });

    // Função para construir e guardar a configuração completa do layout
    function updateLayoutConfig() {
        const layoutConfig = [];
        reportLayoutList.querySelectorAll('.list-group-item').forEach(item => {
            // Descodifica a configuração do atributo de dados
            const configData = JSON.parse(item.dataset.config || '{}');
            layoutConfig.push({
                instance_id: item.dataset.instanceId,
                type: item.dataset.moduleKey,
                title: item.querySelector('.module-title').textContent,
                config: configData
            });
        });
        hiddenLayoutInput.value = JSON.stringify(layoutConfig);
    }

    // Função para abrir o modal de configuração
    function openConfigModal(instanceItem) {
        currentEditingInstanceId = instanceItem.dataset.instanceId;
        const moduleType = instanceItem.dataset.moduleKey;
        const currentTitle = instanceItem.querySelector('.module-title').textContent;
        const currentConfig = JSON.parse(instanceItem.dataset.config || '{}');

        modalTitle.textContent = `Configurar Módulo: ${currentTitle}`;
        
        // Limpa o conteúdo anterior e cria o formulário para o módulo de CPU
        modalFormContent.innerHTML = '';
        if (moduleType === 'cpu') {
            modalFormContent.innerHTML = `
                <div class="mb-3">
                    <label for="config-title" class="form-label">Título Personalizado</label>
                    <input type="text" class="form-control" id="config-title" value="${currentTitle}">
                </div>
                <div class="mb-3">
                    <label for="config-type" class="form-label">Tipo de Análise</label>
                    <select class="form-select" id="config-type">
                        <option value="average" ${currentConfig.analysis === 'average' ? 'selected' : ''}>Média Geral por Host</option>
                        <option value="top_n" ${currentConfig.analysis === 'top_n' ? 'selected' : ''}>Top N Hosts com Maior Consumo</option>
                        <option value="timeline" ${currentConfig.analysis === 'timeline' ? 'selected' : ''}>Linha do Tempo (Diário)</option>
                    </select>
                </div>
                <div class="mb-3" id="top-n-container" style="${currentConfig.analysis !== 'top_n' ? 'display: none;' : ''}">
                    <label for="config-top-n-value" class="form-label">Número de Hosts (N)</label>
                    <input type="number" class="form-control" id="config-top-n-value" value="${currentConfig.value || 5}" min="1">
                </div>
            `;
            // Lógica para mostrar/esconder o campo "N"
            modalFormContent.querySelector('#config-type').addEventListener('change', (e) => {
                document.getElementById('top-n-container').style.display = e.target.value === 'top_n' ? 'block' : 'none';
            });
        } else {
            modalFormContent.innerHTML = '<p>Este módulo não possui configurações personalizáveis.</p>';
        }

        configModal.show();
    }
    
    // Função para guardar a configuração do modal
    saveConfigBtn.addEventListener('click', () => {
        const instanceItem = reportLayoutList.querySelector(`[data-instance-id="${currentEditingInstanceId}"]`);
        if (instanceItem) {
            const newTitle = modalFormContent.querySelector('#config-title').value;
            const analysisType = modalFormContent.querySelector('#config-type').value;
            const topNValue = modalFormContent.querySelector('#config-top-n-value').value;

            instanceItem.querySelector('.module-title').textContent = newTitle;
            
            const newConfig = { analysis: analysisType, value: analysisType === 'top_n' ? parseInt(topNValue) : null };
            instanceItem.dataset.config = JSON.stringify(newConfig);

            updateLayoutConfig();
            configModal.hide();
        }
    });

    // Função para adicionar uma nova instância de módulo ao layout
    function addModuleToLayout(card) {
        const key = card.dataset.moduleKey;
        const name = card.dataset.moduleName;
        const instanceId = `instance_${key}_${Date.now()}`;

        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.dataset.moduleKey = key;
        li.dataset.instanceId = instanceId;
        // Guarda a configuração padrão no próprio elemento
        li.dataset.config = JSON.stringify({ analysis: 'average' });

        li.innerHTML = `
            <div>
                <i class="fas fa-grip-vertical drag-handle me-2" style="cursor: grab;"></i>
                <strong class="module-title" contenteditable="true" onblur="updateLayoutConfig()">${name}</strong>
                <small class="text-muted d-block ms-4">Tipo: ${name}</small>
            </div>
            <div>
                <button type="button" class="btn btn-sm btn-outline-secondary me-2 config-btn">⚙️ Configurar</button>
                <button type="button" class="btn btn-sm btn-outline-danger remove-btn">❌</button>
            </div>
        `;
        reportLayoutList.appendChild(li);

        li.querySelector('.remove-btn').addEventListener('click', () => {
            reportLayoutList.removeChild(li);
            updateLayoutConfig();
        });
        
        // O botão de configurar agora abre o modal
        li.querySelector('.config-btn').addEventListener('click', () => openConfigModal(li));

        updateLayoutConfig();
    }

    // --- Funções de Fetch e Validação (com pequenas adaptações) ---
    
    async function fetchHosts() {
        // ... (código existente, sem alterações)
        const selectedGroupIds = Array.from(hostGroupsSelect.selectedOptions).map(o => o.value);
        hostsContainer.innerHTML = '<small class="text-muted">A carregar...</small>';
        clearModules();
        if (selectedGroupIds.length === 0) {
            hostsContainer.innerHTML = '<small class="text-muted">Selecione um grupo para ver os hosts.</small>';
            return;
        }
        try {
            const response = await fetch(`/api/get_hosts/${selectedGroupIds.join(',')}`);
            if (!response.ok) throw new Error(`Erro na API: ${response.statusText}`);
            const data = await response.json();
            hostsContainer.innerHTML = '';
            if (data.error) {
                hostsContainer.innerHTML = `<div class="alert alert-danger p-2">${data.error}</div>`;
            } else if (data.length === 0) {
                hostsContainer.innerHTML = '<small class="text-muted">Nenhum host encontrado neste grupo.</small>';
            } else {
                data.forEach(host => {
                    const div = document.createElement('div');
                    div.className = 'form-check';
                    div.innerHTML = `
                        <input class="form-check-input host-checkbox" type="checkbox" value="${host.id}" id="host_${host.id}">
                        <label class="form-check-label" for="host_${host.id}">${host.name}</label>
                    `;
                    hostsContainer.appendChild(div);
                });
            }
        } catch (error) {
            console.error('Erro ao buscar hosts:', error);
            hostsContainer.innerHTML = `<div class="alert alert-danger p-2">Erro ao carregar hosts.</div>`;
        }
    }
    
    async function handleHostSelectionChange() {
        // ... (código existente, sem alterações)
        const selectedHostIds = Array.from(hostsContainer.querySelectorAll('.host-checkbox:checked')).map(cb => cb.value);
        Array.from(hostsSelect.options).forEach(opt => opt.selected = false);
        selectedHostIds.forEach(id => {
            let option = hostsSelect.querySelector(`option[value="${id}"]`);
            if (!option) { option = new Option(id, id); hostsSelect.appendChild(option); }
            option.selected = true;
        });
        validateModules();
    }
    
    async function validateModules() {
        // ... (código existente, sem alterações)
        const selectedHostIds = Array.from(hostsContainer.querySelectorAll('.host-checkbox:checked')).map(cb => cb.value);
        if (selectedHostIds.length === 0) { clearModules(); return; }
        helperText.textContent = 'A validar módulos compatíveis...';
        try {
            const [supportedResponse, allModulesResponse] = await Promise.all([
                fetch('/api/validate_modules', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ host_ids: selectedHostIds }) }),
                fetch('/api/get_all_modules')
            ]);
            if (!supportedResponse.ok || !allModulesResponse.ok) throw new Error('Falha ao comunicar com a API de módulos.');
            const supportedData = await supportedResponse.json();
            const allModulesData = await allModulesResponse.json();
            availableModulesContainer.innerHTML = '';
            if (allModulesData.all_modules) {
                const supportedKeys = supportedData.supported_modules.map(m => m.key);
                allModulesData.all_modules.forEach(module => {
                    const isSupported = supportedKeys.includes(module.key);
                    const card = createModuleCard(module, isSupported);
                    availableModulesContainer.appendChild(card);
                });
                helperText.textContent = 'Clique nos módulos para os adicionar ao relatório. Arraste-os no layout final para reordenar.';
            }
        } catch (error) {
            console.error('Erro ao validar módulos:', error);
            availableModulesContainer.innerHTML = `<div class="alert alert-danger p-2">Erro ao validar módulos.</div>`;
        }
    }

    function createModuleCard(module, isSupported) {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-3';
        const card = document.createElement('div');
        card.className = `module-card h-100 ${isSupported ? '' : 'disabled'}`;
        card.dataset.moduleKey = module.key;
        card.dataset.moduleName = module.name;
        const iconClass = moduleIcons[module.key] || moduleIcons['default'];
        card.innerHTML = `<div class="icon"><i class="${iconClass}"></i></div><h6>${module.name}</h6>`;
        if (isSupported) {
            // A ação agora é ADICIONAR uma nova instância, não selecionar/desselecionar
            card.addEventListener('click', () => addModuleToLayout(card));
        }
        col.appendChild(card);
        return col;
    }

    function clearModules() {
        availableModulesContainer.innerHTML = '';
        reportLayoutList.innerHTML = '';
        updateLayoutConfig(); // Usa a nova função
        helperText.textContent = 'Selecione os hosts para ver e escolher os módulos de análise.';
    }

    // Adiciona os Event Listeners
    hostGroupsSelect.addEventListener('change', fetchHosts);
    hostsContainer.addEventListener('change', handleHostSelectionChange);
});