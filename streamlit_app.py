import streamlit as st
from supabase import create_client
import resend
from datetime import datetime
import base64
import mimetypes
import io

# --- Configurações iniciais ---
SUPABASE_URL = "https://trpgnvhwfnqrvywqkdbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
EMAIL_FROM = "Associação Coramdeo <contato@coramdeo.site>"
RESEND_API_KEY = "re_hrEKpqGm_EbMgXQuW2oMWyXW26w38beu5"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
resend.api_key = RESEND_API_KEY

st.set_page_config(page_title="Envio de Emails • Coram Deo", layout="wide")

st.title("📬 Envio de Emails - Coram Deo")

# --- Interface ---
col1, col2 = st.columns(2)

with col1:
    filtro_resposta = st.radio("Enviar para:", ["Todos", "Somente não respondidos", "Somente já respondidos"])

with col2:
    filtro_interesses = st.multiselect(
        "Interesses:",
        ["associado", "voluntario", "doacao", "matricula", "parceria", "outros"],
        default=["associado"]
    )

titulo_input = st.text_input("Assunto do email:", "Convite para se tornar associado da Associação Coramdeo")
mensagem_input = st.text_area("Mensagem (se não enviar HTML):", "Olá! Agradecemos seu interesse na Associação Coramdeo.")

st.divider()

upload_html = st.file_uploader("💡 Corpo do Email (opcional - .html)", type=["html", "txt"])
upload_arquivo = st.file_uploader("📎 Anexar Arquivos (PDF/Imagens)", accept_multiple_files=True, type=["pdf", "jpg", "jpeg", "png"])

# --- Funções ---
def buscar_contatos():
    query = supabase.table("contatos").select("*")
    if filtro_resposta == "Somente não respondidos":
        query = query.eq("respondido", False)
    elif filtro_resposta == "Somente já respondidos":
        query = query.eq("respondido", True)

    contatos = query.execute().data
    return [c for c in contatos if c.get("interesse", "").lower() in filtro_interesses]

def deduplicar_por_email(contatos):
    dedup = {}
    for c in contatos:
        email = c["email"].strip().lower()
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

def preparar_anexos(arquivos):
    anexos = []
    for file in arquivos:
        mime_type, _ = mimetypes.guess_type(file.name)
        content = base64.b64encode(file.read()).decode('utf-8')
        anexos.append({
            "filename": file.name,
            "content": content,
            "type": mime_type or "application/octet-stream",
            "disposition": "attachment"
        })
    return anexos

# --- Envio ---
if st.button("🚀 Enviar Emails"):
    with st.spinner("Processando..."):
        contatos_raw = buscar_contatos()
        contatos_unicos = deduplicar_por_email(contatos_raw)

        if not contatos_unicos:
            st.warning("Nenhum contato encontrado com os filtros aplicados.")
        else:
            st.success(f"Iniciando envio para {len(contatos_unicos)} contatos únicos...")

            # Corpo do email
            if upload_html:
                corpo_email_template = upload_html.read().decode("utf-8")
            else:
                corpo_email_template = f"<p>{mensagem_input}</p>"

            anexos = preparar_anexos(upload_arquivo) if upload_arquivo else None

            for contato in contatos_unicos:
                try:
                    corpo_email = corpo_email_template.format(**contato)

                    response = resend.Emails.send({
                        "from": EMAIL_FROM,
                        "to": [contato["email"]],
                        "subject": titulo_input,
                        "html": corpo_email,
                        "attachments": anexos
                    })

                    if "id" in response and not contato["respondido"]:
                        supabase.table("contatos").update({
                            "respondido": True,
                            "data_resposta": datetime.utcnow().isoformat()
                        }).eq("id", contato["id"]).execute()

                    st.info(f"✅ Enviado para {contato['nome']} - {contato['email']}")
                except Exception as e:
                    st.error(f"❌ Erro com {contato['email']}: {str(e)}")

# --- Resetar uploads ---
if st.button("🧹 Limpar Anexos e HTML"):
    st.experimental_rerun()
