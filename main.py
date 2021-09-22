import ntpath
import os
import shutil
from os import getenv
from typing import List, Optional
from uuid import uuid4

import datetime

import cv2
import numpy as np
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse

import database
import authUtils

from ImageSearch import ImageSearch
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authUtils.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = datetime.timedelta(minutes=int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = authUtils.create_access_token(
        user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def __save_image(path_prefix, received_image):
    file_ext = os.path.splitext(received_image.filename)[1]
    filename = uuid4().hex + file_ext
    image_path = path_prefix + filename
    with open(image_path, "wb+") as local_image:
        shutil.copyfileobj(received_image.file, local_image)
    return filename, image_path


@app.put("/upload")
async def upload_image(visibility: str, current_user: authUtils.User = Depends(authUtils.get_user_from_token),
                       files: List[UploadFile] = File(...)):
    if visibility == "private":
        is_private = True
        path_prefix = 'private/'
    elif visibility == "public":
        is_private = False
        path_prefix = 'public/'
    else:
        raise HTTPException(status_code=400, detail="Visibility can only be 'public' or 'private'")

    relative_image_paths = []
    for received_image in files:
        filename, image_path = __save_image(path_prefix, received_image)
        database.create_image(filename, current_user.username, is_private)
        relative_image_paths.append(image_path)

    # index image if public
    if not is_private:
        image_search.batch_index_images(relative_image_paths)

    return {"filenames": [ntpath.basename(f) for f in relative_image_paths]}


@app.delete("/delete", status_code=204)
async def delete_image(image_name: str, current_user: authUtils.User = Depends(authUtils.get_user_from_token)):
    image_record = database.get_image(image_name)
    if image_record is None:
        raise HTTPException(status_code=404, detail="Image does not exist")
    elif image_record.username != current_user.username:
        raise HTTPException(status_code=401, detail="User not authorized")

    if image_record.private:
        path_prefix = 'private/'
        image_search.delete_image(path_prefix + image_name)
    else:
        path_prefix = 'public/'

    database.delete_image(image_name)
    os.remove(path_prefix + image_name)
    return


@app.get("/image")
async def retrieve_image(image_name: str,
                         current_user: Optional[authUtils.User] = Depends(authUtils.optional_get_user_from_token)):
    image_record = database.get_image(image_name)
    if image_record is None:
        raise HTTPException(status_code=404, detail="Image does not exist")
    elif image_record.private:
        if current_user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        elif image_record.username != current_user.username:
            raise HTTPException(status_code=401, detail="User not authorized")
        path_prefix = 'private/'
    else:
        path_prefix = 'public/'

    return FileResponse(path_prefix + image_name)


@app.post("/search")
async def search_image(file: UploadFile = File(...)):
    filestr = file.file.read()
    npimg = np.fromstring(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)
    results = image_search.search(img)
    return results


@app.post("/signup", status_code=204)
async def sign_up(username: str, password: str):
    if not database.create_user(username, authUtils.hash_password(password)):
        raise HTTPException(status_code=409, detail="Username already taken")
    else:
        return


def make_dirs():
    folders = ['public', 'private']
    for folder in folders:
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass


image_search = ImageSearch(kmeans_clusters=10)
make_dirs()
image_search.batch_index_images([f'public/{filename}' for filename in os.listdir("public")])
