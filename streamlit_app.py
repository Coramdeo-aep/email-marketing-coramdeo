import os
import base64
import mimetypes
from datetime import datetime
from PIL import Image
import streamlit as st
from supabase import create_client
import resend

# --- Configurações seguras ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = "Associação Coramdeo <contato@coramdeo.site>"

# --- Inicializa Clients ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
resend.api_key = RESEND_API_KEY

# --- Templates HTML Salvos ---
TEMPLATES_HTML = {
    "Convite para Associado": "templates/associado.html",
    "Voluntariado": "templates/voluntarios.html",
    "Boas-vindas!": "templates/boas-vindas.html",
    "Profissional Colaborador": "templates/profissionais.html"
}

# --- Layout ---
st.set_page_config(page_title="Coram Deo - Envio de E-mails", layout="wide")

# --- Cabeçalho com logo ---
logo = Image.open("logo_coramdeo.png")
st.image(logo, width=180)
st.title("Painel de Envio de E-mails")
st.markdown("Gerencie suas campanhas com profissionalismo e segurança.")
st.markdown("---")

# --- Sidebar Filtros ---
st.sidebar.header("Filtros de envio")

filtro_resposta = st.sidebar.radio("Enviar para:", ["Todos", "Somente não respondidos", "Somente já respondidos"])

interesses_opcoes = [
    ("Todos", "todos"),
    ("Associado", "associado"),
    ("Voluntário", "voluntario"),
    ("Doação", "doacao"),
    ("Matrícula", "matricula"),
    ("Parceria", "parceria"),
    ("Outros", "outros")
]
filtro_interesses = st.sidebar.multiselect(
    "Filtrar por interesse:",
    options=interesses_opcoes,
    default=[("Associado", "associado")],
    format_func=lambda x: x[0]
)

# --- Corpo Principal ---
st.subheader("Detalhes do e-mail")

col_esquerda, col_direita = st.columns([1, 2], gap="large")

with col_esquerda:
    assunto = st.text_input("Assunto do e-mail", "Convite para se tornar associado da Associação Coram Deo")

    corpo_padrao = st.text_area("Mensagem (usada se não enviar HTML)",
                                 "Olá! Agradecemos seu interesse na Associação Coram Deo.",
                                 height=100)

    st.markdown("### Escolher corpo do e-mail")
    opcao_template = st.selectbox(
        "Escolha um modelo salvo:",
        ["Nenhum (usar texto ou upload)"] + list(TEMPLATES_HTML.keys())
    )

    corpo_html_upload = st.file_uploader("Ou enviar corpo HTML (.html ou .txt)", type=["html", "txt"])

    arquivos_anexo = st.file_uploader("Anexar Arquivos (.pdf, .png, .jpg, .jpeg)",
                                      type=["pdf", "png", "jpg", "jpeg"],
                                      accept_multiple_files=True)

    enviar = st.button("Enviar e-mails", use_container_width=True)

with col_direita:
    corpo_email_template = ""
    if opcao_template != "Nenhum (usar texto ou upload)":
        caminho_template = TEMPLATES_HTML[opcao_template]
        with open(caminho_template, "r", encoding="utf-8") as f:
            corpo_email_template = f.read()
        st.markdown("#### Visualização do e-mail:")
        st.components.v1.html(corpo_email_template, height=600, scrolling=True)
    elif corpo_html_upload:
        corpo_email_template = corpo_html_upload.read().decode("utf-8")
        st.markdown("#### Visualização do e-mail enviado:")
        st.components.v1.html(corpo_email_template, height=600, scrolling=True)
    else:
        corpo_email_template = f"<p>{corpo_padrao}</p>"
        st.markdown("#### Visualização do e-mail em texto simples:")
        st.write(corpo_email_template, unsafe_allow_html=True)

# --- Buscar contatos ---
def buscar_contatos():
    query = supabase.table("contatos").select("*")
    if filtro_resposta == "Somente não respondidos":
        query = query.eq("respondido", False)
    elif filtro_resposta == "Somente já respondidos":
        query = query.eq("respondido", True)

    contatos = query.execute().data
    interesses = [i[1] for i in filtro_interesses]
    if "todos" not in interesses:
        contatos = [c for c in contatos if c.get("interesse", "").lower() in interesses]
    return contatos

# --- Deduplicar contatos ---
def deduplicar_por_email(contatos):
    dedup = {}
    for c in contatos:
        email = c['email'].strip().lower()
        if email in dedup:
            dedup[email]["interesses"].append(c.get("interesse", ""))
        else:
            dedup[email] = {
                "id": c["id"],
                "email": email,
                "nome": c.get("nome", ""),
                "interesses": [c.get("interesse", "")],
                "respondido": c.get("respondido", False)
            }
    return list(dedup.values())

# --- Ação de envio ---
if enviar:
    st.info("🔄 Buscando contatos...")
    contatos_raw = buscar_contatos()
    contatos = deduplicar_por_email(contatos_raw)

    if not contatos:
        st.warning("Nenhum contato encontrado com os filtros aplicados.")
    else:
        st.success(f"{len(contatos)} contatos encontrados. Iniciando envio...")

        # Anexos
        anexos = []
        for arquivo in arquivos_anexo:
            mime_type, _ = mimetypes.guess_type(arquivo.name)
            mime_type = mime_type or "application/octet-stream"
            base64_content = base64.b64encode(arquivo.read()).decode('utf-8')
            anexos.append({
                "filename": arquivo.name,
                "content": base64_content,
                "type": mime_type,
                "disposition": "attachment"
            })

        # Envio
        for contato in contatos:
            try:
                corpo_email = corpo_email_template.format(**contato)
                response = resend.Emails.send({
                    "from": EMAIL_FROM,
                    "to": [contato["email"]],
                    "subject": assunto,
                    "html": corpo_email,
                    "attachments": anexos if anexos else None
                })

                if "id" in response and not contato["respondido"]:
                    supabase.table("contatos").update({
                        "respondido": True,
                        "data_resposta": datetime.utcnow().isoformat()
                    }).eq("id", contato["id"]).execute()

                st.success(f"Enviado para {contato['nome']} - {contato['email']}")

            except Exception as e:
                st.error(f"Erro com {contato['email']}: {str(e)}")
