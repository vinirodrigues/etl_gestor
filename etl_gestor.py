import pdfplumber
import mysql.connector
import re
import pandas as pd
from datetime import datetime

# Conexão MySQL
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='gabinete'
)
cursor = conn.cursor()

# Criação da tabela (execute uma vez no MySQL ou aqui se preferir)
cursor.execute('''
CREATE TABLE IF NOT EXISTS atendimento (
    protocolo INT AUTO_INCREMENT PRIMARY KEY,
    atendente VARCHAR(255),
    data_solicitacao DATETIME,
    descricao TEXT,
    solicitante VARCHAR(255),
    status VARCHAR(100),
    tipo_servico VARCHAR(255)
);
''')
conn.commit()

# Extração do PDF
pdf_path = "C:/Users/Vinicius/Desktop/Gabinete_online/base.pdf"
data_list = []

with pdfplumber.open(pdf_path) as pdf:
    protocolo = 1
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        
        blocks = re.split(r'DETALHES DA SOLICITAÇÃO #[0-9]+', text)
        for block in blocks:
            if "Solicitante" in block:
                # Atendente
                atendente_match = re.search(r'por: (.*?)\s+Data da Solicitação', block, re.IGNORECASE)
                atendente = atendente_match.group(1).strip() if atendente_match else None

                # Data da Solicitação
                data_match = re.search(r'Data da Solicitação:\s*(\d{2}/\d{2}/\d{4})', block)
                data_solicitacao = datetime.strptime(data_match.group(1), "%d/%m/%Y") if data_match else None

                # Solicitante
                solicitante_match = re.search(r'Solicitante:\s*(.*)', block)
                solicitante = solicitante_match.group(1).strip() if solicitante_match else None

                # Tipo Serviço (chamado de Solicitação)
                tipo_match = re.search(r'Solicitação:\s*(.*)', block)
                tipo_servico = tipo_match.group(1).strip() if tipo_match else None

                # Descrição
                descricao_match = re.search(r'Descrição:\s*(.*?)(?:Primeiro Órgão|$)', block, re.DOTALL)
                descricao = descricao_match.group(1).strip().replace('\n', ' ') if descricao_match else None

                # Status
                status_match = re.search(r'Estado da solicitação:\s*(.*)', block)
                status = status_match.group(1).strip() if status_match else None

                # Inserção no MySQL
                cursor.execute('''
                    INSERT INTO atendimento (atendente, data_solicitacao, descricao, solicitante, status, tipo_servico)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (atendente, data_solicitacao, descricao, solicitante, status, tipo_servico))
                
                protocolo += 1

conn.commit()
cursor.close()
conn.close()

print("ETL concluído e dados salvos no MySQL.")
