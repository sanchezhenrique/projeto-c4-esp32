from machine import Pin, I2C, PWM
import ssd1306
import time
import random

# Configuração do OLED
i2c = I2C(0, scl=Pin(23), sda=Pin(22))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Configuração do Buzzer
buzzer = PWM(Pin(15))
buzzer.duty_u16(0)

# Configuração dos Switches (Binário: 8, 4, 2, 1)
sw8 = Pin(5, Pin.IN, Pin.PULL_UP)
sw4 = Pin(18, Pin.IN, Pin.PULL_UP)
sw2 = Pin(19, Pin.IN, Pin.PULL_UP)
sw1 = Pin(21, Pin.IN, Pin.PULL_UP)

# Botão Enter/Confirmar
sw_enter = Pin(4, Pin.IN, Pin.PULL_UP)

def beep(freq, dur):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)
    time.sleep_ms(dur)
    buzzer.duty_u16(0)

def ler_binario():
    b8 = 0 if sw8.value() else 1
    b4 = 0 if sw4.value() else 1
    b2 = 0 if sw2.value() else 1
    b1 = 0 if sw1.value() else 1
    return b8 * 8 + b4 * 4 + b2 * 2 + b1

# --- INICIALIZAÇÃO DO JOGO ---
oled.fill(0)
oled.text("COUNTER STRIKE", 10, 10)
oled.text("C4 PLANTADA", 32, 32)
oled.show()

for f in [1000, 1400, 1800]:
    beep(f, 120)
    time.sleep_ms(50)

time.sleep(1)

# --- CONFIGURAÇÕES DO JOGO ---
tempo_restante_ms = 40000  # 40 segundos
defusada = False
estagio_atual = 1
total_estagios = 3

codigo = random.randint(1, 15)

# Variáveis de controle de tempo (ticks)
last_loop_time = time.ticks_ms()
last_beep_time = time.ticks_ms()
last_display_time = time.ticks_ms()
buzzer_ativo = False

# Controle do estado do botão Enter (para evitar múltiplos cliques travados)
last_enter_val = 1 

# --- LOOP PRINCIPAL DA BOMBA ---
while tempo_restante_ms > 0:
    current_time = time.ticks_ms()
    
    # Delta de tempo (tempo real decorrido)
    dt = time.ticks_diff(current_time, last_loop_time)
    last_loop_time = current_time

    # O tempo corre normalmente
    tempo_restante_ms -= dt

    if tempo_restante_ms <= 0:
        break

    input_atual = ler_binario()
    enter_val = sw_enter.value()

    # DETECÇÃO DO BOTÃO ENTER (GND quando pressionado)
    # Verifica se o botão passou de SOLTO (1) para PRESSIONADO (0)
    if enter_val == 0 and last_enter_val == 1:
        time.sleep_ms(50) # Pequeno debounce para evitar mau contato
        
        if input_atual == codigo:
            # ACERTOU O CÓDIGO!
            if estagio_atual == total_estagios:
                defusada = True
                break
            else:
                estagio_atual += 1
                
                # Animação rápida de acerto
                oled.fill(1)
                oled.show()
                beep(2000, 100)
                beep(2500, 100)
                
                # Novo código aleatório
                novo_codigo = random.randint(1, 15)
                while novo_codigo == codigo:
                    novo_codigo = random.randint(1, 15)
                codigo = novo_codigo
                
                # Reseta o timer de loop para desconsiderar o tempo parado nos beeps
                last_loop_time = time.ticks_ms()
                last_beep_time = time.ticks_ms()
                last_enter_val = sw_enter.value()
                continue
        else:
            # ERROU! Penalidade imediata de 5 segundos (5000ms)
            tempo_restante_ms -= 5000
            beep(400, 400) # Som grave de erro

    # Atualiza o estado anterior do Enter para o próximo ciclo
    last_enter_val = enter_val

    # --- GERENCIAMENTO DO BUZZER (NÃO-BLOQUEANTE) ---
    tempo_seg = tempo_restante_ms / 1000

    if tempo_seg > 20:
        freq_bip, duracao_bip, intervalo_bip = 2600, 40, 1000
    elif tempo_seg > 10:
        freq_bip, duracao_bip, intervalo_bip = 2800, 50, 500
    elif tempo_seg > 5:
        freq_bip, duracao_bip, intervalo_bip = 3000, 60, 250
    else:
        freq_bip, duracao_bip, intervalo_bip = 3200, 70, 125

    if time.ticks_diff(current_time, last_beep_time) >= intervalo_bip:
        buzzer.freq(freq_bip)
        buzzer.duty_u16(32768)
        last_beep_time = current_time
        buzzer_ativo = True

    if buzzer_ativo and time.ticks_diff(current_time, last_beep_time) >= duracao_bip:
        buzzer.duty_u16(0)
        buzzer_ativo = False

    # --- ATUALIZAÇÃO DO DISPLAY ---
    if time.ticks_diff(current_time, last_display_time) >= 100:
        oled.fill(0)
        oled.text("C4 MULTI-DESARME", 5, 0)
        oled.text("FASE: {}/{}".format(estagio_atual, total_estagios), 5, 18)
        
        codigo_hex = hex(codigo)[2:].upper()
        oled.text("CODIGO (HEX): " + codigo_hex, 5, 34)
        
        # Mostra o tempo restante em segundos
        oled.text("TEMPO: {:.1f}s".format(max(0.0, tempo_seg)), 5, 50)
        oled.show()
        last_display_time = current_time

buzzer.duty_u16(0)

# --- TELA DE RESULTADO ---
oled.fill(0)

if defusada:
    for f in [3000, 2600, 2200, 1800]:
        beep(f, 150)
    oled.text("DESARMADO!", 32, 20)
    oled.text("COUNTER WIN", 20, 40)
else:
    for _ in range(5):
        oled.fill(1)
        oled.show()
        buzzer.freq(120)
        buzzer.duty_u16(50000)
        time.sleep_ms(100)
        oled.fill(0)
        oled.show()
        buzzer.duty_u16(0)
        time.sleep_ms(100)

    oled.text("BOOM!", 45, 20)
    oled.text("TERRORISTS WIN", 8, 40)

oled.show()
buzzer.deinit()
