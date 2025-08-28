// ==== AURA_V2/app/static/js/studio.js (VERSÃO FINAL COM TODAS AS FUNCIONALIDADES) ====

document.addEventListener('DOMContentLoaded', function () {
    // --- 1. Seletores de Elementos ---
    const hostGroupsSelect = document.getElementById('host_groups');
    const hostsContainer = document.getElementById('hosts-container');
    const hostsSelect = document.getElementById('hosts');
    const availableModulesContainer = document.getElementById('available-modules-container');
    const reportLayoutList = document.getElementById('report-layout');
    const helperText = document.getElementById('modules-helper-text');
    const hiddenLayoutInput = document.getElementById('report_layout_order');
    const configModalElement = document.getElementById('moduleConfigModal');
    const configModal = new bootstrap.Modal(configModalElement);
    const modalTitle = document.getElementById('moduleConfigModalLabel');
    const modalFormContent = document.getElementById('modal-form-content');
    const saveConfigBtn = document.getElementById('saveModuleConfigBtn');
    
    // --- 2. Variáveis de Estado ---
    let currentEditingInstanceId = null;
    const moduleIcons = {
        'cpu': 'fas fa-microchip',
        'default': 'fas fa-box'
    };

    // --- 3. Inicializações ---
    new Sortable(reportLayoutList, {
        animation: 150,
        handle: '.drag-handle',
        onUpdate: updateLayoutConfig,
    });

    // --- 4. Funções Principais com DEBUG ---

    function updateLayoutConfig() {
        console.log('[DEBUG] updateLayoutConfig: Atualizando a configuração do layout.');
        const layoutConfig = [];
        reportLayoutList.querySelectorAll('.list-group-item').forEach(item => {
            layoutConfig.push({
                instance_id: item.dataset.instanceId,
                type: item.dataset.moduleKey,
                title: item.querySelector('.module-title').textContent,
                config: JSON.parse(item.dataset.config || '{}')
            });
        });
        hiddenLayoutInput.value = JSON.stringify(layoutConfig);
        console.log('[DEBUG] updateLayoutConfig: Configuração final em JSON:', hiddenLayoutInput.value);
    }

    function openConfigModal(instanceItem) {
        console.log('[DEBUG] openConfigModal: Abrindo modal para a instância:', instanceItem.dataset.instanceId);
        currentEditingInstanceId = instanceItem.dataset.instanceId;
        const moduleType = instanceItem.dataset.moduleKey;
        const currentTitle = instanceItem.querySelector('.module-title').textContent;
        const currentConfig = JSON.parse(instanceItem.dataset.config || '{}');

        modalTitle.textContent = `Configurar: ${currentTitle}`;
        modalFormContent.innerHTML = '';

        // Formulário base com Título e a nova opção de Quebra de Página
        let baseFormHtml = `
            <div class="mb-3">
                <label for="config-title" class="form-label">Título da Análise</label>
                <input type="text" class="form-control" id="config-title" value="${currentTitle}">
            </div>
        `;

        let moduleSpecificFormHtml = '';

        if (moduleType === 'cpu') {
            moduleSpecificFormHtml = `
                <div class="mb-3">
                    <label for="config-analysis" class="form-label">Tipo de Análise</label>
                    <select class="form-select" id="config-analysis">
                        <option value="average" ${currentConfig.analysis === 'average' ? 'selected' : ''}>Média Geral por Host</option>
                        <option value="top_n" ${currentConfig.analysis === 'top_n' ? 'selected' : ''}>Top N Hosts (Maior Média)</option>
                        <option value="timeline" ${currentConfig.analysis === 'timeline' ? 'selected' : ''}>Linha do Tempo (Uso Diário)</option>
                    </select>
                </div>
                <div class="mb-3" id="top-n-container" style="${currentConfig.analysis !== 'top_n' ? 'display: none;' : ''}">
                    <label for="config-top-n-value" class="form-label">Número de Hosts (N)</label>
                    <input type="number" class="form-control" id="config-top-n-value" value="${currentConfig.value || 5}" min="1">
                </div>
            `;
        } else {
            moduleSpecificFormHtml = '<p>Este módulo não possui configurações de análise personalizáveis.</p>';
        }

        // Adiciona a opção de nova página para TODOS os módulos
        let layoutOptionsHtml = `
            <hr>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="" id="config-newPage" ${currentConfig.newPage ? 'checked' : ''}>
                <label class="form-check-label" for="config-newPage">
                    Iniciar este módulo numa nova página
                </label>
            </div>
        `;
        
        modalFormContent.innerHTML = baseFormHtml + moduleSpecificFormHtml + layoutOptionsHtml;

        // Adiciona lógica JS específica do módulo, se houver
        if (moduleType === 'cpu') {
            modalFormContent.querySelector('#config-analysis').addEventListener('change', (e) => {
                document.getElementById('top-n-container').style.display = e.target.value === 'top_n' ? 'block' : 'none';
            });
        }
        
        configModal.show();
    }
    
    function addModuleToLayout(card) {
        console.log('[DEBUG] addModuleToLayout: Adicionando módulo ao layout:', card.dataset.moduleKey);
        const key = card.dataset.moduleKey;
        const name = card.dataset.moduleName;
        const instanceId = `instance_${key}_${Date.now()}`;

        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.dataset.moduleKey = key;
        li.dataset.instanceId = instanceId;
        // Configuração padrão inicial
        li.dataset.config = JSON.stringify({ analysis: 'average', newPage: false });

        li.innerHTML = `
            <div>
                <i class="fas fa-grip-vertical drag-handle me-3 text-muted" title="Arrastar para reordenar"></i>
                <strong class="module-title">${name}</strong>
            </div>
            <div>
                <button type="button" class="btn btn-sm btn-outline-primary me-2 config-btn" title="Configurar"><i class="fas fa-cog"></i></button>
                <button type="button" class="btn btn-sm btn-outline-danger remove-btn" title="Remover"><i class="fas fa-trash-alt"></i></button>
            </div>
        `;
        reportLayoutList.appendChild(li);

        li.querySelector('.remove-btn').addEventListener('click', () => {
            console.log('[DEBUG] Evento: Clique para remover a instância:', li.dataset.instanceId);
            li.remove();
            updateLayoutConfig();
        });
        li.querySelector('.config-btn').addEventListener('click', () => openConfigModal(li));

        updateLayoutConfig();
    }

    function createModuleCard(module) {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3';
        const card = document.createElement('div');
        card.className = 'module-card h-100 disabled';
        card.dataset.moduleKey = module.key;
        card.dataset.moduleName = module.name;
        const iconClass = moduleIcons[module.key] || moduleIcons['default'];
        card.innerHTML = `<div class="icon"><i class="${iconClass}"></i></div><h6>${module.name}</h6>`;
        card.title = 'Selecione hosts compatíveis para ativar este módulo.';
        col.appendChild(card);
        return col;
    }

    // --- 5. Funções de API e Sincronização ---
    // (As funções fetchHosts, handleHostSelectionChange, validateModules e initializeStudio não precisam de alterações)
    
    async function fetchHosts() {
        console.log('[DEBUG] fetchHosts: Buscando hosts...');
        const selectedGroupIds = Array.from(hostGroupsSelect.selectedOptions).map(o => o.value);
        hostsContainer.innerHTML = '<div class="text-center p-3"><span class="spinner-border spinner-border-sm"></span> A carregar hosts...</div>';
        document.querySelectorAll('.module-card').forEach(card => card.classList.add('disabled'));
        helperText.textContent = 'Selecione os hosts acima para ver e escolher os módulos de análise.';
        if (selectedGroupIds.length === 0) {
            hostsContainer.innerHTML = '<small class="text-muted p-3">Selecione um grupo para ver os hosts.</small>';
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
                hostsContainer.innerHTML = '<small class="text-muted p-3">Nenhum host encontrado neste grupo.</small>';
            } else {
                data.forEach(host => {
                    const div = document.createElement('div');
                    div.className = 'form-check';
                    div.innerHTML = `<input class="form-check-input host-checkbox" type="checkbox" value="${host.id}" id="host_${host.id}"><label class="form-check-label" for="host_${host.id}">${host.name}</label>`;
                    hostsContainer.appendChild(div);
                });
            }
        } catch (error) {
            console.error('[ERRO] fetchHosts:', error);
            hostsContainer.innerHTML = `<div class="alert alert-danger p-2">Erro ao carregar hosts.</div>`;
        }
    }
    
    async function handleHostSelectionChange() {
        console.log('[DEBUG] handleHostSelectionChange: Seleção de host alterada.');
        const selectedHostIds = Array.from(hostsContainer.querySelectorAll('.host-checkbox:checked')).map(cb => cb.value);
        Array.from(hostsSelect.options).forEach(opt => opt.selected = false);
        selectedHostIds.forEach(id => {
            let option = hostsSelect.querySelector(`option[value="${id}"]`);
            if (!option) { option = new Option(id, id); hostsSelect.appendChild(option); }
            option.selected = true;
        });
        await validateModules();
    }
    
    async function validateModules() {
        console.log('[DEBUG] validateModules: Validando módulos compatíveis...');
        const selectedHostIds = Array.from(hostsContainer.querySelectorAll('.host-checkbox:checked')).map(cb => cb.value);
        if (selectedHostIds.length === 0) {
            document.querySelectorAll('.module-card').forEach(card => card.classList.add('disabled'));
            helperText.textContent = 'Selecione os hosts acima para ver e escolher os módulos de análise.';
            return;
        }
        helperText.textContent = 'A validar módulos compatíveis...';
        try {
            const response = await fetch('/api/validate_modules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host_ids: selectedHostIds })
            });
            if (!response.ok) throw new Error('Falha na API de validação.');
            const data = await response.json();
            const supportedKeys = data.supported_modules.map(m => m.key);
            console.log('[DEBUG] validateModules: Módulos suportados recebidos da API:', supportedKeys);
            document.querySelectorAll('.module-card').forEach(card => {
                const isSupported = supportedKeys.includes(card.dataset.moduleKey);
                card.classList.toggle('disabled', !isSupported);
                card.title = isSupported ? `Adicionar "${card.dataset.moduleName}" ao relatório` : 'Selecione hosts compatíveis para ativar este módulo.';
            });
            helperText.textContent = 'Clique nos módulos suportados para os adicionar ao relatório.';
        } catch (error) {
            console.error('[ERRO] validateModules:', error);
        }
    }
    
    async function initializeStudio() {
        console.log('[DEBUG] initializeStudio: Iniciando o Analytics Studio.');
        try {
            const response = await fetch('/api/get_all_modules');
            const data = await response.json();
            availableModulesContainer.innerHTML = '';
            if (data.all_modules) {
                data.all_modules.forEach(module => {
                    const cardElement = createModuleCard(module);
                    availableModulesContainer.appendChild(cardElement);
                });
            }
        } catch (error) {
            console.error("[ERRO] initializeStudio:", error);
            availableModulesContainer.innerHTML = '<div class="alert alert-danger">Não foi possível carregar os módulos.</div>';
        }
    }

    // --- 6. Event Listeners ---
    availableModulesContainer.addEventListener('click', function(event) {
        const card = event.target.closest('.module-card');
        if (card && !card.classList.contains('disabled')) {
            addModuleToLayout(card);
        }
    });

    hostGroupsSelect.addEventListener('change', fetchHosts);
    hostsContainer.addEventListener('change', handleHostSelectionChange);

    saveConfigBtn.addEventListener('click', () => {
        const instanceItem = reportLayoutList.querySelector(`[data-instance-id="${currentEditingInstanceId}"]`);
        if (instanceItem) {
            const newTitle = modalFormContent.querySelector('#config-title').value;
            instanceItem.querySelector('.module-title').textContent = newTitle;

            // Começa com a configuração que já existia
            let newConfig = JSON.parse(instanceItem.dataset.config);
            
            // Atualiza com os novos valores do formulário
            const analysisSelect = modalFormContent.querySelector('#config-analysis');
            if(analysisSelect) {
                newConfig.analysis = analysisSelect.value;
                if (newConfig.analysis === 'top_n') {
                    newConfig.value = modalFormContent.querySelector('#config-top-n-value').value;
                } else {
                    delete newConfig.value; // Remove a chave 'value' se não for 'top_n'
                }
            }
            
            // Adiciona a nova opção de quebra de página
            newConfig.newPage = modalFormContent.querySelector('#config-newPage').checked;
            
            console.log('[DEBUG] saveConfigBtn: Nova configuração a ser guardada:', newConfig);
            
            instanceItem.dataset.config = JSON.stringify(newConfig);
            updateLayoutConfig();
            configModal.hide();
        }
    });

    initializeStudio();
});