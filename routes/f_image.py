import os
from globals import Db, api, config  # GLOBAL_IMPORT
from routes.helpers import (
    auth_required,
)
from flask import Blueprint, Response, request, send_from_directory
from io import BytesIO
from typing import Callable, Tuple
from PIL import Image, ImageSequence

app = Blueprint("image", __name__, template_folder="templates", static_folder="static")


def resize_image(size: Tuple[int, int]) -> Callable[[Image.Image], Image.Image]:
    return lambda img: img.convert("RGBA").resize(size, Image.Resampling.BICUBIC)


def convert_to_apng(input: Image.Image, size: Tuple[int, int] = (256, 256)):
    iobuf = BytesIO()
    frames = ImageSequence.all_frames(input, resize_image(size))
    frames[0].save(
        iobuf,
        "PNG",
        save_all=True,
        append_images=frames[1:],
    )
    return Image.open(iobuf)


def save_apng(img: Image.Image, filename: str):
    img.save(filename, "PNG", save_all=True, optimize=True, lossless=False)


@app.route("/image/<login>/set", methods=["POST"])
@auth_required
def set_image(login, userid):
    print(userid)
    if config.image_store is None:
        return Response("not image store configured", status=503)
    with Db() as db:
        id = db.get_user_profile(login, api)
        if id is None:
            return Response("user not found", status=404)
        if not userid["admin"] and id["id"] != userid["userid"]:
            return Response("not allowed to edit image", status=403)
        body = BytesIO(request.get_data())
        try:
            save_apng(
                convert_to_apng(Image.open(body)),
                f"{config.image_store}/{id['id']}.png",
            )
            db.set_custom_image(id["id"], userid["userid"])
        except OSError as ex:
            print(f"fialed to open the image: {ex}")
            return Response(f"failed to open the image: {ex}", status=500)
    return Response("Image has been saved", status=200)


@app.route("/image/<login>")
@auth_required
def get_image(login: str, userid) -> Response:
    if config.image_store is None:
        return Response("not found", status=404)
    login = login.removesuffix(".png")
    with Db() as db:
        u = db.get_user_by_login(login)
        custom_img = db.get_custom_image(u["id"])
        if custom_img is not None:
            return send_from_directory(config.image_store, f"{u['id']}.png")
    return Response("not found", status=404)


@app.route("/image/<login>/remove", methods=["DELETE"])
@auth_required
def rm_image(login: str, userid) -> Response:
    if config.image_store is None:
        return Response(status=404)
    with Db() as db:
        id = db.get_user_profile(login, api)
        if id is None:
            return Response("user not found", status=404)
        if not userid["admin"] and id != userid["userid"]:
            return Response("not allowed to edit image", status=403)
        try:
            os.remove(f"{config.image_store}/{userid['userid']}.png")
        except:
            pass
        db.remove_custom_image(userid["userid"])
    return Response("not found", status=404)
