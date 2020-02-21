import io
import cv2
import numpy as np
import threading
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# import process

SCOPES = ['https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'


class ProcessThread (threading.Thread):
    ids_count = 0
    threads = []

    def __init__(self, credentials, folder_id, status):
        threading.Thread.__init__(self)
        self.threadID = ProcessThread.ids_count
        self.running = False
        self.status = status
        self.status['my_thread_id'] = self.threadID
        self.credentials = credentials
        self.folder_id = folder_id
        ProcessThread.ids_count += 1
        ProcessThread.threads.append(self)

    def run(self):
        print("Starting thread number %d" % self.threadID)
        self.running = True
        self.status['running'] = True
        process_folder(self.credentials, self.folder_id, self.status)
        self.running = False
        self.status['running'] = False
        print("Exiting  thread number %d" % self.threadID)


def process_folder(credentials, folder_id, status):

    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Get Folder name from ID
    request_folder_name = drive.files().get(fileId=folder_id).execute()
    original_folder_name = request_folder_name['name']

    print('folder_name = '+original_folder_name)
    print('Downloading user chosen files....')

    if status['cancel_signal']:
        return False

    arr_files = []

    # Pega todos os arquivos da pasta escolhida no Drive
    file_list_return = drive.files().list(q="'%s' in parents and trashed=false" % folder_id).execute()
    file_list = file_list_return['files']

    print('lista de arquivos:')
    print(file_list)

    if status['cancel_signal']:
        return False

    status['files_list'] = file_list
    status['folder_name'] = original_folder_name

    for file in file_list:
        print('baixando arquivo:')
        print('title: %s, id: %s' % (file['name'], file['id']))

        request = drive.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            dwnl_status, done = downloader.next_chunk()
            print("Download %d %%." % int(dwnl_status.progress() * 100))

        if status['cancel_signal']:
            return False

        nparr = np.fromstring(fh.getvalue(), np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        # img = np.flip(img_np, 2)

        file_name = file['name'].split('.')[0]
        arr_files.append([file_name, img])

    print('Imagens baixadas, preparado para rodar..')

    if status['cancel_signal']:
        return False

    # -----------------------

    # AQUI são processados todos os arquivos, uma vez que ele já foram jogados na pasta local

    # result_arr = process.run_array(arr_files, status)
    result_arr = arr_files

    # -----------------------

    if status['cancel_signal']:
        return False

    print('Processamento de imagens concluído!')

    print('Jogando de volta pro drive...!')

    result_folder_name = original_folder_name+'_restaurado'
    result_folder_metadata = {
        'name': result_folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    result_folder = drive.files().create(body=result_folder_metadata,
                                         fields='id').execute()
    result_folder_id = result_folder.get('id')

    print('Criada pasta no drive: Folder ID: %s' % result_folder_id)

    if status['cancel_signal']:
        return False

    # joga todos os arquivos de resultado de volta no Drive
    for [name, image] in result_arr:
        file_metadata = {
            'name': name+'.png',
            'parents': [result_folder_id]
        }
        # img_np = np.flip(image, 2)
        img_np = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        is_success, img_enc = cv2.imencode(".png", img_np, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        fh = io.BytesIO(img_enc)
        media = MediaIoBaseUpload(fh, mimetype='image/png', resumable=True)
        file = drive.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
        print('File name: %s ; ID: %s' % (name, file.get('id')))

    print('Todas as imagens salvas no Drive !')

    status['running'] = False

    return result_folder_name
