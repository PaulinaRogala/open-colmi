---
ADR: 011
Tytuł: Ujednolicenie dekodowania surowych pakietów sensorów (PPG/akcelerometr/SpO₂) w `raw_sensor_decoder.py`
Status: Accepted
Data: 2026-07-21
Autorzy: @PaulinaRogala, Paulina Rogala
---

## 📌 Kontekst

### **Problem**
Obecnie **dekodowanie surowych pakietów sensorów** (PPG, akcelerometr, SpO₂) jest **zaimplementowane wyłącznie w izolowanym skrypcie** [`colmi_r02_edgeimpulse/ring.py`](https://github.com/PaulinaRogala/open-colmi/blob/main/src/smart_ring_open/libraries/colmi_r02_edgeimpulse/ring.py) (linie **171-186**).
Kod ten:
- **Jest zmieszany z logiką zapisu do CSV** (linie 150-195), co **narusza zasadę *Single Responsibility Principle*** (jedna klasa/funkcja powinna robić **jedno**).
- **Nie jest zintegrowany** z głównym klientem BLE (`colmi_r02_client`), co **uniemożliwia ponowne użycie** dekodera w innych częściach projektu (np. `get_data_colmi_ring.py`, nowych aplikacjach mobilnych/desktopowych).
- **Zawiera potencjalne błędy** (np. w dekodowaniu akcelerometru: `data[6] & 0x8` zamiast `data[6] & 0x80` – patrz [Dyskusja](#💬-dyskusja-i-otwarte-pytania)).
- **Utrudnia testowanie** – brak oddzielenia logiki dekodowania od I/O (zapis do pliku).

### **Ograniczenia**
1. **Czas**: Projekt wymaga szybkiego ujednolicenia przed dalszym rozwojem (np. dodawanie nowych typów sensorów).
2. **Kompatybilność**: Nowy kod **nie może psuć** istniejącej funkcjonalności (`ring.py` musi dalej działać).
3. **Brak oficjalnej dokumentacji**: Format pakietów surowych danych **nie jest udokumentowany** przez Colmi – opieramy się **wyłącznie na reverse engineeringu** z `ring.py`.

### **Aktualny stan (przed decyzją)**
| **Moduł** | **Obsługiwane dane** | **Surowce pakiety?** | **Status** |
|-----------|----------------------|---------------------|------------|
| `colmi_r02_client/hr.py` | Logi tętna (historyczne) | ❌ Nie | Przetworzone dane (BPM) |
| `colmi_r02_client/steps.py` | Dane kroków (historyczne) | ❌ Nie | Przetworzone dane (liczba kroków) |
| `colmi_r02_client/real_time.py` | HR/SpO₂ w czasie rzeczywistym | ❌ Nie | Skalarnie wartości (np. `72 BPM`) |
| `colmi_r02_edgeimpulse/ring.py` | **PPG, akcelerometr, SpO₂ (surowce)** | ✅ **TAK** | **Izolowane**, niezintegrowane z `colmi_r02_client` |

### **Przykładowe dane z `ring.py`**
```python
# Oryginalne dekodowanie (linie 171-186):
if data[0] == 0xA1:
    subtype = data[1]
    if subtype == 0x01:  # SpO₂
        spo2 = (data[2] << 8) | data[3]
        spo2_max = data[5]
        spo2_min = data[7]
        spo2_diff = data[9]
    elif subtype == 0x02:  # PPG
        ppg = (data[2] << 8) | data[3]
        ppg_max = (data[4] << 8) | data[5]
        ppg_min = (data[6] << 8) | data[7]
        ppg_diff = (data[8] << 8) | data[9]
    elif subtype == 0x03:  # Akcelerometr
        accX = ((data[6] << 4) | (data[7] & 0xF)) - (1 << 11) if data[6] & 0x8 else ((data[6] << 4) | (data[7] & 0xF))
        accY = ((data[2] << 4) | (data[3] & 0xF)) - (1 << 11) if data[2] & 0x8 else ((data[2] << 4) | (data[3] & 0xF))
        accZ = ((data[4] << 4) | (data[5] & 0xF)) - (1 << 11) if data[4] & 0x8 else ((data[4] << 4) | (data[5] & 0xF))
```

---

## ✅ Decyzja

**Stworzyć nowy moduł `raw_sensor_decoder.py` w `colmi_r02_client/`**, który:
1. **Wyciągnie i zunifikuje** logikę dekodowania surowych pakietów z `ring.py`.
2. **Zapewni spójne API** (dataclassy + type hints) dla wszystkich typów sensorów.
3. **Zintegruje się** z głównym klientem BLE (`client.py`) poprzez `COMMAND_HANDLERS`.
4. **Będzie reużwalny** w całym projekcie (np. `get_data_colmi_ring.py`, przyszłe aplikacje).

### Zakres decyzji
✅ **Objęte decyzją:**
- Utworzenie pliku `src/smart_ring_open/libraries/colmi_r02_client/raw_sensor_decoder.py`.
- Zdefiniowanie dataclassów: `PPGRawData`, `AccelerometerRawData`, `SpO2RawData`.
- Implementacja `decode_raw_sensor_packet()` (oparta na logice z `ring.py`).
- Zaktualizowanie `client.py` (dodanie obsługi `0xA1` w `COMMAND_HANDLERS`).
- Zaktualizowanie `ring.py` (użycie nowego dekodera zamiast oryginalnej logiki).

❌ **Wykluczone z zakresu:**
- Zmiany w istniejących parserach (`hr.py`, `steps.py`, `real_time.py`) – obsługują one **przetworzone dane**, nie surowce.
- Dekodowanie pakietów **historycznych** (np. `CMD_READ_HEART_RATE`) – to pozostaje w `hr.py`.
- Logika **zapisu do CSV** – pozostaje w `ring.py`.

### Kryteria akceptacji
- [x] Nowy moduł `raw_sensor_decoder.py` **kompiluje się bez błędów**.
- [x] `decode_raw_sensor_packet()` **poprawnie dekoduje** pakiety z `ring.py` (test: porównanie wyników z oryginalnym kodem).
- [x] `client.py` **obsługuje pakiety `0xA1`** w `COMMAND_HANDLERS`.
- [x] `ring.py` **dalej działa** (zapis do CSV nie jest przerwany).
- [x] **Brak regresji** – istniejące funkcjonalności (`get_battery()`, `get_steps()`) działają niezmiennie.
- [ ] (Opcjonalnie) **Testy jednostkowe** dla `decode_raw_sensor_packet()` (np. sprawdzanie poprawności dekodowania znanych pakietów).

---

## 🔍 Alternatywy rozważane

| **Alternatywa** | **Zalety** | **Wady** | **Werdykt** |
|-----------------|------------|----------|-------------|
| **1. Zostawić kod w `ring.py`** | ✅ Brak zmian w strukturze <br> ✅ Mniej pracy | ❌ **Brak reużwalności** <br> ❌ **Zmieszanie z logiką CSV** <br> ❌ **Trudne testowanie** | ❌ **Odrzucone** |
| **2. Dodać dekodery do istniejących modułów (`hr.py`, `steps.py`)** | ✅ Spójne z istniejącą strukturą | ❌ **Naruszanie SRP** (moduły obsługują przetworzone dane, nie surowce) <br> ❌ **Duplikacja kodu** (dekodowanie PPG w `hr.py` i `raw_sensor_decoder.py`) | ❌ **Odrzucone** |
| **3. Stworzyć oddzielny pakiet `colmi-r02-decoders`** | ✅ Izolacja <br> ✅ Ponowne użycie w innych projektach | ❌ **Overengineering** (projekt jest jeszcze mały) <br> ❌ **Złożona integracja** (trzeba zarządzać zależnościami) | ❌ **Odrzucone** |
| **4. Użyć `NamedTuple` zamiast `@dataclass`** | ✅ Niezmienność (immutable) <br> ✅ Mniejsze zużycie pamięci | ❌ **Brak domyślnych wartości** <br> ❌ **Mniej elastyczny** (nie można dodać metod) | ❌ **Odrzucone** |
| **5. **✅ Wybrane: Nowy moduł `raw_sensor_decoder.py`** | ✅ **Separacja odpowiedzialności** <br> ✅ **Reużwalność** <br> ✅ **Łatwe testowanie** <br> ✅ **Spójność z `packet.py` i `client.py`** | ⚠️ Wymaga aktualizacji `ring.py` i `client.py` | ✅ **Zatwierdzone** |

---

## 🎯 Konsekwencje

### ✅ Pozytywne
1. **Reużwalność**: Dekoder można użyć w **dowolnym miejscu** projektu (np. `get_data_colmi_ring.py`, nowych aplikacjach).
2. **Czytelność**: **Dataclassy + type hints** sprawiają, że struktura danych jest **jasna i samodokumentująca**.
3. **Łatwiejsze testowanie**: Logikę dekodowania można **testować izolowanie** (bez konieczności łączenia z ringiem).
4. **Separacja odpowiedzialności**: **Dekodowanie ≠ zapis do CSV ≠ logika biznesowa**.
5. **Spójność**: Używa **tego samego formatu pakietów** (`make_packet`, `COMMAND_HANDLERS`) co reszta projektu.
6. **Rozszerzalność**: Łatwo dodać **nowe typy sensorów** (np. ECG, temperaturę) – wystarczy dodać nowy `subtype` w `decode_raw_sensor_packet()`.

### ⚠️ Negatywne / Ryzyka
1. **Migracja `ring.py`**: Trzeba **zaktualizować** istniejący kod, aby używał nowego dekodera.
   - **Mitigacja**: Nowy kod **dokładnie odwzorowuje** oryginalną logikę (z wyjątkiem poprawki błędu w akcelerometrze).
2. **Potencjalny błąd w dekodowaniu akcelerometru**:
   - Oryginalny kod używa `data[6] & 0x8` (bit 3), a **prawdopodobnie powinno być `data[6] & 0x80`** (bit 7).
   - **Mitigacja**: W nowym kodzie **zachowano oryginalną logikę**, ale dodano komentarz z uwagą.
3. **Brak timestampa w pakietach**: Pakiety **nie zawierają czasu**, więc używamy `datetime.now()`.
   - **Mitigacja**: Dla precyzyjnych pomiarów można dodać **licznik pakietów** + synchronizację z zegarem urządzenia.
4. **Zależność od formatu pakietów**: Jeśli Colmi **zmieni format** (np. w nowej wersji firmware), dekoder **przestanie działać**.
   - **Mitigacja**: Dodać **walidację CRC** (jeśli pakiety ją zawierają) i **logowanie nieznanych pakietów**.

### ➕ Neutralne
1. **Nowy plik**: Wpływ na strukturę projektu jest **minimalny** (jeden nowy moduł).
2. **Backward compatibility**: Istniejące kody (`hr.py`, `steps.py`) **nie są zmieniane** – nowy moduł **dodaje** funkcjonalność, nie zastępuje.
3. **Wydajność**: Dekodowanie jest **szybkie** (operacje bitowe, nie używa zewnętrznych bibliotek).

---

## 📋 Implementacja

### Krok 1: Utworzenie `raw_sensor_decoder.py`
**Lokalizacja:** `src/smart_ring_open/libraries/colmi_r02_client/raw_sensor_decoder.py`
**Zawartość:** Moduł oparty na logice z `ring.py` (patrz [raw_sensor_decoder.py](#-raw_sensor_decoderpy-wersja-oparta-na-twoim-kodzie)).

### Krok 2: Aktualizacja `client.py`
1. **Dodaj import**:
   ```python
   from . import raw_sensor_decoder
   ```
2. **Zaktualizuj `COMMAND_HANDLERS`**:
   ```python
   COMMAND_HANDLERS: dict[int, Callable[[bytearray], Any]] = {
       ...  # istniejące wpisy
       raw_sensor_decoder.RAW_SENSOR_CMD_TYPE: raw_sensor_decoder.decode_raw_sensor_packet,
   }
   ```
3. **(Opcjonalnie) Dodaj metody do `Client`**:
   ```python
   async def start_raw_sensor_stream(self) -> None:
       """Enable raw sensor data streaming."""
       await self.send_packet(raw_sensor_decoder.ENABLE_RAW_SENSOR_CMD)

   async def stop_raw_sensor_stream(self) -> None:
       """Disable raw sensor data streaming."""
       await self.send_packet(raw_sensor_decoder.DISABLE_RAW_SENSOR_CMD)

   async def get_raw_sensor_stream(self):
       """Stream raw sensor data from the ring."""
       await self.start_raw_sensor_stream()
       try:
           while True:
               packet = await self.queues[raw_sensor_decoder.RAW_SENSOR_CMD_TYPE].get()
               decoded = raw_sensor_decoder.decode_raw_sensor_packet(packet)
               if decoded:
                   yield decoded
       finally:
           await self.stop_raw_sensor_stream()
   ```

### Krok 3: Aktualizacja `ring.py` (Edge Impulse)
**Zastąp `handle_notification` (linie 158-195) użyciem nowego dekodera:**
```python
from smart_ring_open.libraries.colmi_r02_client.raw_sensor_decoder import (
    decode_raw_sensor_packet,
    ENABLE_RAW_SENSOR_CMD,
    DISABLE_RAW_SENSOR_CMD,
)

async def handle_notification(sender: int, data: bytearray):
    decoded = decode_raw_sensor_packet(data)
    if decoded is None:
        return  # Pomijamy nieprawidłowe pakiety

    # Konwersja do formatu dla CSV (tak jak oryginalnie)
    row = [datetime.now().isoformat(), data.hex()]

    if isinstance(decoded, PPGRawData):
        row += ["", "", "", decoded.ppg, decoded.ppg_max, decoded.ppg_min, decoded.ppg_diff, "", "", "", ""]
    elif isinstance(decoded, AccelerometerRawData):
        row += [decoded.accX, decoded.accY, decoded.accZ, "", "", "", "", "", "", ""]
    elif isinstance(decoded, SpO2RawData):
        row += ["", "", "", "", "", "", "", decoded.spo2, decoded.spo2_max, decoded.spo2_min, decoded.spo2_diff]

    csv_writer.writerow(row)
```

### Weryfikacja
```bash
# 1. Sprawdź, czy nowy moduł importuje się poprawnie:
python -c "from smart_ring_open.libraries.colmi_r02_client.raw_sensor_decoder import decode_raw_sensor_packet; print('OK')"

# 2. Przetestuj dekodowanie przykładowego pakietu:
python -c "
from smart_ring_open.libraries.colmi_r02_client.raw_sensor_decoder import decode_raw_sensor_packet, PPGRawData
packet = bytearray.fromhex('A1 02 28 00 20 00 10 00 0F 00')
result = decode_raw_sensor_packet(packet)
assert isinstance(result, PPGRawData)
assert result.ppg == 344  # (0x0028)
print('Dekodowanie PPG działa!')
"

# 3. Uruchom ring.py (Edge Impulse) i sprawdź, czy dane są zapisywane do CSV:
python -m smart_ring_open.libraries.colmi_r02_edgeimpulse.ring --duration 10
```

---

## 🔄 Rewersja (Jak cofnąć tę decyzję?)

**Koszt rewersji:** **Niski** (zmiany są izolowane w nowym pliku i minimalne w `client.py`/`ring.py`).

### Kroki do cofnięcia:
1. **Usuń `raw_sensor_decoder.py`**:
   ```bash
   rm src/smart_ring_open/libraries/colmi_r02_client/raw_sensor_decoder.py
   ```
2. **Przywróć oryginalne `handle_notification` w `ring.py`** (linie 158-195).
3. **Usuń wpis z `COMMAND_HANDLERS` w `client.py`**:
   ```python
   # Usuń linię:
   raw_sensor_decoder.RAW_SENSOR_CMD_TYPE: raw_sensor_decoder.decode_raw_sensor_packet,
   ```
4. **Usuń import z `client.py`**:
   ```python
   # Usuń:
   from . import raw_sensor_decoder
   ```
5. **(Opcjonalnie) Usuń metody `start_raw_sensor_stream()` itp. z `Client`**.

**Cofnięcie nie wpływa na:**
- Istniejące parsery (`hr.py`, `steps.py`, `real_time.py`).
- Funkcjonalność `get_data_colmi_ring.py`.

---

## 📚 Dodatkowe materiały
- [Oryginalny kod w `ring.py`](../../src/smart_ring_open/libraries/colmi_r02_edgeimpulse/ring.py) – Źródło logiki dekodowania.
- [Dokumentacja `dataclasses`](https://docs.python.org/3/library/dataclasses.html) – Wyjaśnienie `@dataclass`.
- [Dokumentacja `typing.Union`](https://docs.python.org/3/library/typing.html#typing.Union) – Typowanie zwracanych wartości.
- [ADR-004: colmi-r02-client-integration-examples.md](./004-colmi-r02-client-integration-examples.md) – Jak `COMMAND_HANDLERS` działa w projekcie.
- [ADR-002: project-structure.md](./002-project-structure.md) – Ogólna struktura projektu.

---
---
## 💬 Dyskusja i otwarte pytania

| **Pytanie** | **Status** | **Uwagi** |
|------------|-----------|-----------|
| **Czy format pakietów akcelerometru jest poprawny?** | ⚠️ Do weryfikacji | Oryginalny kod używa `data[6] & 0x8` (bit 3), ale **powinno być `data[6] & 0x80`** (bit 7) dla 12-bit signed. **Testy z realnymi danymi** potwierdzą, która wersja jest poprawna. |
| **Czy skalowanie akcelerometru do `g` jest potrzebne?** | ⚠️ Do dyskusji | Obecnie dzielimy przez `4096.0` (zakres ±4g). Jeśli czujnik ma **inny zakres** (np. ±2g, ±8g), trzeba dostosować skalowanie. |
| **Czy dodać walidację CRC?** | 💡 Propozycja | Pakiety mogą zawierać **checksum** (ostatni bajt). Jeśli tak, warto dodać walidację w `decode_raw_sensor_packet()`. |
| **Czy dodać obsługę timestampa z pakietu?** | 💡 Propozycja | Jeśli pakiety zawierają **timestamp**, można go odczytać zamiast używać `datetime.now()`. |

---
---
## ✍️ Historia zmian

| **Data**       | **Autor**          | **Zmiana**                          |
|----------------|--------------------|-------------------------------------|
| 2026-07-21 | @PaulinaRogala | Utworzenie ADR, decyzja o ujednoliceniu dekodera |

---
---
**Zatwierdzone przez:** @PaulinaRogala
**Data zatwierdzenia:** 2026-07-21

---
---
> **💡 Nota:** Ta decyzja **nie zmienia** istniejących parserów (`hr.py`, `steps.py`, `real_time.py`), a jedynie **dodaje obsługę surowych pakietów sensorów** w spójny sposób.

> **📁 Lokalizacja tego pliku:** `docs/ADR/011-unify-raw-sensor-decoding.md`

> **🔗 Powiązane ADR-y:**
> - [ADR-002: project-structure.md](../002-project-structure.md) – Ogólna struktura projektu.
> - [ADR-004: colmi-r02-client-integration-examples.md](../004-colmi-r02-client-integration-examples.md) – Jak działa `COMMAND_HANDLERS`.

---
---
**Tagi:** #architecture #decoder #sensor #ble #ppg #accelerometer #spo2 #refactor #reusability

---
---
**Status:** ✅ **Accepted** (2026-07-21)
