#!/usr/bin/env python3
"""
Leitor para Sensor de Solo RS485 Modbus 7 em 1 com Kivy - Interface Melhorada
Lê dados de umidade, temperatura, pH, condutividade elétrica, N, P, K
Adaptado para Android usando usbserial4a com interface gráfica moderna
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

# Importações para Android
try:
    import usb4a.usb as usb
    import usbserial4a.serial4a as serial4a
    ANDROID = True
except ImportError:
    import serial
    import minimalmodbus
    ANDROID = False

class ColoredCard(Widget):
    def __init__(self, color="#2196F3", **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex(self.color), 1)  # Fundo sólido
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
            # Sombra discreta
            Color(0, 0, 0, 0.08)
            RoundedRectangle(pos=(self.pos[0] + dp(2), self.pos[1] - dp(2)), 
                           size=self.size, radius=[dp(18)])

class DataCard(BoxLayout):
    def __init__(self, title, value, unit, color="#000000FF", **kwargs):
        super().__init__(orientation='vertical', spacing=dp(5), **kwargs)
        self.size_hint_y = None
        self.height = dp(140)
        self.padding = [dp(8), dp(8), dp(8), dp(8)]
        # Usar cor escura para contraste
        self.bg_color = color if color else "#000000FF"
        with self.canvas.before:
            Color(*get_color_from_hex(self.bg_color), 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
            Color(0, 0, 0, 0.18)
            self.shadow_rect = RoundedRectangle(pos=(self.pos[0] + dp(2), self.pos[1] - dp(2)), size=self.size, radius=[dp(18)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        # Content layout
        content = BoxLayout(orientation='vertical', spacing=dp(6), padding=[dp(10), dp(8)])
        # Ícone e título em uma linha
        title_row = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=dp(5), padding=[0,0,0,0])
        title_label = Label(
            text=title,
            font_size=dp(15),
            color=(1, 1, 1, 1),
            bold=True,
            halign='center',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        title_row.add_widget(title_label)
        content.add_widget(title_row)
        # Value com indicador de status
        value_row = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=dp(5))
        self.value_label = Label(
            text=f"{value}",
            font_size=dp(28),
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )
        self.value_label.bind(size=self.value_label.setter('text_size'))
        value_row.add_widget(self.value_label)
        # Indicador de status (círculo colorido)
        self.status_indicator = Widget(size_hint=(None, 1), width=dp(14))
        with self.status_indicator.canvas:
            Color(0, 1, 0, 1)  # Verde para OK
            self.status_circle = RoundedRectangle(pos=(0, 0), size=(dp(14), dp(14)), radius=[dp(7)])
        self.status_indicator.bind(pos=self._update_status_indicator)
        value_row.add_widget(self.status_indicator)
        content.add_widget(value_row)
        # Unit e timestamp
        info_row = BoxLayout(orientation='vertical', size_hint_y=0.25)
        unit_label = Label(
            text=unit,
            font_size=dp(18),
            color=(1, 1, 1, 0.95),
            halign='center',
            valign='middle'
        )
        unit_label.bind(size=unit_label.setter('text_size'))
        info_row.add_widget(unit_label)
        self.timestamp_label = Label(
            text="--:--:--",
            font_size=dp(10),
            color=(1, 1, 1, 0.8),
            halign='center',
            valign='middle'
        )
        self.timestamp_label.bind(size=self.timestamp_label.setter('text_size'))
        info_row.add_widget(self.timestamp_label)
        content.add_widget(info_row)
        self.add_widget(content)
    
    def _update_status_indicator(self, *args):
        center_y = self.status_indicator.center_y - dp(7)
        self.status_circle.pos = (self.status_indicator.right - dp(17), center_y)
    
    def update_value(self, value, timestamp=None):
        if isinstance(value, (int, float)) and value is not None:
            self.value_label.text = f"{value:.1f}"
            with self.status_indicator.canvas:
                self.status_indicator.canvas.clear()
                Color(0.2, 0.8, 0.2, 1)
                self.status_circle = RoundedRectangle(
                    pos=(self.status_indicator.right - dp(17), self.status_indicator.center_y - dp(7)), 
                    size=(dp(14), dp(14)), 
                    radius=[dp(7)]
                )
        else:
            self.value_label.text = "ERRO"
            with self.status_indicator.canvas:
                self.status_indicator.canvas.clear()
                Color(0.8, 0.2, 0.2, 1)
                self.status_circle = RoundedRectangle(
                    pos=(self.status_indicator.right - dp(17), self.status_indicator.center_y - dp(7)), 
                    size=(dp(14), dp(14)), 
                    radius=[dp(7)]
                )
        
        if timestamp:
            try:
                if 'T' in timestamp:
                    time_part = timestamp.split('T')[1][:8]
                    self.timestamp_label.text = time_part
                else:
                    self.timestamp_label.text = timestamp
            except:
                self.timestamp_label.text = "Agora"

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.shadow_rect.pos = (self.pos[0] + dp(2), self.pos[1] - dp(2))
        self.shadow_rect.size = self.size

class StatusCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10), **kwargs)
        self.size_hint_y = None
        self.height = dp(100)
        # Fundo preto puro para contraste
        self.bg_color = "#000000"
        with self.canvas.before:
            Color(*get_color_from_hex(self.bg_color), 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
            Color(0, 0, 0, 0.22)
            self.shadow_rect = RoundedRectangle(pos=(self.pos[0] + dp(2), self.pos[1] - dp(2)), size=self.size, radius=[dp(18)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        # Content centralizado
        content = BoxLayout(orientation='vertical', padding=[dp(20), dp(15)], size_hint=(1, 1))
        self.status_label = Label(
            text="Selecione um modo para iniciar",
            font_size=dp(20),
            color=(1, 1, 1, 1),
            bold=True,
            halign='center',
            valign='middle',
            size_hint=(1, 1)
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        content.add_widget(self.status_label)
        self.add_widget(content)
    
    def update_status(self, text, color="#000000"):
        self.status_label.text = text
        self.bg_color = color
        with self.canvas.before:
            Color(*get_color_from_hex(self.bg_color), 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
            Color(0, 0, 0, 0.22)
            self.shadow_rect = RoundedRectangle(pos=(self.pos[0] + dp(2), self.pos[1] - dp(2)), size=self.size, radius=[dp(18)])
        self._update_bg()

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.shadow_rect.pos = (self.pos[0] + dp(2), self.pos[1] - dp(2))
        self.shadow_rect.size = self.size

class ModernButton(Button):
    def __init__(self, bg_color="#2196F3", **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = dp(16)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(55)
        self.padding = [dp(8), 0]
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        self.bind(state=self.on_state_change)
        self.bg_color = bg_color
        self.pressed = False
        
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if not self.pressed:
                Color(0, 0, 0, 0.18)
                RoundedRectangle(
                    pos=(self.pos[0] + dp(2), self.pos[1] - dp(3)), 
                    size=self.size, 
                    radius=[dp(28)]
                )
            
            color = get_color_from_hex(self.bg_color)
            if self.pressed:
                Color(color[0] * 0.8, color[1] * 0.8, color[2] * 0.8, 1)
            else:
                Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(28)])
    
    def on_state_change(self, *args):
        self.pressed = self.state == 'down'
        self.update_graphics()

class SensorSolo7em1:
    def __init__(self, porta_com: str = None, endereco_slave: int = 1, baudrate: int = 4800):
        self.porta_com = porta_com
        self.endereco_slave = endereco_slave
        self.baudrate = baudrate
        self.instrumento = None
        self.serial_port = None
        self.dados = {}

        self.registradores = {
            'umidade': 0x0015,
            'temperatura': 0x0001,
            'ph': 0x0024,
            'condutividade': 0x0064,
            'nitrogenio': 0x0012,
            'fosforo': 0x0013,
            'potassio': 0x0014
        }

        self.registradores_alternativos = {
            'nitrogenio': [0x0004, 0x0012, 0x0025, 0x0030],
            'fosforo': [0x0005, 0x0013, 0x0026, 0x0031],
            'potassio': [0x0006, 0x0014, 0x0027, 0x0032]
        }

        self.conectar()

    def conectar(self):
        try:
            if ANDROID:
                usb_manager = usb.get_usb_manager()
                usb_device_list = usb.get_usb_device_list()
                
                if not usb_device_list:
                    print("Nenhum dispositivo USB encontrado")
                    return
                
                device = None
                for d in usb_device_list:
                    if d.getVendorId() == 6790 and d.getProductId() == 29987:
                        device = d
                        break
                
                if not device:
                    print("Dispositivo alvo (Vendor ID=6790, Product ID=29987) não encontrado")
                    return
                
                if not usb.has_usb_permission(device):
                    print("Solicitando permissão para acessar o dispositivo USB...")
                    usb.request_usb_permission(device)
                    timeout = 30
                    interval = 1
                    elapsed = 0
                    while not usb.has_usb_permission(device) and elapsed < timeout:
                        time.sleep(interval)
                        elapsed += interval
                    
                    if not usb.has_usb_permission(device):
                        print("Permissão USB não concedida. Reinicie o aplicativo.")
                        return
                
                print("Permissão USB concedida.")
                
                self.serial_port = serial4a.get_serial_port(
                    device.getDeviceName(),
                    self.baudrate,
                    8,
                    'N',
                    1,
                    timeout=2.0
                )
                self.serial_port.DEFAULT_READ_BUFFER_SIZE = 16 * 1024
                self.serial_port.USB_READ_TIMEOUT_MILLIS = 100
                
                if not self.serial_port.is_open:
                    self.serial_port.open()
                
                print(f"Conectado ao sensor via USB no Android em {device.getDeviceName()}")
            else:
                self.instrumento = minimalmodbus.Instrument(self.porta_com, self.endereco_slave)
                self.instrumento.serial.baudrate = self.baudrate
                self.instrumento.serial.bytesize = 8
                self.instrumento.serial.parity = serial.PARITY_NONE
                self.instrumento.serial.stopbits = 1
                self.instrumento.serial.timeout = 2.0
                self.instrumento.mode = minimalmodbus.MODE_RTU
                self.instrumento.clear_buffers_before_each_transaction = True
                print(f"Conectado ao sensor na porta {self.porta_com}")

        except Exception as e:
            print(f"Erro ao conectar: {e}")
            raise

    def _calcular_crc16(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc.to_bytes(2, byteorder='little')

    def _criar_comando_modbus(self, slave_addr, function_code, register_addr, register_count=1):
        cmd = bytearray([
            slave_addr,
            function_code,
            register_addr >> 8,
            register_addr & 0xFF,
            register_count >> 8,
            register_count & 0xFF,
        ])
        crc = self._calcular_crc16(cmd)
        cmd.extend(crc)
        return cmd

    def ler_registrador(self, endereco: int, fator_escala: float = 0.1, tentativas: int = 3) -> Optional[float]:
        for i in range(tentativas):
            try:
                if ANDROID:
                    self.serial_port.reset_input_buffer()
                    self.serial_port.reset_output_buffer()
                    time.sleep(0.2)
                    cmd = self._criar_comando_modbus(self.endereco_slave, 3, endereco)
                    self.serial_port.write(cmd)
                    time.sleep(0.1)
                    resposta = self.serial_port.read(7)
                    if len(resposta) >= 7 and resposta[0] == self.endereco_slave and resposta[1] == 3:
                        valor_bruto = (resposta[3] << 8) | resposta[4]
                        return valor_bruto * fator_escala
                    raise Exception(f"Resposta inválida: {resposta.hex() if resposta else 'vazia'}")
                else:
                    self.instrumento.serial.reset_input_buffer()
                    self.instrumento.serial.reset_output_buffer()
                    time.sleep(0.2)
                    valor_bruto = self.instrumento.read_register(endereco, 0)
                    return valor_bruto * fator_escala
            except Exception as e:
                if i == tentativas - 1:
                    print(f"Erro ao ler registrador {endereco}: {e}")
                    return None
                time.sleep(0.5)
        return None

    def ler_npk_alternativo(self, nutriente: str) -> Optional[float]:
        if nutriente not in self.registradores_alternativos:
            return None
        fatores = [0.1, 1.0, 10.0]
        for reg in self.registradores_alternativos[nutriente]:
            for fator in fatores:
                valor = self.ler_registrador(reg, fator)
                if valor is not None and valor > 0:
                    print(f"Encontrado {nutriente} no registrador 0x{reg:04X} com fator {fator}: {valor}")
                    return valor
        return 0.0

    def ler_todos_dados(self) -> Dict[str, float]:
        dados = {}
        fatores_escala = {
            'umidade': 0.1,
            'temperatura': 0.1,
            'ph': 0.1,
            'condutividade': 1.0,
            'nitrogenio': 1.0,
            'fosforo': 1.0,
            'potassio': 1.0
        }

        for parametro in ['umidade', 'temperatura', 'ph', 'condutividade']:
            endereco = self.registradores[parametro]
            fator = fatores_escala.get(parametro, 1.0)
            valor = self.ler_registrador(endereco, fator)
            dados[parametro] = valor
            time.sleep(0.3)

        for nutriente in ['nitrogenio', 'fosforo', 'potassio']:
            endereco = self.registradores[nutriente]
            fator = fatores_escala.get(nutriente, 1.0)
            valor = self.ler_registrador(endereco, fator)
            if valor is None or valor == 0:
                valor = self.ler_npk_alternativo(nutriente)
            dados[nutriente] = valor
            time.sleep(0.3)

        dados['timestamp'] = datetime.now().isoformat()
        return dados

    def salvar_dados(self, dados: Dict[str, float], arquivo_base: str = "dados_sensor_solo"):
        try:
            contagem = 1
            arquivo = f"{arquivo_base}_{contagem}.json"
            while os.path.exists(arquivo):
                contagem += 1
                arquivo = f"{arquivo_base}_{contagem}.json"
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            print(f"Dados salvos em {arquivo}")
            return arquivo
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            return None

    def salvar_dados_continuo(self, dados: Dict[str, float], arquivo_base: str = "dados_sensor_solo_continuo"):
        try:
            contagem = 1
            arquivo = f"{arquivo_base}_{contagem}.json"
            while os.path.exists(arquivo):
                contagem += 1
                arquivo = f"{arquivo_base}_{contagem}.json"
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            print(f"Dados salvos em {arquivo}")
            return arquivo
        except Exception as e:
            print(f"Erro ao salvar dados contínuos: {e}")
            return None

    def salvar_media(self, leituras: List[Dict], media: Dict, arquivo_base: str = "dados_sensor_solo"):
        try:
            contagem = 1
            arquivo = f"{arquivo_base}_{contagem}.json"
            while os.path.exists(arquivo):
                contagem += 1
                arquivo = f"{arquivo_base}_media_{contagem}.json"
            media_completa = {'media': media, 'leituras': leituras, 'timestamp': media['timestamp']}
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(media_completa, f, indent=2, ensure_ascii=False)
            print(f"Média salva em {arquivo}")
            return arquivo
        except Exception as e:
            print(f"Erro ao salvar média: {e}")
            return None

    def desconectar(self):
        try:
            if ANDROID and self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            elif self.instrumento and self.instrumento.serial.is_open:
                self.instrumento.serial.close()
            print("Conexão fechada")
        except Exception as e:
            print(f"Erro ao fechar conexão: {e}")

class SensorApp(App):
    sensor_porta_com = None
    modo = None
    arquivo_continuo_atual = None
    leituras_continuas = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not ANDROID:
            self.sensor = SensorSolo7em1(porta_com=self.sensor_porta_com)
        else:
            self.sensor = SensorSolo7em1()
        self.leituras = []
        self.file_input = TextInput(
            text="dados_sensor_solo", 
            multiline=False,
            font_size=dp(14),
            size_hint=(1, 0.8)
        )
        self.current_mode = None
        self.data_cards = {}

    def build(self):
        # Layout principal com gradiente de fundo
        main_layout = BoxLayout(orientation='vertical', spacing=dp(15), padding=[dp(10), dp(10)])
        with main_layout.canvas.before:
            Color(0.93, 0.94, 0.97, 1)
            RoundedRectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)
        # Header centralizado
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=dp(5), padding=[0,0,0,0])
        icon_widget = Widget(size_hint=(None, None), size=(dp(54), dp(54)), pos_hint={'center_x': 0.5})
        with icon_widget.canvas:
            Color(0.2, 0.6, 0.2, 1)
            RoundedRectangle(pos=(0, 0), size=(dp(54), dp(54)), radius=[dp(27)])
        # Centralizar ícone
        icon_box = BoxLayout(size_hint_y=None, height=dp(54))
        icon_box.add_widget(Widget())
        icon_box.add_widget(icon_widget)
        icon_box.add_widget(Widget())
        header.add_widget(icon_box)
        # Centralizar textos
        title = Label(
            text="Sensor de Solo 7 em 1",
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(32),
            color=(0.13, 0.13, 0.13, 1),
            halign='center',
            valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        subtitle = Label(
            text="Monitoramento Inteligente de Cultivos",
            font_size=dp(13),
            size_hint_y=None,
            height=dp(20),
            color=(0.4, 0.4, 0.4, 1),
            halign='center',
            valign='middle'
        )
        subtitle.bind(size=subtitle.setter('text_size'))
        header.add_widget(title)
        header.add_widget(subtitle)
        main_layout.add_widget(header)
        # Status Card melhorado e centralizado
        self.status_card = StatusCard()
        self.status_card.update_status("Selecione um modo para iniciar", "#000000")
        main_layout.add_widget(self.status_card)
        scroll = ScrollView(size_hint=(1, 0.5))
        self.data_grid = GridLayout(
            cols=2 if self.root_window and self.root_window.width > 600 else 1,
            spacing=dp(12),
            size_hint_y=None,
            padding=[0, dp(10)]
        )
        self.data_grid.bind(minimum_height=self.data_grid.setter('height'))
        self.create_data_cards()
        scroll.add_widget(self.data_grid)
        main_layout.add_widget(scroll)
        self.progress_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=0, spacing=dp(5))
        self.progress_label = Label(
            text="", 
            size_hint_y=None, 
            height=dp(25), 
            font_size=dp(13),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        )
        progress_container = BoxLayout(size_hint_y=None, height=dp(25), padding=[dp(10), 0])
        self.progress_bar = ProgressBar(max=10, value=0, size_hint_y=None, height=dp(8))
        with self.progress_bar.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            RoundedRectangle(pos=self.progress_bar.pos, size=self.progress_bar.size, radius=[dp(4)])
        progress_container.add_widget(self.progress_bar)
        self.progress_layout.add_widget(self.progress_label)
        self.progress_layout.add_widget(progress_container)
        main_layout.add_widget(self.progress_layout)
        buttons_layout = GridLayout(cols=3, spacing=dp(12), size_hint_y=None, height=dp(65), padding=[0,0,0,0])
        btn_continuo = ModernButton(text="📊 Contínuo", bg_color="#4CAF50")
        btn_continuo.bind(on_press=lambda x: self.set_modo('continuo'))
        buttons_layout.add_widget(btn_continuo)
        btn_unica = ModernButton(text="📸 Única", bg_color="#2196F3")
        btn_unica.bind(on_press=lambda x: self.set_modo('unica'))
        buttons_layout.add_widget(btn_unica)
        btn_media = ModernButton(text="📈 Média", bg_color="#FF9800")
        btn_media.bind(on_press=lambda x: self.set_modo('media'))
        buttons_layout.add_widget(btn_media)
        main_layout.add_widget(buttons_layout)
        config_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
        btn_arquivo = ModernButton(text="📁 Configurações", bg_color="#9C27B0")
        btn_arquivo.bind(on_press=self.show_file_popup)
        config_layout.add_widget(btn_arquivo)
        btn_info = ModernButton(text="ℹ️ Info", bg_color="#607D8B")
        btn_info.bind(on_press=self.show_info_popup)
        btn_info.size_hint_x = 0.3
        config_layout.add_widget(btn_info)
        main_layout.add_widget(config_layout)
        self.create_popups()
        Clock.schedule_interval(self.update, 10.0)
        return main_layout
    
    def _update_bg(self, *args):
        if hasattr(self, 'root') and self.root:
            self.root.canvas.before.clear()
            with self.root.canvas.before:
                Color(0.93, 0.94, 0.97, 1)
                RoundedRectangle(pos=self.root.pos, size=self.root.size)

    def create_data_cards(self):
        card_configs = [
            ("💧 Umidade", 0, "%", "#2196F3"),
            ("🌡️ Temperatura", 0, "°C", "#FF5722"),
            ("⚗️ pH", 0, "", "#9C27B0"),
            ("⚡ Condutividade", 0, "μS/cm", "#607D8B"),
            ("🌿 Nitrogênio", 0, "mg/kg", "#4CAF50"),
            ("🧪 Fósforo", 0, "mg/kg", "#FF9800"),
            ("💎 Potássio", 0, "mg/kg", "#795548")
        ]
        
        params = ['umidade', 'temperatura', 'ph', 'condutividade', 'nitrogenio', 'fosforo', 'potassio']
        
        for i, (title, value, unit, color) in enumerate(card_configs):
            card = DataCard(title, value, unit, color)
            self.data_cards[params[i]] = card
            self.data_grid.add_widget(card)
    
    def create_popups(self):
        # Popup de configurações de arquivo
        file_content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
    
        file_content.add_widget(Label(
        text="Nome do arquivo base:",
        size_hint_y=None,
        height=dp(30),
        font_size=dp(14)
        ))
    
        file_content.add_widget(self.file_input)
    
        file_buttons = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
    
        btn_ok = ModernButton(text="OK", bg_color="#4CAF50")
        btn_ok.bind(on_press=lambda x: self.file_popup.dismiss())
    
        btn_cancel = ModernButton(text="Cancelar", bg_color="#F44336")
        btn_cancel.bind(on_press=lambda x: self.file_popup.dismiss())
    
        file_buttons.add_widget(btn_ok)
        file_buttons.add_widget(btn_cancel)
        file_content.add_widget(file_buttons)
    
        self.file_popup = Popup(
            title="Configurações de Arquivo",
            content=file_content,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
    
        # Popup de informações
        info_content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
    
        info_text = """
        📊 Sensor de Solo 7 em 1

        Este aplicativo permite monitorar:
        - Umidade do solo (%)
        - Temperatura (°C)  
        - pH do solo
        - Condutividade elétrica (μS/cm)
        - Nitrogênio (mg/kg)
        - Fósforo (mg/kg)
        - Potássio (mg/kg)

        Modos de operação:
        📊 Contínuo: Leituras automáticas a cada 10s
        📸 Única: Uma leitura pontual
        📈 Média: Média de 10 leituras

        Desenvolvido para sensores Modbus RTU
        """
    
        info_label = Label(
            text=info_text,
            text_size=(None, None),
            halign='left',
            valign='top',
            font_size=dp(12)
        )
    
        info_content.add_widget(info_label)
    
        btn_close = ModernButton(text="Fechar", bg_color="#607D8B")
        btn_close.bind(on_press=self.close_info_popup)
        info_content.add_widget(btn_close)
    
        self.info_popup = Popup(
            title="Informações do App",
            content=info_content,
            size_hint=(0.9, 0.7),
            auto_dismiss=True
        )

    def show_file_popup(self, instance):
        self.file_popup.open()
    
    def show_info_popup(self, instance):
        self.info_popup.open()
    
    def close_info_popup(self, instance):
        self.info_popup.dismiss()

    def set_modo(self, modo):
        self.modo = modo
        self.current_mode = modo
        if modo != 'continuo':
            self.arquivo_continuo_atual = None
            self.leituras_continuas = None
        if modo == 'continuo':
            self.status_card.update_status("🔄 Modo Contínuo - Lendo a cada 10s", "#11151A")
            self.progress_layout.height = 0
            # Criar novo arquivo para a sessão
            arquivo_base = self.file_input.text if self.file_input.text else "dados_sensor_solo_continuo"
            contagem = 1
            arquivo = f"{arquivo_base}_{contagem}.json"
            while os.path.exists(arquivo):
                contagem += 1
                arquivo = f"{arquivo_base}_{contagem}.json"
            self.arquivo_continuo_atual = arquivo
            self.leituras_continuas = []
        elif modo == 'unica':
            self.status_card.update_status("📸 Realizando leitura única...", "#1565C0")
            self.progress_layout.height = 0
            self.leitura_unica()
        elif modo == 'media':
            self.status_card.update_status("📈 Modo Média - Coletando 10 amostras", "#FF9800")
            self.progress_layout.height = dp(60)
            self.leituras = []
            self.progress_bar.value = 0
            Clock.schedule_once(self.iniciar_modo_media, 0)

    def iniciar_modo_media(self, dt):
        Clock.schedule_once(self.modo_media, 0)

    def update(self, dt):
        if self.modo == 'continuo':
            try:
                dados = self.sensor.ler_todos_dados()
                self.update_data_cards(dados)
                # Acumular leituras na sessão
                if self.leituras_continuas is not None:
                    self.leituras_continuas.append(dados)
                    # Salvar todas as leituras da sessão no arquivo
                    with open(self.arquivo_continuo_atual, 'w', encoding='utf-8') as f:
                        json.dump({'leituras': self.leituras_continuas}, f, indent=2, ensure_ascii=False)
                    timestamp = dados.get('timestamp', 'N/A').split('T')[1][:8] if 'T' in dados.get('timestamp', '') else 'N/A'
                    self.status_card.update_status(f"✅ Última leitura: {timestamp}", "#000000")
            except Exception as e:
                self.status_card.update_status(f"❌ Erro: {str(e)[:50]}...", "#B71C1C")
        elif self.modo is None:
            # Não faz nada até o modo ser escolhido
            pass

    def update_data_cards(self, dados):
        for param, card in self.data_cards.items():
            if param in dados:
                card.update_value(dados[param])

    def leitura_unica(self):
        try:
            dados = self.sensor.ler_todos_dados()
            self.update_data_cards(dados)
            arquivo_base = self.file_input.text if self.file_input.text else "dados_sensor_solo"
            arquivo_salvo = self.sensor.salvar_dados(dados, arquivo_base)
            if arquivo_salvo:
                self.status_card.update_status(f"✅ Leitura salva: {os.path.basename(arquivo_salvo)}", "#11151A")
            else:
                self.status_card.update_status("❌ Erro ao salvar leitura", "#B71C1C")
        except Exception as e:
            self.status_card.update_status(f"❌ Erro: {str(e)[:50]}...", "#B71C1C")
        self.current_mode = None

    def modo_media(self, dt):
        if len(self.leituras) < 10:
            try:
                dados = self.sensor.ler_todos_dados()
                self.leituras.append(dados)
                self.update_data_cards(dados)
                # Atualizar progresso
                progress = len(self.leituras)
                self.progress_bar.value = progress
                self.progress_label.text = f"Coletando amostra {progress}/10..."
                Clock.schedule_once(self.modo_media, 10.0)  # 10 segundos entre leituras para modo média
            except Exception as e:
                self.status_card.update_status(f"❌ Erro: {str(e)[:50]}...", "#B71C1C")
        else:
            self.calcular_media()

    def calcular_media(self):
        if not self.leituras:
            self.status_card.update_status("❌ Nenhuma leitura para calcular média", "#B71C1C")
            return

        media = {'timestamp': datetime.now().isoformat()}
        params = ['umidade', 'temperatura', 'ph', 'condutividade', 'nitrogenio', 'fosforo', 'potassio']
        
        for param in params:
            valores = [d[param] for d in self.leituras if d[param] is not None and isinstance(d[param], (int, float))]
            media[param] = round(sum(valores) / len(valores), 2) if valores else None

        # Atualizar cards com média
        self.update_data_cards(media)
        
        # Salvar média
        arquivo_base = self.file_input.text if self.file_input.text else "dados_sensor_solo"
        arquivo_salvo = self.sensor.salvar_media(self.leituras, media, arquivo_base)
        
        if arquivo_salvo:
            self.status_card.update_status(f"✅ Média salva: {os.path.basename(arquivo_salvo)}", "#11151A")
        else:
            self.status_card.update_status("❌ Erro ao salvar média", "#B71C1C")
        
        # Reset
        self.leituras = []
        self.current_mode = None
        self.progress_layout.height = 0
        self.progress_bar.value = 0
        self.progress_label.text = ""

    def on_stop(self):
        self.sensor.desconectar()

if __name__ == "__main__":
    if not ANDROID:
        import serial.tools.list_ports
        portas = list(serial.tools.list_ports.comports())
        if not portas:
            print("Nenhuma porta serial encontrada. Conecte o sensor e tente novamente.")
            exit(1)
        print("Portas seriais disponíveis:")
        for i, porta in enumerate(portas):
            print(f"[{i}] {porta.device} - {porta.description}")
        escolha = input("Escolha o número da porta a ser utilizada: ")
        try:
            idx = int(escolha)
            porta_escolhida = portas[idx].device
        except (ValueError, IndexError):
            print("Escolha inválida.")
            exit(1)
        SensorApp.sensor_porta_com = porta_escolhida
        SensorApp().run()
    else:
        SensorApp().run()