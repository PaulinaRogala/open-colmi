# 📚 Architecture Decision Records (ADR)

> **Czym jest ADR?**
> *Architecture Decision Record* (ADR) to **lekkodostępny dokument**, który **rejestruje ważne decyzje architektoniczne** podjęte w trakcie rozwoju projektu.
> Każdy plik w tym folderze opisuje **kontekst, decyzję, alternatywy, konsekwencje i implementację** danej decyzji.

---

## 🎯 Cel tego katalogu

Celem tego folderu jest:
✅ **Utrwalenie wiedzy** – aby nikt nie musiał od nowa odkrywać, dlaczego podjęto daną decyzję.
✅ **Ułatwienie onboardingu** – nowi członkowie zespołu mogą szybko zrozumieć, dlaczego projekt wygląda tak, a nie inaczej.
✅ **Zapewnienie spójności** – decyzje są dokumentowane **przed** implementacją, co zmniejsza ryzyko chaosu.
✅ **Umożliwienie rewersji** – jeśli decyzja okaże się błędna, wiemy **jak i dlaczego** ją cofnąć.

---

## 📁 Struktura folderu

```
docs/ADR/
├── README.md          # Ten plik – wprowadzenie do ADR
├── 000-template.md    # Szablon dla nowych ADR-ów
├── 001-use-uv-as-python-environment.md  # Decyzja: Użycie uv
└── 011-unify-raw-sensor-decoding.md    # Decyzja: Ujednolicenie dekodowania surowych pakietów sensorów
```

---

## 📝 Jak dodać nowy ADR?

### Krok 1: Skopiuj szablon
```bash
# Na Windows (CMD)
copy docs\ADR\000-template.md docs\ADR\0XX-[krotki-tytul].md
```

### Krok 2: Uzupełnij plik
- **Numer ADR**: Następny wolny numer (np. `012`, `013`, ...).
- **Tytuł**: Krótki, deskryptywny (np. `use-pydantic-for-data-validation`).
- **Status**: `Proposed` (do dyskusji) lub `Accepted` (zatwierdzony).
- **Autorzy**: Twoje imię/nick (np. `@paulina`, `Paulina Rogala`).
- **Data**: Aktualna data (YYYY-MM-DD).

### Krok 3: Wypełnij sekcje
1. **Kontekst** – Dlaczego ta decyzja była potrzebna?
2. **Decyzja** – Co zdecydowano?
3. **Alternatywy** – Co rozważano i dlaczego odrzucono?
4. **Konsekwencje** – Jakie są plusy, minusy i ryzyka?
5. **Implementacja** – Jak wdrożyć tę decyzję?
6. **Rewersja** – Jak cofnąć, jeśli coś pójdzie nie tak?

### Krok 4: Zatwierdź i dodaj do repozytorium
```bash
git add docs/ADR/0XX-[krotki-tytul].md
git commit -m "docs(adr): dodano ADR-0XX – [tytuł]"
git push
```

---

## 📋 Zasady pisania ADR-ów

### ✅ Do whatever:
- **Bądź zwięzły** – ADR powinien być **krótki** (1-2 strony).
- **Używaj prostego języka** – unikanie żargonu, chyba że jest konieczny.
- **Dokumentuj kontekst** – wyjaśnij **dlaczego** podjęto decyzję, a nie **co** zrobiono (to jest w kodzie).
- **Używaj formatu Markdown** – czytelność jest kluczowa.
- **Linkuj do źródeł** – jeśli oparłeś się na artykule, benchmarku lub dyskusji, dodaj link.

### ❌ Don't:
- **Pisz powieści** – ADR nie jest place na dygresje.
- **Opisuj implementację w szczegółach** – to powinno być w kodzie i dokumentacji technicznej.
- **Zmieniaj przeszłych ADR-ów** – jeśli decyzja się zmieniła, stwórz **nowy ADR** (`Superseded` lub `Deprecated`).
- **Używaj ADR dla drobnych decyzji** – np. „wybrałem czcionkę 12px” nie wymaga ADR.

---

## 🔍 Kiedy tworzyć ADR?

Stwórz ADR, jeśli decyzja:
✔️ **Miała znaczący wpływ na architekturę** (np. wybór frameworka, baza danych).
✔️ **Była trudna do podjęcia** (wiele alternatyw, kompromisy).
✔️ **Będzie miała długoterminowe konsekwencje** (np. migracja z Poetry na uv).
✔️ **Wymagała dyskusji zespołu** (nie jest oczywista).

**Nie tworzyć ADR dla:**
❌ Drobnych zmian w kodzie (np. refaktor funkcji).
❌ Decyzji estetycznych (np. kolorystyka UI).
❌ Standardowych praktyk (np. „używamy `black` do formatowania”).

---

## 📊 Lista decyzji

| Numer | Tytuł | Status | Data | Autor |
|-------|-------|--------|------|-------|
| [000](./000-template.md) | Szablon ADR | 📄 Template | - | - |
| [011](./011-unify-raw-sensor-decoding.md) | Ujednolicenie dekodowania surowych pakietów sensorów | ✅ Accepted | 2026-07-21 | @PaulinaRogala |

---

## 🔗 Przydatne linki
- [ADR GitHub](https://adr.github.io/) – Oficjalna dokumentacja ADR.
- [ADR Template](https://github.com/adr/adr-tools/blob/master/adr-template.md) – Oryginalny szablon.
- [Example ADRs](https://github.com/joel-costigliola/adr-examples) – Przykłady z prawdziwych projektów.

---

## 💬 Pytania i odpowiedzi

### ❓ **Dlaczego nie używamy wiki lub Confluence?**
- ADR to **pliki Markdown** w repozytorium – łatwe do versionowania, przeglądania i edytowania.
- Nie wymagają zewnętrznych narzędzi (GitHub/GitLab wystarczy).
- Są **blisko kodu**, więc programiści naturalnie je czytają.

### ❓ **Czy ADR może być odrzucony?**
- Tak! Jeśli decyzja okaże się błędna, można:
  1. Utworzyć nowy ADR z **`Status: Deprecated`** i wyjaśnić dlaczego.
  2. Utworzyć nowy ADR z **`Status: Superseded`** i wskazać nową decyzję.

### ❓ **Jak szukać ADR-ów?**
- Przeglądaj folder `docs/ADR/` w repozytorium.
- Użyj `grep`/`rg` (ripgrep):
  ```bash
  rg "Status: Accepted" docs/ADR/
  ```

---

## 🎯 Podsumowanie

> **„Jeśli nie zapiszesz decyzji, za 6 miesięcy nikt nie będzie pamiętał, dlaczego coś zrobiono tak, a nie inaczej.”**

ADR to **prosty, skuteczny sposób** na dokumentowanie **kluczowych decyzji projektowych**.
Dzięki nim:
- **Nowi członkowie zespołu** szybko rozumieją projekt.
- **Zespół unika powtarzania tych samych dyskusji**.
- **Decyzje są przejrzyste i uzasadnione**.

**Zachęcamy do tworzenia ADR-ów dla wszystkich ważnych decyzji architektonicznych!** 🚀

---

*Inspirowane przez [ADR GitHub](https://adr.github.io/).*
