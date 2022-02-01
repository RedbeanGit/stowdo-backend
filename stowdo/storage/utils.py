from django.http import FileResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from io import BytesIO
from os import path as op
from rest_framework.exceptions import PermissionDenied
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from storage.models import File, Folder



def check_parent_folder(request):
    folder_id = request.data.get('parent_folder', None)
    if isinstance(folder_id, int):
        folder_query = Folder.objects.filter(pk=folder_id, user=request.user)

        if not folder_query.exists():
            raise PermissionDenied()


def create_zip_response(user, folders_pk, files_pk):
    def create_path(folders):
        return '/'.join(folder.name for folder in folders)

    buffer = BytesIO()
    todo = [[get_object_or_404(Folder, pk=folder_pk, user=user),] for folder_pk in folders_pk]

    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as zfile:
        for file_pk in files_pk:
            file = get_object_or_404(File, pk=file_pk, user=user)

            with file.path.open() as f:
                zfile.writestr(file.name, f.read())
        while todo:
            folders = todo.pop()
            folder_path = create_path(folders)
            subfiles = File.objects.filter(user=user, parent_folder=folders[-1])
            subfolders = Folder.objects.filter(user=user, parent_folder=folders[-1])

            if subfiles.exists():
                for subfile in subfiles:
                    with subfile.path.open() as f:
                        zfile.writestr(op.join(folder_path, subfile.name), f.read())
            else:
                zif = ZipInfo(folder_path + '/')
                zfile.writestr(zif, '')

            todo.extend([folders + subfolder for subfolder in subfolders])

    filesize = buffer.tell()
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename='Files.zip')
    response['Content-Length'] = filesize
    response['Content-Disposition'] = 'attachment; filename="Files.zip"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


def create_file_response(user, file_pk):
    file = get_object_or_404(File, pk=file_pk, user=user)

    try:
        reader = file.path.open()
    except Exception:
        return HttpResponseServerError('An error occurred when reading file')
    else:
        response = FileResponse(reader)
        response['Content-Length'] = file.path.size
        response['Content-Disposition'] = f'attachment; filename="{file.name}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'

        return response