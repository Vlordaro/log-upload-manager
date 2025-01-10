from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import socket
from dotenv import load_dotenv

load_dotenv()

NOME_DA_MAQUINA = socket.gethostname()

PASTAS = {
   'kernel': {
       'nome': 'Kernel Log',
       'id': os.getenv('KERNEL_FOLDER_ID'),
       'pasta_base': os.getenv('KERNEL_PATH'),
       'nome_arquivo': f'kernel_log_{NOME_DA_MAQUINA}.txt'
   },
   'audio': {
       'nome': 'Audio Log', 
       'id': os.getenv('AUDIO_FOLDER_ID'),
       'pasta_base': os.getenv('AUDIO_PATH'),
       'nome_arquivo': f'audio_log_{NOME_DA_MAQUINA}.txt'
   },
   'device': {
       'nome': 'Device Log',
       'id': os.getenv('DEVICE_FOLDER_ID'),
       'pasta_base': os.getenv('DEVICE_PATH'),
       'nome_arquivo': f'device_log_{NOME_DA_MAQUINA}.txt'
   }
}

def criar_pastas():
   for pasta_info in PASTAS.values():
       pasta_base = pasta_info['pasta_base']
       if not os.path.exists(pasta_base):
           os.makedirs(pasta_base)

def criar_service():
   SCOPES = ['https://www.googleapis.com/auth/drive.file']
   credentials = service_account.Credentials.from_service_account_file(
       os.getenv('GOOGLE_CREDS_PATH'),
       scopes=SCOPES
   )
   return build('drive', 'v3', credentials=credentials)

def encontrar_arquivo_existente(service, nome_arquivo, pasta_id):
   query = f"name = '{nome_arquivo}' and '{pasta_id}' in parents and trashed = false"
   resultados = service.files().list(
       q=query,
       spaces='drive',
       fields='files(id)'
   ).execute()
   arquivos = resultados.get('files', [])
   return arquivos[0]['id'] if arquivos else None

def upload_ou_atualiza_arquivo(service, caminho_arquivo, nome_arquivo, pasta_id):
   arquivo_existente_id = encontrar_arquivo_existente(service, nome_arquivo, pasta_id)
   media = MediaFileUpload(caminho_arquivo, resumable=True)
   
   if arquivo_existente_id:
       service.files().update(
           fileId=arquivo_existente_id,
           media_body=media
       ).execute()
   else:
       file_metadata = {
           'name': nome_arquivo,
           'parents': [pasta_id]
       }
       service.files().create(
           body=file_metadata,
           media_body=media,
           fields='id'
       ).execute()

def upload_arquivos_da_pasta(tipo_alerta):
   try:
       if tipo_alerta not in PASTAS:
           return
           
       service = criar_service()
       pasta_info = PASTAS[tipo_alerta]
       
       caminho_arquivo = os.path.join(pasta_info['pasta_base'], pasta_info['nome_arquivo'])
       
       if not os.path.isfile(caminho_arquivo):
           return
           
       upload_ou_atualiza_arquivo(
           service,
           caminho_arquivo,
           pasta_info['nome_arquivo'],
           pasta_info['id']
       )
           
   except Exception:
       pass

def verificar_todas_pastas():
   for tipo_alerta in PASTAS:
       upload_arquivos_da_pasta(tipo_alerta)

if __name__ == '__main__':
   criar_pastas()
   verificar_todas_pastas()
