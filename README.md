# Sensor-de-Solo

Este projeto é um leitor para o Sensor de Solo RS485 Modbus 7 em 1, desenvolvido em Python com interface gráfica moderna usando Kivy. Permite a leitura de dados de umidade, temperatura, pH, condutividade elétrica, nitrogênio (N), fósforo (P) e potássio (K) em PC ou Android (via USB OTG).

## Principais Funcionalidades
- Interface gráfica moderna, responsiva e com alto contraste.
- Só começa a ler dados após o usuário escolher um modo.
- **Modo Contínuo:** Cada sessão gera um novo arquivo JSON, acumulando todas as leituras dessa sessão.
- **Modo Única:** Cada leitura é salva em um arquivo separado.
- **Modo Média:** Cada média (10 amostras) é salva em um arquivo separado, contendo as 10 leituras e a média calculada.
- Delay de 10 segundos entre amostras no modo média.
- Unidades de medida destacadas e legíveis.
- Compatível com Windows, Linux e Android (Pydroid 3).

## Instalação

### Android (Pydroid 3)
1. Baixe e instale o [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) na Play Store.
2. No PIP do Pydroid, instale:
   - `kivy`
   - `usb4a`
   - `usbserial4a`
   - `pyserial`
   - `minimalmodbus`
3. Conecte o sensor via cabo OTG e dê permissão USB ao Pydroid 3.

### PC (Windows/Linux)
1. Instale as dependências:
   ```bash
   pip install kivy pyserial minimalmodbus
   ```
2. Conecte o sensor via USB/Serial.

## Como Usar
1. Execute o script `SesorDeSolo.py`.
2. Escolha a porta serial (no PC) quando solicitado.
3. A interface será exibida. **Escolha um modo para iniciar as leituras:**
   - **Contínuo:** Leituras automáticas a cada 10s, todas salvas em um arquivo único por sessão.
   - **Única:** Uma leitura pontual, salva em arquivo próprio.
   - **Média:** Coleta 10 amostras (com 10s de intervalo), calcula a média e salva tudo em um arquivo próprio.
4. Os arquivos são salvos automaticamente na pasta do projeto.

## Estrutura dos Arquivos Gerados

### Modo Contínuo
- Cada vez que você entra no modo contínuo, um novo arquivo é criado (ex: `dados_sensor_solo_continuo_1.json`, `dados_sensor_solo_continuo_2.json`, ...).
- Todas as leituras dessa sessão ficam dentro do campo `leituras`:
```json
{
  "leituras": [
    { "umidade": 23.1, "temperatura": 25.0, ... },
    { "umidade": 23.2, "temperatura": 25.1, ... },
    ...
  ]
}
```

### Modo Única
- Cada leitura é salva em um arquivo separado, ex: `dados_sensor_solo_1.json`, `dados_sensor_solo_2.json`, ...

### Modo Média
- Cada média é salva em um arquivo separado, ex: `dados_sensor_solo_media_1.json`, `dados_sensor_solo_media_2.json`, ...
- O arquivo contém as 10 leituras e a média calculada:
```json
{
  "media": { "umidade": 23.2, "temperatura": 25.1, ... },
  "leituras": [ { ... }, { ... }, ... ],
  "timestamp": "2024-05-30T14:00:00"
}
```

## Observações Importantes
- **Troca de modo:** Sempre que você muda para o modo contínuo ou média, um novo arquivo é criado para aquela sessão.
- **Modo contínuo:** Não sobrescreve arquivos antigos, cada sessão é independente.
- **Modo média:** Delay de 10 segundos entre cada amostra.
- **Modo única:** Sempre gera um novo arquivo.
- **Unidades de medida** estão maiores e mais visíveis na interface.
- **Interface:** Visual limpo, responsivo e com alto contraste para uso em campo.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
