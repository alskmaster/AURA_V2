# ==== AURA_V2/app/zabbix_api.py ====

import requests
import json
from flask import current_app

class ZabbixServiceError(Exception):
    """Exceção customizada para erros na API do Zabbix."""
    pass

class ZabbixService:
    """Uma classe dedicada para toda a comunicação com a API do Zabbix."""
    def __init__(self, datasource):
        if datasource.platform.lower() != 'zabbix':
            raise ValueError("A fonte de dados fornecida não é do tipo 'Zabbix'.")

        credentials = datasource.get_credentials()
        self.url = credentials.get('url')
        self.token = credentials.get('token') # Procura por um token primeiro

        # Se não encontrou um token, tenta o login com user/password
        if not self.token:
            self.user = credentials.get('user')
            self.password = credentials.get('password')
            if not all([self.url, self.user, self.password]):
                raise ValueError("Credenciais insuficientes. Forneça 'url' e 'token', ou 'url', 'user' e 'password'.")
            self._login()
        
        elif not self.url:
            raise ValueError("Credenciais insuficientes. A 'url' é obrigatória.")

    def _login(self):
        """Realiza o login na API (usado apenas se não for fornecido um token)."""
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": self.user, "password": self.password},
            "id": 1
        }
        response = self._make_request(payload, auth_required=False)
        self.token = response.get('result')
        if not self.token:
            raise ZabbixServiceError("Falha na autenticação com o Zabbix. Verifique as credenciais.")

    def _make_request(self, payload, auth_required=True):
        """Método central para fazer requisições à API."""
        headers = {'Content-Type': 'application/json-rpc'}
        
        if auth_required:
            if not self.token:
                raise ZabbixServiceError("Token de autenticação não encontrado ou inválido.")
            payload['auth'] = self.token

        try:
            response = requests.post(self.url, headers=headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                error_msg = data['error'].get('data', 'Erro desconhecido na API do Zabbix.')
                current_app.logger.error(f"Erro na API Zabbix: {error_msg}")
                raise ZabbixServiceError(error_msg)
            return data
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão com o Zabbix: {e}")
            raise ZabbixServiceError(f"Não foi possível conectar ao servidor Zabbix em {self.url}.")

    def get(self, method, params):
        """Método genérico para chamadas 'get' da API."""
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        return self._make_request(payload).get('result')