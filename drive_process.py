import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
import process


def process_folder(credentials, folder_id):
    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials(**credentials)
    drive = GoogleDrive(gauth)

    local_input_parent = './user_uploads'
    local_results_parent = './user_results'

    # TODO incluir no nome dessas pastas id do usuario e datetime (credenciais)
    local_input_folder = local_input_parent + '/' + folder_id
    local_result_folder = local_results_parent + '/' + folder_id

    os.makedirs(local_input_folder, exist_ok=True)  # verifica se a pasta de saida realmente existe
    os.makedirs(local_result_folder, exist_ok=True)  # verifica se a pasta de saida realmente existe
    # deletar essas pastas depois de salvar de volta no drive!

    # Pegar nome da pasta de origem a partir do ID dela
    drive_input_folder = drive.CreateFile({'id': folder_id})
    drive_input_folder.FetchMetadata(fields='title')
    original_folder_name = drive_input_folder['title']

    print('folder_name = '+original_folder_name)
    print('Downloading user chosen files....')

    # Pega todos os arquivos da pasta escolhida no Drive
    file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" % folder_id}).GetList()
    for file1 in file_list:
        print('title: %s, id: %s' % (file1['title'], file1['id']))

        # Initialize GoogleDriveFile instance with file id.
        file_in = drive.CreateFile({'id': file1['id']})
        file_in.GetContentFile(local_input_folder + '/' + file1['title'])  # get content of the file to local folder

    print('Imagens baixadas, preparado para rodar..')

    # AQUI são processados todos os arquivos, uma vez que ele já foram jogados na pasta local
    process.run_batch(local_input_folder, local_result_folder)

    print('Processamento de imagens concluído!')

    # cria pasta no Drive onde serão jogados todos os arquivos de resultado
    result_folder_name = original_folder_name+'_restaurado'
    drive_result_folder_metadata = {'title': result_folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    drive_result_folder = drive.CreateFile(drive_result_folder_metadata)
    drive_result_folder.Upload()
    drive_result_folder_id = drive_result_folder['id']

    # joga todos os arquivos de resultado de volta no Drive
    for f in os.listdir(local_result_folder):
        file_path = os.path.join(local_result_folder, f)
        file1 = drive.CreateFile(
             metadata={"title": f, "parents": [{"kind": "drive#fileLink", "id": drive_result_folder_id}]})
        file1.SetContentFile(file_path)
        file1.Upload()

    print('Todas as imagens salvas no Drive !')

    return result_folder_name
