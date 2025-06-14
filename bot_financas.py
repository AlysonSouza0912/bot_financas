
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import pandas as pd
import os
import nest_asyncio
import asyncio
from datetime import datetime
import re

TOKEN = os.getenv('TOKEN')
ARQUIVO = 'gastos.csv'

def detectar_categoria(msg):
    msg = msg.lower()
    categorias = {
        'Mercado': ['mercado', 'supermercado', 'compras'],
        'Alimentação': ['restaurante', 'lanche', 'comida', 'almoço', 'jantar'],
        'Transporte': ['uber', 'gasolina', 'ônibus', 'metrô'],
        'Lazer': ['cinema', 'festa', 'bar', 'show'],
        'Contas': ['luz', 'água', 'internet', 'aluguel'],
        'Receita': ['recebi', 'salário', 'ganhei']
    }
    for categoria, palavras in categorias.items():
        for palavra in palavras:
            if palavra in msg:
                return categoria
    return 'Outros'

def salvar_gasto(user, message):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    categoria = detectar_categoria(message)
    novo_registro = {
        'Usuario': user,
        'DataHora': data,
        'Mensagem': message,
        'Categoria': categoria
    }
    if os.path.exists(ARQUIVO):
        df = pd.read_csv(ARQUIVO)
        df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
    else:
        df = pd.DataFrame([novo_registro])
    df.to_csv(ARQUIVO, index=False)

def extrair_valor(msg):
    valores = re.findall(r'\d+(?:[.,]\d+)?', msg)
    if valores:
        return float(valores[0].replace(',', '.'))
    return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá! Sou seu bot de finanças. Me envie seus gastos!')

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(ARQUIVO):
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return
    user = update.message.from_user.username
    df = pd.read_csv(ARQUIVO)
    df_user = df[df['Usuario'] == user]

    total_receitas = 0
    total_despesas = 0

    for _, row in df_user.iterrows():
        valor = extrair_valor(row['Mensagem'])
        if row['Categoria'] == 'Receita':
            total_receitas += valor
        elif row['Categoria'] != 'Outros':
            total_despesas += valor

    saldo_total = total_receitas - total_despesas

    resposta = (
        f"📊 Seu saldo aproximado:\n\n"
        f"💰 Total de Receitas: R$ {total_receitas:.2f}\n"
        f"💸 Total de Despesas: R$ {total_despesas:.2f}\n"
        f"🧾 Saldo Final: R$ {saldo_total:.2f}"
    )

    await update.message.reply_text(resposta)

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(ARQUIVO):
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return
    user = update.message.from_user.username
    df = pd.read_csv(ARQUIVO)
    df_user = df[df['Usuario'] == user]

    categorias_totais = {}

    for _, row in df_user.iterrows():
        valor = extrair_valor(row['Mensagem'])
        if valor > 0:
            categorias_totais[row['Categoria']] = categorias_totais.get(row['Categoria'], 0) + valor

    if not categorias_totais:
        await update.message.reply_text("Nenhum valor numérico encontrado nas suas mensagens.")
        return

    resposta = "📋 *Resumo por Categoria:*\n\n"
    for categoria, total in categorias_totais.items():
        resposta += f"🔸 {categoria}: R$ {total:.2f}\n"

    await update.message.reply_text(resposta, parse_mode='Markdown')

async def relatorio_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(ARQUIVO):
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Use o comando assim: /relatorio_mes 06/2025")
        return

    user = update.message.from_user.username
    periodo = context.args[0]
    try:
        mes, ano = periodo.split('/')
    except:
        await update.message.reply_text("Formato incorreto. Use: /relatorio_mes 06/2025")
        return

    df = pd.read_csv(ARQUIVO)
    df_user = df[df['Usuario'] == user]

    df_user['DataHora'] = pd.to_datetime(df_user['DataHora'], errors='coerce')
    df_user = df_user[(df_user['DataHora'].dt.month == int(mes)) & (df_user['DataHora'].dt.year == int(ano))]

    categorias_totais = {}

    for _, row in df_user.iterrows():
        valor = extrair_valor(row['Mensagem'])
        if valor > 0:
            categorias_totais[row['Categoria']] = categorias_totais.get(row['Categoria'], 0) + valor

    if not categorias_totais:
        await update.message.reply_text("Nenhum valor encontrado nesse mês.")
        return

    resposta = f"📆 Resumo de {mes}/{ano}:\n\n"
    for categoria, total in categorias_totais.items():
        resposta += f"🔸 {categoria}: R$ {total:.2f}\n"

    await update.message.reply_text(resposta)

async def relatorio_ano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(ARQUIVO):
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Use o comando assim: /relatorio_ano 2025")
        return

    user = update.message.from_user.username
    ano = context.args[0]

    df = pd.read_csv(ARQUIVO)
    df_user = df[df['Usuario'] == user]

    df_user['DataHora'] = pd.to_datetime(df_user['DataHora'], errors='coerce')
    df_user = df_user[df_user['DataHora'].dt.year == int(ano)]

    categorias_totais = {}

    for _, row in df_user.iterrows():
        valor = extrair_valor(row['Mensagem'])
        if valor > 0:
            categorias_totais[row['Categoria']] = categorias_totais.get(row['Categoria'], 0) + valor

    if not categorias_totais:
        await update.message.reply_text("Nenhum valor encontrado nesse ano.")
        return

    resposta = f"📆 Resumo Anual {ano}:\n\n"
    for categoria, total in categorias_totais.items():
        resposta += f"🔸 {categoria}: R$ {total:.2f}\n"

    await update.message.reply_text(resposta)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    message = update.message.text
    salvar_gasto(user, message)
    await update.message.reply_text(f"Gasto recebido e salvo! ✅")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("relatorio", relatorio))
app.add_handler(CommandHandler("relatorio_mes", relatorio_mes))
app.add_handler(CommandHandler("relatorio_ano", relatorio_ano))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

nest_asyncio.apply()

print("Bot financeiro rodando...")

async def run_bot():
    await app.run_polling()

asyncio.run(run_bot())
