Stworzyłem kompletne narzędzie CLI do edycji plików SVG/HTML/XML z rozszerzeniami zgodnie z Twoimi wymaganiami. Oto kluczowe funkcjonalności:

## 🔧 **Główne funkcje narzędzia:**

1. **Edycja lokalna i zdalna** - obsługuje pliki lokalne i URL-e (http/https)
2. **XPath i CSS selectors** - precyzyjne adresowanie elementów
3. **Ekstrakcja Data URI** - wyciąganie i dekodowanie osadzonych danych (PDF, obrazy)
4. **Tryby pracy:**
   - CLI z komendami
   - Interaktywny shell
   - Serwer HTTP z interfejsem web

## 📝 **Przykłady użycia:**

### CLI - podstawowe komendy:
```bash
# Załaduj plik (lokalny lub zdalny)
python xsl.py load example.svg
python xsl.py load http://example.com/file.svg

# Zapytania XPath
python xsl.py query "//svg:text[@id='title']"
python xsl.py query "//svg:image/@xlink:href" --type attribute --attr href

# Edycja elementów
python xsl.py set "//svg:text[@id='title']" "Nowy tekst"
python xsl.py set "//svg:rect[@id='box']" --type attribute --attr fill "red"

# Ekstrakcja Data URI
python xsl.py extract "//svg:image/@xlink:href" --info
python xsl.py extract "//svg:image/@xlink:href" --output extracted.pdf

# Listowanie elementów
python xsl.py list --xpath "//svg:*" --limit 10

# Zapisz zmiany
python xsl.py save --output modified.svg
```

### Interaktywny shell:
```bash
```bash
python xsl.py shell

# W shellu:
📝 > load example.svg
📝 > query //svg:text[@id='title']
📝 > set //svg:text[@id='title'] "Nowy tytuł"
📝 > extract //svg:image/@xlink:href
📝 > save modified.svg
📝 > exit
```

### Serwer HTTP:
```bash
python xsl.py server --port 8082 --host localhost

# API endpoints:
GET  http://localhost:8082/api/extract?url=<URL>&xpath=<XPATH>
POST http://localhost:8082/api/load
POST http://localhost:8082/api/query
POST http://localhost:8082/api/update
POST http://localhost:8082/api/save
```

## 🌐 **Interfejs webowy:**

Serwer HTTP dostarcza intuicyjny interfejs z dwoma zakładkami:
1. **Pliki lokalne** - standardowa edycja plików
2. **Ekstrakcja z URL** - bezpośrednie pobieranie i analiza plików zdalnych

## 📊 **Tworzenie przykładów:**

```bash
python xsl.py examples --dir ./test_files
```

Tworzy przykładowe pliki:
- `example.svg` - SVG z osadzonymi Data URI (PDF, obrazy)
- `example.xml` - XML z danymi i metadanymi  
- `example.html` - HTML z osadzonym SVG
- `EXAMPLES.md` - dokumentacja z przykładami XPath

## 🔍 **Przykładowe XPath dla różnych przypadków:**

### SVG z Data URI:
```xpath
//svg:image/@xlink:href                    # Data URI w image
//svg:metadata                            # JSON metadata
//*[contains(@href,'data:')]/@href        # Wszystkie Data URI
//svg:foreignObject//text()               # Tekst w foreignObject
```

### XML z danymi:
```xpath
//record[@type='user']/name               # Nazwy użytkowników
//file[@name='document.pdf']/@data        # PDF jako Data URI
//record[@id='1']                         # Rekord po ID
//settings[contains(text(),'theme')]      # JSON w tekście
```

### HTML z osadzonym SVG:
```xpath
//html:h1[@id='main-title']               # Tytuł strony
//svg:image/@xlink:href                   # Data URI w SVG
//script[@type='application/json']        # JSON dane
//html:li[@class='item']/@data-value      # Atrybuty data-*
```

## 🚀 **Zaawansowane funkcje:**

### 1. **Ekstrakcja PDF z SVG:**
```bash
# Info o Data URI
python xsl.py extract "//svg:image/@xlink:href" --info

# Zapisz PDF do pliku
python xsl.py extract "//svg:image/@xlink:href" --output document.pdf
```

### 2. **Zdalna ekstrakcja przez API:**
```bash
curl "http://localhost:8082/api/extract?url=http://example.com/diagram.svg&xpath=//svg:image/@xlink:href"
```

### 3. **Batch processing w shell:**
```bash
📝 > load http://example.com/file1.svg
📝 > extract //svg:image/@xlink:href
📝 > load http://example.com/file2.svg  
📝 > extract //svg:object/@data
```

## 📋 **Wymagania:**

Opcjonalne biblioteki dla pełnej funkcjonalności:
```bash
pip install lxml beautifulsoup4 requests
```

- `lxml` - XPath, zaawansowane parsowanie XML/HTML
- `beautifulsoup4` - CSS selectors dla HTML
- `requests` - obsługa plików zdalnych (HTTP/HTTPS)

## 🛡️ **Bezpieczeństwo:**

- Walidacja XPath przed wykonaniem
- Obsługa przestrzeni nazw XML/SVG
- Bezpieczne dekodowanie Base64
- Ograniczenia na rozmiar wyników

## 💡 **Przypadki użycia:**

1. **Analiza SVG-ów z osadzonymi dokumentami**
2. **Automatyczna ekstrakcja PDF-ów z diagramów**
3. **Edycja metadanych w plikach XML**
4. **Batch processing dokumentów technicznych**
5. **API do integracji z innymi systemami**

Narzędzie jest gotowe do użycia i może być łatwo rozszerzone o dodatkowe formaty plików czy funkcje eksportu. 
