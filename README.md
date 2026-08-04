# Cotações do Tesouro Direto

Este repositório contém um dashboard estático web para acompanhar os preços dos títulos do Tesouro Direto brasileiro.

O funcionamento do projeto é baseado em um fluxo de trabalho automatizado:
- Um script em Python (`update_data.py`) busca os dados mais recentes a partir do CSV oficial disponibilizado pelo governo, processa as informações dos títulos e salva os resultados em um arquivo local chamado `dados.json`.
- A interface da aplicação (`index.html`) é construída com HTML, CSS e JavaScript puros (Vanilla), que consome o arquivo `dados.json` para exibir as cotações atualizadas em uma tabela simples.
- A automação é feita utilizando GitHub Actions através do arquivo `update.yml`. O fluxo de trabalho é executado de hora em hora, roda o script Python para atualizar os dados, realiza o commit e o push das alterações do `dados.json` (caso existam) e, em seguida, faz o deploy da página estática automaticamente no GitHub Pages.
