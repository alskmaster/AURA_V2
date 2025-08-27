// ==== AURA_V2/app/static/js/studio.js ====

document.addEventListener('DOMContentLoaded', function () {
    const hostGroupsSelect = document.getElementById('host_groups');
    const hostsContainer = document.getElementById('hosts-container');
    const hostsSelect = document.getElementById('hosts'); // O select escondido
    const modulesContainer = document.querySelector('#modules-helper-text').parentNode;
    const helperText = document.getElementById('modules-helper-text');

    // Função para buscar Hosts quando um grupo é selecionado
    async function fetchHosts() {
        const selectedGroupIds = Array.from(hostGroupsSelect.selectedOptions).map(o => o.value);
        hostsContainer.innerHTML = '<small class="text-muted">A carregar...</small>';
        
        // Limpa os módulos quando a seleção de grupo muda
        modulesContainer.innerHTML = '<p class="text-muted" id="modules-helper-text">Selecione os hosts acima para ver os módulos de análise.</p>';

        if (selectedGroupIds.length === 0) {
            hostsContainer.innerHTML = '<small class="text-muted">Selecione um grupo para ver os hosts.</small>';
            return;
        }

        try {
            const response = await fetch(`/api/get_hosts/${selectedGroupIds.join(',')}`);
            if (!response.ok) throw new Error(`Erro na API: ${response.statusText}`);
            const data = await response.json();

            hostsContainer.innerHTML = ''; // Limpa o container
            if (data.error) {
                hostsContainer.innerHTML = `<div class="alert alert-danger p-2">${data.error}</div>`;
            } else if (data.length === 0) {
                hostsContainer.innerHTML = '<small class="text-muted">Nenhum host encontrado neste grupo.</small>';
            } else {
                // Cria um checkbox para cada host
                data.forEach(host => {
                    const div = document.createElement('div');
                    div.className = 'form-check';
                    div.innerHTML = `
                        <input class="form-check-input host-checkbox" type="checkbox" value="${host.id}" id="host_${host.id}">
                        <label class.="form-check-label" for="host_${host.id}">${host.name}</label>
                    `;
                    hostsContainer.appendChild(div);
                });
            }
        } catch (error) {
            console.error('Erro ao buscar hosts:', error);
            hostsContainer.innerHTML = `<div class="alert alert-danger p-2">Erro ao carregar hosts.</div>`;
        }
    }

    // Função para validar módulos quando um host é selecionado
    async function validateModules() {
        const selectedHostIds = Array.from(hostsContainer.querySelectorAll('.host-checkbox:checked')).map(cb => cb.value);

        // Sincroniza os checkboxes com o <select> múltiplo que será enviado no formulário
        Array.from(hostsSelect.options).forEach(opt => opt.selected = false);
        selectedHostIds.forEach(id => {
            let option = hostsSelect.querySelector(`option[value="${id}"]`);
            if (!option) {
                option = new Option(id, id);
                hostsSelect.appendChild(option);
            }
            option.selected = true;
        });

        if (selectedHostIds.length === 0) {
            modulesContainer.innerHTML = '<p class="text-muted" id="modules-helper-text">Selecione os hosts acima para ver os módulos de análise.</p>';
            return;
        }

        helperText.textContent = 'A validar módulos compatíveis...';

        try {
            const response = await fetch('/api/validate_modules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host_ids: selectedHostIds })
            });
            if (!response.ok) throw new Error(`Erro na API: ${response.statusText}`);
            const data = await response.json();
            
            modulesContainer.innerHTML = ''; // Limpa a área de módulos
            
            if (data.error) {
                 modulesContainer.innerHTML = `<div class="alert alert-danger p-2">${data.error}</div>`;
            } else if (data.supported_modules && data.supported_modules.length > 0) {
                data.supported_modules.forEach(module => {
                    const div = document.createElement('div');
                    div.className = 'form-check';
                    div.innerHTML = `
                        <input class="form-check-input" type="checkbox" name="modules" value="${module.key}" id="module_${module.key}">
                        <label class="form-check-label" for="module_${module.key}">${module.name}</label>
                    `;
                    modulesContainer.appendChild(div);
                });
            } else {
                modulesContainer.innerHTML = '<div class="alert alert-warning">Nenhum módulo compatível encontrado para a seleção atual.</div>';
            }

        } catch (error) {
            console.error('Erro ao validar módulos:', error);
            modulesContainer.innerHTML = `<div class="alert alert-danger p-2">Erro ao validar módulos.</div>`;
        }
    }

    // Adiciona os gatilhos (event listeners)
    hostGroupsSelect.addEventListener('change', fetchHosts);
    hostsContainer.addEventListener('change', validateModules); // Valida sempre que um checkbox de host é alterado
});