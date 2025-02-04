import hmac
import base64
from django.conf import settings
from Crypto import Random
from Crypto.Cipher import AES
from django.core.exceptions import ImproperlyConfigured
import json
import os
import pyAesCrypt
from os import remove

EN_DE_BUFFER_SIZE = 64 * 1024
KEY_FOR_JSON_VALUE = "securitydatajson"
KEY_FOR_JSON_FILE = "keyfordatajsonenc"


def get_data_from_file(setting, data_num):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if os.path.exists(os.path.join(BASE_DIR, "data" + data_num + ".json.aes")):
        try:
            open(os.path.join(BASE_DIR, "data" + data_num + "_enc.json"), "w+")
            pyAesCrypt.decryptFile(
                os.path.join(BASE_DIR, "data" + data_num + ".json.aes"),
                os.path.join(BASE_DIR, "data" + data_num + "_enc.json"),
                KEY_FOR_JSON_FILE,
                EN_DE_BUFFER_SIZE,
            )

            with open(
                os.path.join(BASE_DIR, "data" + data_num + "_enc.json")
            ) as secrets_file:
                secrets = json.load(secrets_file)
                secrets_file.close()
                remove(os.path.join(BASE_DIR, "data" + data_num + "_enc.json"))
                return dfs_decrypt_and_get_val(setting, secrets[setting], secrets)
        except KeyError:
            raise ImproperlyConfigured(
                "Error in reading setting data for : ".format(setting)
            )
    else:
        value = os.getenv(setting)
        if value is not None:
            return value
        else:
            return None


def sign(params):
    return sign_data(build_data_to_sign(params), settings.SIGNATURE_SECRET_KEY)


def sign_data(data, secret_key):
    return base64.b64encode(
        hmac.new(
            bytes(secret_key, "utf-8"),
            bytes(data, "utf-8"),
            digestmod=settings.HMAC_SHA256,
        ).digest()
    )


def build_data_to_sign(params):

    data_to_sign = []
    signed_field_names = params["signed_field_names"].split(",")

    for field in signed_field_names:
        data_to_sign.append(field + "=" + params[field])

    return comma_separate(data_to_sign)


def comma_separate(data_to_sign):
    return ",".join(data_to_sign)


BS = 16
pad = lambda s: bytes(s + (BS - len(s) % BS) * chr(BS - len(s) % BS), "utf-8")
unpad = lambda s: s[0 : -ord(s[-1:])]


class AESCipher:

    def __init__(self, key):
        self.key = bytes(key, "utf-8")

    def encrypt_val(self, raw):
        raw = pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode()

    def decrypt_val(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[16:])).decode("utf-8")


def dfs_decrypt_and_get_val(key, val, json_tree):
    dfs_decrypt(key, val, json_tree)
    return json_tree[key]


def dfs_decrypt(key, val, json_tree):
    if isinstance(val, dict):
        for k, v in val.items():
            dfs_decrypt(k, v, val)
    else:
        json_tree[key] = AESCipher(KEY_FOR_JSON_VALUE).decrypt_val(val)
