# Coram Deo – Painel de Envio de E-mails

Este é um aplicativo interno da Associação Coram Deo desenvolvido para facilitar o envio segmentado e profissional de e-mails a contatos armazenados no Supabase. Ele permite escolher modelos prontos, personalizar mensagens, anexar arquivos e visualizar a mensagem antes do envio.

## Funcionalidades

* Filtro por interesse e status de resposta
* Seleção de modelos HTML internos
* Upload manual de mensagens personalizadas
* Pré-visualização completa do conteúdo do e-mail
* Suporte a anexos em PDF e imagem
* Marcação automática de contatos como respondidos

## Tecnologias

* **Streamlit** – Interface interativa
* **Supabase** – Armazenamento de dados
* **Resend** – Plataforma de envio de e-mails
* **Python 3.10+**

## Estrutura Esperada

```
projeto/
├── app.py
├── logo_coramdeo.png
├── templates/
│   ├── associado.html
│   ├── voluntarios.html
│   ├── profissionais.html
│   └── boas-vindas.html
```

## Variáveis de Ambiente

O app depende das seguintes variáveis de ambiente, configuráveis localmente ou via plataforma (ex.: Streamlit Cloud):

```env
SUPABASE_URL=...
SUPABASE_KEY=...
RESEND_API_KEY=...
```

## Execução Local

```bash
# Instale os requisitos
pip install -r requirements.txt

# Execute o aplicativo
streamlit run app.py
```

## Objetivo

Este sistema foi desenvolvido para agilizar a comunicação da Coram Deo com seus contatos e interessados, assegurando consistência visual, rastreabilidade e usabilidade mesmo por usuários sem experiência técnica.
